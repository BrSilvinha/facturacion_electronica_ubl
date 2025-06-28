from abc import ABC, abstractmethod
from jinja2 import Environment, FileSystemLoader
from django.conf import settings
from decimal import Decimal
from datetime import datetime
import os
import uuid

class BaseUBLGenerator(ABC):
    """Generador base para documentos UBL 2.1"""
    
    def __init__(self):
        # Configurar Jinja2
        template_dir = os.path.join(settings.BASE_DIR, 'conversion', 'templates', 'ubl')
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Registrar filtros personalizados
        self.env.filters['format_decimal'] = self._format_decimal
        self.env.filters['format_date'] = self._format_date
        self.env.filters['cdata'] = self._cdata
    
    @abstractmethod
    def get_template_name(self):
        """Retorna el nombre del template a usar"""
        pass
    
    @abstractmethod
    def get_document_type_code(self):
        """Retorna el código de tipo de documento"""
        pass
    
    def generate_xml(self, documento):
        """Genera XML UBL 2.1 para el documento"""
        
        # Preparar contexto de datos
        context = self._prepare_context(documento)
        
        # Cargar template
        template = self.env.get_template(self.get_template_name())
        
        # Generar XML
        xml_content = template.render(context)
        
        return xml_content
    
    def _prepare_context(self, documento):
        """Prepara el contexto de datos para el template"""
        
        # Calcular totales detallados
        totals = self._calculate_detailed_totals(documento)
        
        # Preparar datos de impuestos
        tax_data = self._prepare_tax_data(documento, totals)
        
        # Context completo
        context = {
            # Metadatos del documento
            'ubl_version': '2.1',
            'customization_id': '2.0',
            'document_id': f"{documento.serie}-{documento.numero:08d}",
            'issue_date': documento.fecha_emision,
            'document_type_code': self.get_document_type_code(),
            'currency_code': documento.moneda,
            
            # Empresa emisora
            'supplier': {
                'ruc': documento.empresa.ruc,
                'document_type': '6',  # RUC
                'legal_name': documento.empresa.razon_social,
                'trade_name': documento.empresa.nombre_comercial or documento.empresa.razon_social,
                'address': documento.empresa.direccion,
                'ubigeo': documento.empresa.ubigeo or '150101'  # Lima por defecto
            },
            
            # Cliente receptor
            'customer': {
                'document_type': documento.receptor_tipo_doc,
                'document_number': documento.receptor_numero_doc,
                'legal_name': documento.receptor_razon_social,
                'address': documento.receptor_direccion or ''
            },
            
            # Líneas del documento
            'lines': self._prepare_lines(documento),
            
            # Totales e impuestos
            'totals': totals,
            'tax_data': tax_data,
            
            # Metadatos adicionales
            'uuid': str(uuid.uuid4()),
            'generation_time': datetime.now(),
        }
        
        return context
    
    def _calculate_detailed_totals(self, documento):
        """Calcula totales detallados del documento"""
        
        subtotal_gravado = Decimal('0.00')
        subtotal_exonerado = Decimal('0.00')
        subtotal_inafecto = Decimal('0.00')
        subtotal_exportacion = Decimal('0.00')
        
        igv_total = Decimal('0.00')
        isc_total = Decimal('0.00')
        icbper_total = Decimal('0.00')
        
        for linea in documento.lineas.all():
            if linea.afectacion_igv == '10':  # Gravado
                subtotal_gravado += linea.valor_venta
                igv_total += linea.igv_linea
            elif linea.afectacion_igv == '20':  # Exonerado
                subtotal_exonerado += linea.valor_venta
            elif linea.afectacion_igv == '30':  # Inafecto
                subtotal_inafecto += linea.valor_venta
            elif linea.afectacion_igv == '40':  # Exportación
                subtotal_exportacion += linea.valor_venta
            
            isc_total += linea.isc_linea
            icbper_total += linea.icbper_linea
        
        total_valor_venta = subtotal_gravado + subtotal_exonerado + subtotal_inafecto + subtotal_exportacion
        total_precio_venta = total_valor_venta + igv_total + isc_total + icbper_total
        
        return {
            'subtotal_gravado': subtotal_gravado,
            'subtotal_exonerado': subtotal_exonerado,
            'subtotal_inafecto': subtotal_inafecto,
            'subtotal_exportacion': subtotal_exportacion,
            'total_valor_venta': total_valor_venta,
            'igv_total': igv_total,
            'isc_total': isc_total,
            'icbper_total': icbper_total,
            'total_precio_venta': total_precio_venta,
            'total_descuentos': Decimal('0.00'),  # Para futuras mejoras
            'total_otros_cargos': Decimal('0.00')  # Para futuras mejoras
        }
    
    def _prepare_tax_data(self, documento, totals):
        """Prepara datos de impuestos para el XML"""
        
        tax_data = []
        
        # IGV
        if totals['igv_total'] > 0:
            tax_data.append({
                'tax_id': '1000',
                'tax_name': 'IGV',
                'tax_type_code': 'VAT',
                'tax_amount': totals['igv_total'],
                'taxable_amount': totals['subtotal_gravado'],
                'tax_percentage': Decimal('18.00')
            })
        
        # ISC
        if totals['isc_total'] > 0:
            tax_data.append({
                'tax_id': '2000',
                'tax_name': 'ISC',
                'tax_type_code': 'EXC',
                'tax_amount': totals['isc_total'],
                'taxable_amount': totals['total_valor_venta'],  # Base para ISC
                'tax_percentage': None  # ISC puede ser monto fijo
            })
        
        # ICBPER
        if totals['icbper_total'] > 0:
            tax_data.append({
                'tax_id': '7152',
                'tax_name': 'ICBPER',
                'tax_type_code': 'OTH',
                'tax_amount': totals['icbper_total'],
                'taxable_amount': None,  # ICBPER es por unidad
                'tax_percentage': None
            })
        
        return tax_data
    
    def _prepare_lines(self, documento):
        """Prepara las líneas del documento para el template"""
        
        lines = []
        
        for linea in documento.lineas.all():
            line_data = {
                'id': linea.numero_linea,
                'quantity': linea.cantidad,
                'unit_code': linea.unidad_medida,
                'description': linea.descripcion,
                'product_code': linea.codigo_producto or '',
                'unit_price': linea.valor_unitario,
                'line_extension_amount': linea.valor_venta,
                
                # Impuestos de línea
                'tax_data': self._prepare_line_tax_data(linea),
                
                # Precio con impuestos incluidos
                'price_amount': linea.valor_unitario,
                'base_quantity': linea.cantidad
            }
            
            lines.append(line_data)
        
        return lines
    
    def _prepare_line_tax_data(self, linea):
        """Prepara datos de impuestos para una línea específica"""
        
        line_taxes = []
        
        # IGV de línea
        if linea.igv_linea > 0 or linea.afectacion_igv in ['10', '20', '30', '40']:
            tax_category_id = 'S' if linea.afectacion_igv == '10' else 'E'
            
            line_taxes.append({
                'tax_id': '1000',
                'tax_name': 'IGV',
                'tax_type_code': 'VAT',
                'tax_category_id': tax_category_id,
                'tax_percentage': Decimal('18.00') if linea.afectacion_igv == '10' else Decimal('0.00'),
                'tax_amount': linea.igv_linea,
                'taxable_amount': linea.valor_venta,
                'exemption_reason_code': linea.afectacion_igv
            })
        
        # ISC de línea
        if linea.isc_linea > 0:
            line_taxes.append({
                'tax_id': '2000',
                'tax_name': 'ISC',
                'tax_type_code': 'EXC',
                'tax_category_id': 'S',
                'tax_percentage': None,
                'tax_amount': linea.isc_linea,
                'taxable_amount': linea.valor_venta,
                'exemption_reason_code': None
            })
        
        # ICBPER de línea
        if linea.icbper_linea > 0:
            line_taxes.append({
                'tax_id': '7152',
                'tax_name': 'ICBPER',
                'tax_type_code': 'OTH',
                'tax_category_id': 'S',
                'tax_percentage': None,
                'tax_amount': linea.icbper_linea,
                'taxable_amount': None,
                'exemption_reason_code': None
            })
        
        return line_taxes
    
    # Filtros para Jinja2
    def _format_decimal(self, value, decimals=2):
        """Formatea decimal para XML"""
        if value is None:
            return "0.00"
        return f"{float(value):.{decimals}f}"
    
    def _format_date(self, value):
        """Formatea fecha para XML (YYYY-MM-DD)"""
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)
    
    def _cdata(self, value):
        """Envuelve texto en CDATA"""
        if value is None:
            return ""
        return f"<![CDATA[{value}]]>"