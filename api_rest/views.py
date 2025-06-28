from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
import uuid

from documentos.models import (
    Empresa, TipoDocumento, DocumentoElectronico, 
    DocumentoLinea, CertificadoDigital, LogOperacion
)

class TestAPIView(APIView):
    """Endpoint de prueba para verificar que la API funciona"""
    
    def get(self, request):
        return Response({
            'message': 'API de Facturación Electrónica UBL 2.1 funcionando correctamente',
            'version': '1.0',
            'timestamp': timezone.now(),
            'endpoints': [
                '/api/test/',
                '/api/generar-xml/',
                '/api/tipos-documento/',
                '/api/empresas/',
                '/api/validar-ruc/',
            ]
        })

class TiposDocumentoView(APIView):
    """Lista todos los tipos de documento disponibles"""
    
    def get(self, request):
        tipos = TipoDocumento.objects.filter(activo=True).order_by('codigo')
        data = [
            {
                'codigo': tipo.codigo,
                'descripcion': tipo.descripcion
            }
            for tipo in tipos
        ]
        return Response({
            'success': True,
            'data': data
        })

class EmpresasView(APIView):
    """Lista todas las empresas activas"""
    
    def get(self, request):
        empresas = Empresa.objects.filter(activo=True).order_by('razon_social')
        data = [
            {
                'id': str(empresa.id),
                'ruc': empresa.ruc,
                'razon_social': empresa.razon_social,
                'nombre_comercial': empresa.nombre_comercial
            }
            for empresa in empresas
        ]
        return Response({
            'success': True,
            'data': data
        })

class ValidarRUCView(APIView):
    """Valida un RUC peruano"""
    
    def post(self, request):
        ruc = request.data.get('ruc', '').strip()
        
        if not ruc:
            return Response({
                'success': False,
                'error': 'RUC es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validación básica de RUC peruano
        if len(ruc) != 11 or not ruc.isdigit():
            return Response({
                'success': False,
                'error': 'RUC debe tener exactamente 11 dígitos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si existe en la base de datos
        try:
            empresa = Empresa.objects.get(ruc=ruc)
            return Response({
                'success': True,
                'existe': True,
                'empresa': {
                    'id': str(empresa.id),
                    'ruc': empresa.ruc,
                    'razon_social': empresa.razon_social
                }
            })
        except Empresa.DoesNotExist:
            return Response({
                'success': True,
                'existe': False,
                'message': 'RUC válido pero no registrado en el sistema'
            })

class GenerarXMLView(APIView):
    """
    Endpoint principal del reto: Genera XML UBL 2.1 firmado
    """
    
    def post(self, request):
        try:
            # 1. Validar datos de entrada
            data = request.data
            
            # Validaciones básicas
            required_fields = [
                'tipo_documento', 'serie', 'numero', 'fecha_emision',
                'empresa_id', 'receptor', 'items'
            ]
            
            for field in required_fields:
                if field not in data:
                    return Response({
                        'success': False,
                        'error': f'Campo requerido: {field}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Validar empresa
            try:
                empresa = Empresa.objects.get(id=data['empresa_id'], activo=True)
            except Empresa.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Empresa no encontrada o inactiva'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 3. Validar tipo de documento
            try:
                tipo_documento = TipoDocumento.objects.get(
                    codigo=data['tipo_documento'], 
                    activo=True
                )
            except TipoDocumento.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Tipo de documento no válido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 4. Validar datos del receptor
            receptor = data['receptor']
            required_receptor_fields = ['tipo_doc', 'numero_doc', 'razon_social']
            
            for field in required_receptor_fields:
                if field not in receptor:
                    return Response({
                        'success': False,
                        'error': f'Campo requerido en receptor: {field}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # 5. Validar items
            items = data['items']
            if not items or len(items) == 0:
                return Response({
                    'success': False,
                    'error': 'Debe incluir al menos un item'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 6. Calcular totales
            subtotal = Decimal('0.00')
            igv_total = Decimal('0.00')
            
            for item in items:
                cantidad = Decimal(str(item.get('cantidad', 0)))
                valor_unitario = Decimal(str(item.get('valor_unitario', 0)))
                valor_venta = cantidad * valor_unitario
                
                # Calcular IGV (18% para afectación '10')
                if item.get('afectacion_igv', '10') == '10':
                    igv_item = valor_venta * Decimal('0.18')
                    igv_total += igv_item
                
                subtotal += valor_venta
            
            total = subtotal + igv_total
            
            # 7. Crear documento en base de datos
            documento = DocumentoElectronico.objects.create(
                empresa=empresa,
                tipo_documento=tipo_documento,
                serie=data['serie'],
                numero=int(data['numero']),
                receptor_tipo_doc=receptor['tipo_doc'],
                receptor_numero_doc=receptor['numero_doc'],
                receptor_razon_social=receptor['razon_social'],
                receptor_direccion=receptor.get('direccion', ''),
                fecha_emision=data['fecha_emision'],
                fecha_vencimiento=data.get('fecha_vencimiento'),
                moneda=data.get('moneda', 'PEN'),
                subtotal=subtotal,
                igv=igv_total,
                total=total,
                estado='PENDIENTE',
                datos_json=data
            )
            
            # 8. Crear líneas del documento
            for i, item in enumerate(items, 1):
                cantidad = Decimal(str(item.get('cantidad', 0)))
                valor_unitario = Decimal(str(item.get('valor_unitario', 0)))
                valor_venta = cantidad * valor_unitario
                
                # Calcular IGV de la línea
                igv_linea = Decimal('0.00')
                if item.get('afectacion_igv', '10') == '10':
                    igv_linea = valor_venta * Decimal('0.18')
                
                DocumentoLinea.objects.create(
                    documento=documento,
                    numero_linea=i,
                    codigo_producto=item.get('codigo_producto', ''),
                    descripcion=item['descripcion'],
                    unidad_medida=item.get('unidad_medida', 'NIU'),
                    cantidad=cantidad,
                    valor_unitario=valor_unitario,
                    valor_venta=valor_venta,
                    afectacion_igv=item.get('afectacion_igv', '10'),
                    igv_linea=igv_linea
                )
            
            # 9. Generar XML UBL 2.1 (por ahora un XML básico)
            xml_content = self._generar_xml_basico(documento)
            documento.xml_content = xml_content
            
            # 10. Simular firma digital (por ahora)
            xml_firmado = self._simular_firma(xml_content)
            documento.xml_firmado = xml_firmado
            documento.hash_digest = 'sha256:' + str(uuid.uuid4())[:32]
            documento.estado = 'FIRMADO'
            documento.save()
            
            # 11. Log de operación
            LogOperacion.objects.create(
                documento=documento,
                operacion='CONVERSION',
                estado='SUCCESS',
                mensaje='XML UBL 2.1 generado y firmado exitosamente',
                duracion_ms=100
            )
            
            # 12. Respuesta exitosa
            return Response({
                'success': True,
                'documento_id': str(documento.id),
                'numero_completo': documento.get_numero_completo(),
                'xml_firmado': xml_firmado,
                'hash': documento.hash_digest,
                'estado': documento.estado,
                'totales': {
                    'subtotal': float(subtotal),
                    'igv': float(igv_total),
                    'total': float(total)
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generar_xml_basico(self, documento):
        """Genera un XML UBL 2.1 básico"""
        
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>2.0</cbc:CustomizationID>
    <cbc:ID>{documento.serie}-{documento.numero:08d}</cbc:ID>
    <cbc:IssueDate>{documento.fecha_emision}</cbc:IssueDate>
    <cbc:InvoiceTypeCode listAgencyName="PE:SUNAT" listName="SUNAT:Identificador de Tipo de Documento" listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01">{documento.tipo_documento.codigo}</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode listID="ISO 4217 Alpha" listName="Currency" listAgencyName="United Nations Economic Commission for Europe">{documento.moneda}</cbc:DocumentCurrencyCode>
    
    <!-- Emisor -->
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6" schemeName="Documento de Identidad" schemeAgencyName="PE:SUNAT" schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06">{documento.empresa.ruc}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name><![CDATA[{documento.empresa.nombre_comercial or documento.empresa.razon_social}]]></cbc:Name>
            </cac:PartyName>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[{documento.empresa.razon_social}]]></cbc:RegistrationName>
                <cac:RegistrationAddress>
                    <cbc:AddressLine>
                        <cbc:Line><![CDATA[{documento.empresa.direccion}]]></cbc:Line>
                    </cbc:AddressLine>
                </cac:RegistrationAddress>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <!-- Receptor -->
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="{documento.receptor_tipo_doc}" schemeName="Documento de Identidad" schemeAgencyName="PE:SUNAT" schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06">{documento.receptor_numero_doc}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[{documento.receptor_razon_social}]]></cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <!-- Totales -->
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="{documento.moneda}">{documento.subtotal}</cbc:LineExtensionAmount>
        <cbc:TaxInclusiveAmount currencyID="{documento.moneda}">{documento.total}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="{documento.moneda}">{documento.total}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    <!-- Líneas del documento -->'''
        
        for linea in documento.lineas.all():
            xml += f'''
    <cac:InvoiceLine>
        <cbc:ID>{linea.numero_linea}</cbc:ID>
        <cbc:InvoicedQuantity unitCode="{linea.unidad_medida}">{linea.cantidad}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="{documento.moneda}">{linea.valor_venta}</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Description><![CDATA[{linea.descripcion}]]></cbc:Description>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="{documento.moneda}">{linea.valor_unitario}</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>'''
        
        xml += '''
</Invoice>'''
        
        return xml
    
    def _simular_firma(self, xml_content):
        """Simula la firma digital (por ahora retorna el XML con un comentario)"""
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- XML FIRMADO DIGITALMENTE - SIMULACIÓN -->
{xml_content[xml_content.find('<Invoice'):]}
<!-- FIRMA DIGITAL SIMULADA - HASH: {str(uuid.uuid4())[:16]} -->'''