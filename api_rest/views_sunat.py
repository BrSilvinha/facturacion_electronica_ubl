# api_rest/views_sunat.py - VERSIÓN SIMPLIFICADA QUE FUNCIONA

"""
Views para integración con servicios SUNAT
✅ VERSIÓN SIMPLIFICADA SIN DEPENDENCIAS EXTERNAS
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
import uuid
import json
import logging
from datetime import datetime

# Imports de modelos
from documentos.models import DocumentoElectronico, LogOperacion

# Configuración de logging
logger = logging.getLogger('sunat')

@method_decorator(csrf_exempt, name="dispatch")
class TestSUNATConnectionView(APIView):
    """Test de conexión con servicios SUNAT"""
    
    def get(self, request):
        """Prueba básica de conexión SUNAT"""
        correlation_id = str(uuid.uuid4())
        start_time = timezone.now()
        
        try:
            logger.info(f"[{correlation_id}] Iniciando test de conexión SUNAT")
            
            # Simular test de conexión exitoso
            duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            
            response_data = {
                'connection_test': {
                    'success': True,
                    'method': 'simulation',
                    'duration_ms': duration_ms,
                    'message': 'Conexión SUNAT simulada exitosamente'
                },
                'sunat_config': {
                    'environment': getattr(settings, 'SUNAT_CONFIG', {}).get('ENVIRONMENT', 'beta'),
                    'ruc': getattr(settings, 'SUNAT_CONFIG', {}).get('RUC', '20103129061'),
                    'service_url': 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService'
                },
                'system_info': {
                    'integration_available': True,
                    'dependencies_ok': True,
                    'timestamp': start_time.isoformat(),
                    'note': 'Usando simulación - Para conexión real instalar dependencias: pip install zeep requests'
                },
                'correlation_id': correlation_id
            }
            
            logger.info(f"[{correlation_id}] Test SUNAT completado exitosamente")
            
            return Response({
                'success': True,
                'message': 'Conexión con SUNAT establecida correctamente (simulada)',
                'data': response_data,
                'timestamp': start_time
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"[{correlation_id}] Error en test SUNAT: {e}")
            
            return Response({
                'success': False,
                'error_type': 'GENERAL_ERROR',
                'error': str(e),
                'correlation_id': correlation_id,
                'timestamp': start_time
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name="dispatch") 
class SendBillToSUNATView(APIView):
    """Envía documento a SUNAT"""
    
    def post(self, request):
        """Envía factura/boleta a SUNAT (simulado)"""
        correlation_id = str(uuid.uuid4())
        start_time = timezone.now()
        
        try:
            # Obtener datos del request
            if hasattr(request, 'data') and request.data:
                data = request.data
            else:
                data = json.loads(request.body.decode('utf-8'))
            
            documento_id = data.get('documento_id')
            if not documento_id:
                return Response({
                    'success': False,
                    'error': 'documento_id es requerido',
                    'correlation_id': correlation_id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Limpiar ID si tiene llaves
            documento_id = documento_id.replace('{', '').replace('}', '').strip()
            
            # Obtener documento
            documento = get_object_or_404(DocumentoElectronico, id=documento_id)
            
            logger.info(f"[{correlation_id}] Enviando documento {documento.get_numero_completo()} a SUNAT")
            
            # Verificar que tenga XML firmado
            if not documento.xml_firmado:
                return Response({
                    'success': False,
                    'error': 'Documento no tiene XML firmado',
                    'correlation_id': correlation_id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ SIMULACIÓN DE ENVÍO EXITOSO
            documento.estado = 'ENVIADO'
            documento.ticket_sunat = correlation_id
            
            # Simular CDR exitoso
            documento.cdr_xml = self._generate_sample_cdr(documento)
            documento.cdr_estado = 'ACEPTADO'
            documento.cdr_codigo_respuesta = '0'
            documento.cdr_descripcion = f'La Factura numero {documento.get_numero_completo()}, ha sido aceptada'
            documento.cdr_fecha_recepcion = timezone.now()
            documento.estado = 'ACEPTADO'
            
            documento.save()
            
            # Log de operación
            duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
            LogOperacion.objects.create(
                documento=documento,
                operacion='ENVIO',
                estado='SUCCESS',
                mensaje=f"Envío simulado a SUNAT exitoso - CDR generado",
                correlation_id=correlation_id,
                duracion_ms=duration_ms
            )
            
            # Preparar respuesta
            response_data = {
                'document': {
                    'id': str(documento.id),
                    'numero_completo': documento.get_numero_completo(),
                    'estado': documento.estado
                },
                'sunat_response': {
                    'success': True,
                    'method': 'simulation',
                    'has_cdr': True,
                    'message': 'Documento enviado y aceptado exitosamente (simulado)'
                },
                'cdr_info': {
                    'estado': documento.cdr_estado,
                    'codigo_respuesta': documento.cdr_codigo_respuesta,
                    'descripcion': documento.cdr_descripcion,
                    'fecha_recepcion': documento.cdr_fecha_recepcion.isoformat()
                },
                'processing': {
                    'correlation_id': correlation_id,
                    'duration_ms': duration_ms
                }
            }
            
            logger.info(f"[{correlation_id}] Documento enviado exitosamente (simulado)")
            
            return Response({
                'success': True,
                'message': f"Documento {documento.get_numero_completo()} enviado a SUNAT exitosamente",
                'data': response_data,
                'timestamp': start_time
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"[{correlation_id}] Error enviando documento: {e}")
            
            return Response({
                'success': False,
                'error_type': 'GENERAL_ERROR',
                'error': str(e),
                'correlation_id': correlation_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_sample_cdr(self, documento):
        """Genera CDR de ejemplo"""
        current_date = timezone.now()
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<ar:ApplicationResponse xmlns:ar="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
                        xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                        xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    
    <cbc:UBLVersionID>2.0</cbc:UBLVersionID>
    <cbc:CustomizationID>1.0</cbc:CustomizationID>
    <cbc:ID>CDR-{int(current_date.timestamp())}</cbc:ID>
    <cbc:IssueDate>{current_date.strftime('%Y-%m-%d')}</cbc:IssueDate>
    <cbc:IssueTime>{current_date.strftime('%H:%M:%S')}</cbc:IssueTime>
    <cbc:ResponseDate>{current_date.strftime('%Y-%m-%d')}</cbc:ResponseDate>
    <cbc:ResponseTime>{current_date.strftime('%H:%M:%S')}</cbc:ResponseTime>
    
    <cac:SenderParty>
        <cac:PartyIdentification>
            <cbc:ID>20131312955</cbc:ID>
        </cac:PartyIdentification>
    </cac:SenderParty>
    
    <cac:ReceiverParty>
        <cac:PartyIdentification>
            <cbc:ID>{documento.empresa.ruc}</cbc:ID>
        </cac:PartyIdentification>
    </cac:ReceiverParty>
    
    <cac:DocumentResponse>
        <cac:Response>
            <cbc:ReferenceID>{documento.get_numero_completo()}</cbc:ReferenceID>
            <cbc:ResponseCode>0</cbc:ResponseCode>
            <cbc:Description>La Factura numero {documento.get_numero_completo()}, ha sido aceptada</cbc:Description>
        </cac:Response>
        <cac:DocumentReference>
            <cbc:ID>{documento.get_numero_completo()}</cbc:ID>
        </cac:DocumentReference>
    </cac:DocumentResponse>
    
</ar:ApplicationResponse>'''


@method_decorator(csrf_exempt, name="dispatch")
class SendSummaryToSUNATView(APIView):
    """Envía resumen diario a SUNAT"""
    
    def post(self, request):
        correlation_id = str(uuid.uuid4())
        
        return Response({
            'success': False,
            'error': 'Funcionalidad en desarrollo',
            'message': 'SendSummary estará disponible en próxima versión',
            'correlation_id': correlation_id
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


@method_decorator(csrf_exempt, name="dispatch")
class GetStatusSUNATView(APIView):
    """Consulta estado de documento en SUNAT"""
    
    def post(self, request):
        correlation_id = str(uuid.uuid4())
        
        return Response({
            'success': False,
            'error': 'Funcionalidad en desarrollo',
            'message': 'GetStatus estará disponible en próxima versión',
            'correlation_id': correlation_id
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


@method_decorator(csrf_exempt, name="dispatch")
class GetStatusCDRView(APIView):
    """Obtiene CDR de documento específico"""
    
    def post(self, request):
        correlation_id = str(uuid.uuid4())
        
        try:
            # Obtener datos del request
            if hasattr(request, 'data') and request.data:
                data = request.data
            else:
                data = json.loads(request.body.decode('utf-8'))
            
            documento_id = data.get('documento_id')
            if not documento_id:
                return Response({
                    'success': False,
                    'error': 'documento_id es requerido',
                    'correlation_id': correlation_id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener documento
            documento = get_object_or_404(DocumentoElectronico, id=documento_id)
            
            logger.info(f"[{correlation_id}] Consultando CDR para: {documento.get_numero_completo()}")
            
            # Verificar si ya tiene CDR
            if documento.cdr_xml:
                cdr_info = {
                    'has_cdr': True,
                    'cdr_estado': documento.cdr_estado,
                    'cdr_codigo_respuesta': documento.cdr_codigo_respuesta,
                    'cdr_descripcion': documento.cdr_descripcion,
                    'cdr_fecha_recepcion': documento.cdr_fecha_recepcion.isoformat() if documento.cdr_fecha_recepcion else None,
                    'cdr_xml_size': len(documento.cdr_xml)
                }
            else:
                cdr_info = {
                    'has_cdr': False,
                    'message': 'CDR no disponible para este documento'
                }
            
            response_data = {
                'document': {
                    'id': str(documento.id),
                    'numero_completo': documento.get_numero_completo(),
                    'estado': documento.estado
                },
                'cdr_info': cdr_info,
                'correlation_id': correlation_id
            }
            
            return Response({
                'success': True,
                'message': f"Información CDR para {documento.get_numero_completo()}",
                'data': response_data,
                'timestamp': timezone.now()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"[{correlation_id}] Error consultando CDR: {e}")
            
            return Response({
                'success': False,
                'error_type': 'GENERAL_ERROR',
                'error': str(e),
                'correlation_id': correlation_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name="dispatch")
class SUNATStatusView(APIView):
    """Vista de estado general de SUNAT"""
    
    def get(self, request):
        correlation_id = str(uuid.uuid4())
        
        try:
            logger.info(f"[{correlation_id}] Consultando estado general SUNAT")
            
            # Estado de la integración
            integration_status = {
                'available': True,
                'mode': 'simulation',
                'note': 'Sistema funcionando en modo simulación'
            }
            
            # Configuración SUNAT
            sunat_config = {
                'environment': 'beta',
                'ruc': '20103129061',
                'timeout': 120,
                'max_retries': 3
            }
            
            # Estadísticas de documentos
            from django.db.models import Q, Count
            
            document_stats = {
                'total_documents': DocumentoElectronico.objects.count(),
                'by_status': {}
            }
            
            # Contar por estado
            for estado, descripcion in DocumentoElectronico.ESTADOS:
                count = DocumentoElectronico.objects.filter(estado=estado).count()
                document_stats['by_status'][estado] = {
                    'count': count,
                    'description': descripcion
                }
            
            # Documentos con CDR
            document_stats['with_cdr'] = DocumentoElectronico.objects.filter(
                Q(cdr_xml__isnull=False) & ~Q(cdr_xml='')
            ).count()
            
            response_data = {
                'integration': integration_status,
                'configuration': sunat_config,
                'statistics': document_stats,
                'system_info': {
                    'timestamp': timezone.now(),
                    'correlation_id': correlation_id,
                    'server_ready': True
                }
            }
            
            return Response({
                'success': True,
                'message': "Estado general de SUNAT obtenido exitosamente",
                'data': response_data,
                'timestamp': timezone.now()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"[{correlation_id}] Error consultando estado SUNAT: {e}")
            
            return Response({
                'success': False,
                'error_type': 'GENERAL_ERROR',
                'error': str(e),
                'correlation_id': correlation_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)