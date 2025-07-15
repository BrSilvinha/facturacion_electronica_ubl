# conversion/generators/__init__.py - VERSIÓN COMPLETA CON LIMPIEZA

"""
Generadores UBL 2.1 para documentos electrónicos SUNAT
VERSIÓN COMPLETA - Incluye limpieza de artefactos de desarrollo
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
from django.template.loader import get_template
from django.template import Context, Template
from documentos.models import DocumentoElectronico

logger = logging.getLogger(__name__)

# Factory para crear generadores
class UBLGeneratorFactory:
    """Factory para crear generadores UBL según tipo de documento"""
    
    _generators = {}
    _supported_types = ['01', '03', '07', '08', '09']
    
    @classmethod
    def get_generator(cls, document_type: str):
        """Obtiene el generador apropiado para el tipo de documento"""
        
        if document_type not in cls._generators:
            if document_type in ['01']:  # Factura
                cls._generators[document_type] = FacturaGenerator()
            elif document_type in ['03']:  # Boleta
                cls._generators[document_type] = BoletaGenerator()
            elif document_type in ['07']:  # Nota de Crédito
                cls._generators[document_type] = NotaCreditoGenerator()
            elif document_type in ['08']:  # Nota de Débito
                cls._generators[document_type] = NotaDebitoGenerator()
            else:
                raise ValueError(f"Tipo de documento no soportado: {document_type}")
        
        return cls._generators[document_type]
    
    @classmethod
    def get_supported_document_types(cls) -> List[str]:
        """Retorna lista de tipos de documento soportados"""
        return cls._supported_types.copy()
    
    @classmethod
    def is_supported(cls, document_type: str) -> bool:
        """Verifica si un tipo de documento está soportado"""
        return document_type in cls._supported_types


class BaseUBLGenerator:
    """Generador base para documentos UBL 2.1"""
    
    def __init__(self):
        self.template_name = None
        self.document_type = None
        self.ubl_version = "2.1"
        self.customization_id = "2.0"
    
    def generate_xml(self, documento: DocumentoElectronico) -> str:
        """
        Genera XML UBL 2.1 para el documento
        
        Args:
            documento: DocumentoElectronico instance
            
        Returns:
            XML UBL 2.1 como string
        """
        
        try:
            logger.info(f"Generando {self.document_type} UBL 2.1: {documento.get_numero_completo()}")
            
            # Preparar contexto
            context = self._prepare_context(documento)
            
            # Renderizar template
            xml_content = self._render_template(context)
            
            # Limpiar artefactos de desarrollo
            clean_xml = self._clean_development_artifacts(xml_content)
            
            # Validar XML generado
            self._validate_generated_xml(clean_xml, documento)
            
            logger.info(f"XML UBL 2.1 generado exitosamente: {len(clean_xml)} caracteres")
            
            return clean_xml
            
        except Exception as e:
            logger.error(f"Error generando XML UBL 2.1 para {documento.get_numero_completo()}: {e}")
            raise
    
    def _prepare_context(self, documento: DocumentoElectronico) -> Dict[str, Any]:
        """Prepara el contexto para el template"""
        
        # Información básica
        context = {
            'ubl_version': self.ubl_version,
            'customization_id': self.customization_id,
            'document_id': documento.get_numero_completo(),
            'document_type_code': documento.tipo_documento.codigo,
            'issue_date': documento.fecha_emision,
            'generation_time': datetime.now(),
            'currency_code': documento.moneda,
        }
        
        # Empresa emisora
        context['supplier'] = self._prepare_supplier_data(documento.empresa)
        
        # Cliente receptor
        context['customer'] = self._prepare_customer_data(documento)
        
        # Líneas del documento
        context['lines'] = self._prepare_lines_data(documento)
        
        # Totales
        context['totales'] = self._prepare_totals_data(documento)
        
        # Datos tributarios
        context['tax_data'] = self._prepare_tax_data(documento)
        
        # Condiciones de pago (solo facturas)
        if documento.tipo_documento.codigo == '01':
            context['payment_terms'] = self._prepare_payment_terms(documento)
        
        return context
    
    def _prepare_supplier_data(self, empresa) -> Dict[str, Any]:
        """Prepara datos del emisor (empresa)"""
        
        return {
            'ruc': empresa.ruc,
            'legal_name': empresa.razon_social,
            'trade_name': empresa.nombre_comercial or empresa.razon_social,
            'address': empresa.direccion,
            'ubigeo': empresa.ubigeo or '150101'
        }
    
    def _prepare_customer_data(self, documento: DocumentoElectronico) -> Dict[str, Any]:
        """Prepara datos del receptor (cliente)"""
        
        return {
            'document_type': documento.receptor_tipo_doc,
            'document_number': documento.receptor_numero_doc,
            'legal_name': documento.receptor_razon_social,
            'address': documento.receptor_direccion
        }
    
    def _prepare_lines_data(self, documento: DocumentoElectronico) -> List[Dict[str, Any]]:
        """Prepara datos de las líneas del documento"""
        
        lines = []
        
        for linea in documento.lineas.all().order_by('numero_linea'):
            # Calcular precio unitario con IGV incluido
            precio_unitario_con_igv = linea.valor_unitario + (linea.igv_linea / linea.cantidad if linea.cantidad > 0 else Decimal('0'))
            
            line_data = {
                'id': linea.numero_linea,
                'product_code': linea.codigo_producto or '',
                'description': linea.descripcion,
                'quantity': linea.cantidad,
                'unit_code': linea.unidad_medida,
                'price_amount': linea.valor_unitario,
                'base_quantity': Decimal('1.000'),
                'line_extension_amount': linea.valor_venta,
                'tax_data': self._prepare_line_tax_data(linea)
            }
            
            lines.append(line_data)
        
        return lines
    
    def _prepare_line_tax_data(self, linea) -> List[Dict[str, Any]]:
        """Prepara datos tributarios de una línea"""
        
        tax_data = []
        
        # IGV
        if linea.afectacion_igv in ['10', '11', '12', '13', '14', '15', '16', '17']:
            # Gravado
            tax_data.append({
                'tax_id': '1000',
                'tax_name': 'IGV',
                'tax_type_code': 'VAT',
                'tax_category_id': 'S',
                'tax_amount': linea.igv_linea,
                'taxable_amount': linea.valor_venta,
                'tax_percentage': Decimal('18.00'),
                'exemption_reason_code': linea.afectacion_igv
            })
        elif linea.afectacion_igv in ['20', '21']:
            # Exonerado
            tax_data.append({
                'tax_id': '9997',
                'tax_name': 'EXO',
                'tax_type_code': 'VAT',
                'tax_category_id': 'E',
                'tax_amount': Decimal('0.00'),
                'taxable_amount': linea.valor_venta,
                'tax_percentage': None,
                'exemption_reason_code': linea.afectacion_igv
            })
        elif linea.afectacion_igv in ['30', '31', '32', '33', '34', '35', '36']:
            # Inafecto
            tax_data.append({
                'tax_id': '9998',
                'tax_name': 'INA',
                'tax_type_code': 'FRE',
                'tax_category_id': 'O',
                'tax_amount': Decimal('0.00'),
                'taxable_amount': linea.valor_venta,
                'tax_percentage': None,
                'exemption_reason_code': linea.afectacion_igv
            })
        elif linea.afectacion_igv == '40':
            # Exportación
            tax_data.append({
                'tax_id': '9995',
                'tax_name': 'EXP',
                'tax_type_code': 'FRE',
                'tax_category_id': 'G',
                'tax_amount': Decimal('0.00'),
                'taxable_amount': linea.valor_venta,
                'tax_percentage': None,
                'exemption_reason_code': linea.afectacion_igv
            })
        
        # ISC (si aplica)
        if linea.isc_linea > 0:
            tax_data.append({
                'tax_id': '2000',
                'tax_name': 'ISC',
                'tax_type_code': 'EXC',
                'tax_category_id': 'S',
                'tax_amount': linea.isc_linea,
                'taxable_amount': linea.valor_venta,
                'tax_percentage': None
            })
        
        # ICBPER (si aplica)
        if linea.icbper_linea > 0:
            tax_data.append({
                'tax_id': '7152',
                'tax_name': 'ICBPER',
                'tax_type_code': 'OTH',
                'tax_category_id': 'S',
                'tax_amount': linea.icbper_linea,
                'taxable_amount': None,
                'tax_percentage': None
            })
        
        return tax_data
    
    def _prepare_totals_data(self, documento: DocumentoElectronico) -> Dict[str, Any]:
        """Prepara datos de totales del documento"""
        
        # Calcular subtotales por afectación
        lineas = documento.lineas.all()
        
        subtotal_gravado = sum(
            linea.valor_venta for linea in lineas
            if linea.afectacion_igv in ['10', '11', '12', '13', '14', '15', '16', '17']
        )
        
        subtotal_exonerado = sum(
            linea.valor_venta for linea in lineas
            if linea.afectacion_igv in ['20', '21']
        )
        
        subtotal_inafecto = sum(
            linea.valor_venta for linea in lineas
            if linea.afectacion_igv in ['30', '31', '32', '33', '34', '35', '36']
        )
        
        subtotal_exportacion = sum(
            linea.valor_venta for linea in lineas
            if linea.afectacion_igv == '40'
        )
        
        return {
            'subtotal_gravado': subtotal_gravado,
            'subtotal_exonerado': subtotal_exonerado,
            'subtotal_inafecto': subtotal_inafecto,
            'subtotal_exportacion': subtotal_exportacion,
            'total_valor_venta': documento.subtotal,
            'total_igv': documento.igv,
            'total_isc': documento.isc,
            'total_icbper': documento.icbper,
            'total_precio_venta': documento.total,
            'total_descuentos': Decimal('0.00'),
            'total_otros_cargos': Decimal('0.00')
        }
    
    def _prepare_tax_data(self, documento: DocumentoElectronico) -> List[Dict[str, Any]]:
        """Prepara resumen de impuestos del documento"""
        
        tax_data = []
        
        # IGV total
        if documento.igv > 0:
            # Calcular base gravada
            lineas_gravadas = documento.lineas.filter(
                afectacion_igv__in=['10', '11', '12', '13', '14', '15', '16', '17']
            )
            base_gravada = sum(linea.valor_venta for linea in lineas_gravadas)
            
            tax_data.append({
                'tax_id': '1000',
                'tax_name': 'IGV',
                'tax_type_code': 'VAT',
                'tax_amount': documento.igv,
                'taxable_amount': base_gravada,
                'tax_percentage': Decimal('18.00')
            })
        
        # ISC total
        if documento.isc > 0:
            tax_data.append({
                'tax_id': '2000',
                'tax_name': 'ISC',
                'tax_type_code': 'EXC',
                'tax_amount': documento.isc,
                'taxable_amount': None,
                'tax_percentage': None
            })
        
        # ICBPER total
        if documento.icbper > 0:
            tax_data.append({
                'tax_id': '7152',
                'tax_name': 'ICBPER',
                'tax_type_code': 'OTH',
                'tax_amount': documento.icbper,
                'taxable_amount': None,
                'tax_percentage': None
            })
        
        return tax_data
    
    def _prepare_payment_terms(self, documento: DocumentoElectronico) -> Dict[str, Any]:
        """Prepara condiciones de pago (solo para facturas)"""
        
        if documento.fecha_vencimiento:
            return {
                'payment_due_date': documento.fecha_vencimiento,
                'payment_means_code': 'Contado' if documento.fecha_vencimiento == documento.fecha_emision else 'Credito',
                'payment_amount': documento.total
            }
        
        return {
            'payment_means_code': 'Contado',
            'payment_amount': documento.total
        }
    
    def _render_template(self, context: Dict[str, Any]) -> str:
        """Renderiza el template UBL con el contexto"""
        
        if not self.template_name:
            raise ValueError("Template name no definido en el generador")
        
        try:
            template = get_template(self.template_name)
            
            # Agregar filtros personalizados al contexto
            context.update({
                'format_decimal': self._format_decimal,
                'format_date': self._format_date,
                'cdata': self._cdata_wrap
            })
            
            xml_content = template.render(context)
            
            return xml_content
            
        except Exception as e:
            logger.error(f"Error renderizando template {self.template_name}: {e}")
            raise
    
    def _clean_development_artifacts(self, xml_content: str) -> str:
        """
        🧹 LIMPIA ARTEFACTOS DE DESARROLLO DEL XML
        Elimina comentarios, espacios extra y normaliza formato
        """
        
        import re
        
        # 1. Eliminar comentarios de desarrollo
        comment_patterns = [
            r'<!--.*?FIRMA DIGITAL.*?-->',
            r'<!--.*?Aquí va la firma digital.*?-->',
            r'<!--.*?Signature placeholder.*?-->',
            r'<!--.*?TODO.*?-->',
            r'<!--.*?DEBUG.*?-->',
            r'<!--.*?DEVELOPMENT.*?-->',
            r'<!--.*?Template.*?-->',
            r'<!--.*?Generated.*?-->',
        ]
        
        cleaned_xml = xml_content
        for pattern in comment_patterns:
            cleaned_xml = re.sub(pattern, '', cleaned_xml, flags=re.DOTALL | re.IGNORECASE)
        
        # 2. Limpiar espacios múltiples y líneas vacías
        cleaned_xml = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_xml)
        cleaned_xml = re.sub(r'[ \t]+\n', '\n', cleaned_xml)
        
        # 3. Normalizar indentación
        lines = cleaned_xml.split('\n')
        normalized_lines = []
        
        for line in lines:
            if line.strip():  # Solo procesar líneas con contenido
                normalized_lines.append(line.rstrip())  # Eliminar espacios al final
            elif normalized_lines and normalized_lines[-1].strip():  # Mantener separación
                normalized_lines.append('')
        
        # 4. Asegurar declaración XML correcta
        final_xml = '\n'.join(normalized_lines)
        
        # Corregir declaración XML si es necesario
        if not final_xml.startswith('<?xml'):
            final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + final_xml
        elif "version='1.0'" in final_xml:
            final_xml = final_xml.replace("version='1.0'", 'version="1.0"')
        elif "encoding='UTF-8'" in final_xml:
            final_xml = final_xml.replace("encoding='UTF-8'", 'encoding="UTF-8"')
        
        logger.info(f"XML limpiado: {len(xml_content)} → {len(final_xml)} caracteres")
        
        return final_xml
    
    def _validate_generated_xml(self, xml_content: str, documento: DocumentoElectronico):
        """Valida el XML generado"""
        
        # Validaciones básicas
        if not xml_content.strip():
            raise ValueError("XML generado está vacío")
        
        if not xml_content.startswith('<?xml'):
            raise ValueError("XML no tiene declaración XML válida")
        
        # Verificar elementos obligatorios
        required_elements = [
            f'<cbc:ID>{documento.get_numero_completo()}</cbc:ID>',
            f'<cbc:ID>{documento.empresa.ruc}</cbc:ID>',
            '<cbc:InvoiceTypeCode' if documento.tipo_documento.codigo in ['01', '03'] else '<cbc:CreditNoteTypeCode',
        ]
        
        for element in required_elements:
            if element not in xml_content:
                logger.warning(f"Elemento requerido posiblemente faltante: {element}")
        
        # Verificar estructura UBL
        ubl_elements = ['<cbc:UBLVersionID>', '<cbc:CustomizationID>', '<cac:AccountingSupplierParty>']
        for element in ubl_elements:
            if element not in xml_content:
                raise ValueError(f"Elemento UBL requerido faltante: {element}")
        
        logger.info("XML validado exitosamente")
    
    def _format_decimal(self, value: Decimal, places: int = 2) -> str:
        """Formatea decimal para XML"""
        if value is None:
            return "0.00"
        return f"{value:.{places}f}"
    
    def _format_date(self, date_obj) -> str:
        """Formatea fecha para XML (YYYY-MM-DD)"""
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime('%Y-%m-%d')
        return str(date_obj)
    
    def _cdata_wrap(self, text: str) -> str:
        """Envuelve texto en CDATA si contiene caracteres especiales"""
        if any(char in text for char in ['<', '>', '&', '"', "'"]):
            return f"<![CDATA[{text}]]>"
        return text


class FacturaGenerator(BaseUBLGenerator):
    """Generador específico para facturas (01)"""
    
    def __init__(self):
        super().__init__()
        self.template_name = 'ubl/factura.xml'
        self.document_type = 'Factura'


class BoletaGenerator(BaseUBLGenerator):
    """Generador específico para boletas (03)"""
    
    def __init__(self):
        super().__init__()
        self.template_name = 'ubl/boleta.xml'
        self.document_type = 'Boleta'


class NotaCreditoGenerator(BaseUBLGenerator):
    """Generador específico para notas de crédito (07)"""
    
    def __init__(self):
        super().__init__()
        self.template_name = 'ubl/nota_credito.xml'
        self.document_type = 'Nota de Crédito'


class NotaDebitoGenerator(BaseUBLGenerator):
    """Generador específico para notas de débito (08)"""
    
    def __init__(self):
        super().__init__()
        self.template_name = 'ubl/nota_debito.xml'
        self.document_type = 'Nota de Débito'


# Función principal para generar XML
def generate_ubl_xml(documento: DocumentoElectronico) -> str:
    """
    Genera XML UBL 2.1 para cualquier tipo de documento
    VERSIÓN LIMPIA - Sin artefactos de desarrollo
    
    Args:
        documento: DocumentoElectronico instance
        
    Returns:
        XML UBL 2.1 limpio como string
    """
    
    try:
        # Obtener generador apropiado
        generator = UBLGeneratorFactory.get_generator(documento.tipo_documento.codigo)
        
        # Generar XML limpio
        xml_content = generator.generate_xml(documento)
        
        logger.info(f"XML UBL 2.1 generado y limpiado para {documento.get_numero_completo()}")
        
        return xml_content
        
    except Exception as e:
        logger.error(f"Error generando XML UBL 2.1: {e}")
        raise


# Función para limpiar XML existente
def clean_existing_xml(xml_content: str) -> str:
    """
    Limpia XML existente eliminando artefactos de desarrollo
    
    Args:
        xml_content: XML a limpiar
        
    Returns:
        XML limpio
    """
    
    generator = BaseUBLGenerator()
    return generator._clean_development_artifacts(xml_content)