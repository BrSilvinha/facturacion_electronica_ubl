"""
Endpoints de API para integración con SUNAT
Ubicación: api_rest/views_sunat.py
VERSIÓN CORREGIDA - Usa lazy loading para clientes SUNAT
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
import logging

from documentos.models import DocumentoElectronico, LogOperacion
from sunat_integration import (
    get_sunat_client, cdr_processor, SUNATError, 
    SUNATConnectionError, SUNATAuthenticationError, SUNATValidationError
)

logger = logging.getLogger('sunat')

class TestSUNATConnectionView(APIView):
    """Prueba la conexión con SUNAT Beta"""
    
    def get(self, request):
        """Prueba conexión básica"""
        try:
            # Obtener cliente con lazy loading
            client = get_sunat_client('factura')
            
            # Probar conexión
            result = client.test_connection()
            
            return Response({
                'success': result['success'],
                'message': result.get('message', 'Conexión probada'),
                'service_info': result.get('service_info', {}),
                'timestamp': result['timestamp']
            })
            
        except Exception as e:
            logger.error(f"Error probando conexión SUNAT: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendBillToSUNATView(APIView):
    """Envía documento individual a SUNAT (síncrono)"""
    
    def post(self, request):
        """
        Envía factura, nota de crédito o débito a SUNAT
        
        Body:
        {
            "documento_id": "uuid-del-documento"
        }
        """
        
        try:
            # Validar datos
            documento_id = request.data.get('documento_id')
            if not documento_id:
                return Response({
                    'success': False,
                    'error': 'documento_id es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener documento
            documento = get_object_or_404(
                DocumentoElectronico, 
                id=documento_id
            )
            
            # Validar que esté firmado
            if not documento.xml_firmado:
                return Response({
                    'success': False,
                    'error': 'Documento no está firmado digitalmente'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar estado
            if documento.estado in ['ENVIADO', 'ACEPTADO']:
                return Response({
                    'success': False,
                    'error': f'Documento ya fue enviado (estado: {documento.estado})'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar tipo de documento soportado
            if documento.tipo_documento.codigo not in ['01', '07', '08']:
                return Response({
                    'success': False,
                    'error': f'Tipo de documento {documento.tipo_documento.codigo} no soportado para sendBill'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            start_time = timezone.now()
            
            # Obtener cliente SUNAT
            client = get_sunat_client('factura')
            
            # Enviar a SUNAT
            try:
                logger.info(f"Enviando documento {documento.get_numero_completo()} a SUNAT")
                
                response = client.send_bill(documento, documento.xml_firmado)
                
                # Procesar CDR
                cdr_data = cdr_processor.process_cdr_zip(response['cdr_content'])
                
                # Actualizar estado del documento
                if cdr_data['is_accepted']:
                    documento.estado = 'ACEPTADO'
                    log_message = f"Documento aceptado por SUNAT. CDR: {cdr_data['cdr_id']}"
                    log_estado = 'SUCCESS'
                else:
                    documento.estado = 'RECHAZADO'
                    log_message = f"Documento rechazado por SUNAT. Código: {cdr_data['response_code']}"
                    log_estado = 'ERROR'
                
                documento.save()
                
                # Log de operación
                duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)
                LogOperacion.objects.create(
                    documento=documento,
                    operacion='ENVIO',
                    estado=log_estado,
                    mensaje=log_message,
                    duracion_ms=duration_ms
                )
                
                return Response({
                    'success': True,
                    'document_id': str(documento.id),
                    'document_number': documento.get_numero_completo(),
                    'sunat_response': {
                        'method': response['method'],
                        'duration_ms': response['duration_ms'],
                        'correlation_id': response['correlation_id']
                    },
                    'cdr_info': {
                        'cdr_id': cdr_data['cdr_id'],
                        'is_accepted': cdr_data['is_accepted'],
                        'is_rejected': cdr_data['is_rejected'],
                        'response_code': cdr_data['response_code'],
                        'response_description': cdr_data['response_description'],
                        'notes_count': len(cdr_data['notes']),
                        'status_summary': cdr_data['status_summary']
                    },
                    'document_status': documento.estado,
                    'timestamp': timezone.now()
                })
                
            except SUNATAuthenticationError as e:
                # Error de autenticación
                documento.estado = 'ERROR'
                documento.save()
                
                LogOperacion.objects.create(
                    documento=documento,
                    operacion='ENVIO',
                    estado='ERROR',
                    mensaje=f'Error autenticación SUNAT: {str(e)}'
                )
                
                return Response({
                    'success': False,
                    'error': 'Error de autenticación con SUNAT',
                    'error_type': 'AUTHENTICATION_ERROR',
                    'details': str(e)
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            except SUNATValidationError as e:
                # Error de validación
                documento.estado = 'RECHAZADO'
                documento.save()
                
                LogOperacion.objects.create(
                    documento=documento,
                    operacion='ENVIO',
                    estado='ERROR',
                    mensaje=f'Error validación SUNAT: {str(e)}'
                )
                
                return Response({
                    'success': False,
                    'error': 'Documento rechazado por SUNAT',
                    'error_type': 'VALIDATION_ERROR',
                    'details': str(e),
                    'error_code': getattr(e, 'error_code', None)
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
            except SUNATConnectionError as e:
                # Error de conexión - documento queda pendiente
                LogOperacion.objects.create(
                    documento=documento,
                    operacion='ENVIO',
                    estado='ERROR',
                    mensaje=f'Error conexión SUNAT: {str(e)}'
                )
                
                return Response({
                    'success': False,
                    'error': 'Error de conexión con SUNAT',
                    'error_type': 'CONNECTION_ERROR',
                    'details': str(e),
                    'retry_suggestion': 'Intente nuevamente en unos minutos'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.error(f"Error inesperado enviando documento: {e}")
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SendSummaryToSUNATView(APIView):
    """Envía resumen diario a SUNAT (asíncrono)"""
    
    def post(self, request):
        """
        Envía resumen diario de boletas
        
        Body:
        {
            "ruc": "20123456789",
            "fecha_emision": "2025-06-28",
            "correlativo": 1,
            "tipo_resumen": "RC"  // RC = Resumen, RA = Baja
        }
        """
        
        try:
            # Validar datos requeridos
            required_fields = ['ruc', 'fecha_emision', 'correlativo', 'tipo_resumen']
            for field in required_fields:
                if field not in request.data:
                    return Response({
                        'success': False,
                        'error': f'Campo requerido: {field}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extraer datos
            ruc = request.data['ruc']
            fecha_emision = request.data['fecha_emision']
            correlativo = request.data['correlativo']
            tipo_resumen = request.data['tipo_resumen']
            
            # Generar nombre de archivo
            archivo_resumen = f"{ruc}-{tipo_resumen}-{fecha_emision.replace('-', '')}-{correlativo}"
            
            # XML de resumen de ejemplo (simplificado)
            xml_resumen = f'''<?xml version="1.0" encoding="UTF-8"?>
<SummaryDocuments xmlns="urn:sunat:names:specification:ubl:peru:schema:xsd:SummaryDocuments-1">
    <cbc:UBLVersionID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">2.0</cbc:UBLVersionID>
    <cbc:CustomizationID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">1.1</cbc:CustomizationID>
    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{archivo_resumen}</cbc:ID>
    <cbc:ReferenceDate xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{fecha_emision}</cbc:ReferenceDate>
    <cbc:IssueDate xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">{fecha_emision}</cbc:IssueDate>
</SummaryDocuments>'''
            
            try:
                logger.info(f"Enviando resumen {archivo_resumen} a SUNAT")
                
                # Obtener cliente SUNAT
                client = get_sunat_client('factura')
                
                response = client.send_summary(archivo_resumen, xml_resumen)
                
                return Response({
                    'success': True,
                    'filename': archivo_resumen,
                    'ticket': response['ticket'],
                    'sunat_response': {
                        'method': response['method'],
                        'duration_ms': response['duration_ms'],
                        'correlation_id': response['correlation_id']
                    },
                    'message': 'Resumen enviado exitosamente. Use el ticket para consultar el estado.',
                    'next_step': f'Consultar estado con ticket: {response["ticket"]}',
                    'timestamp': timezone.now()
                })
                
            except SUNATError as e:
                return Response({
                    'success': False,
                    'error': f'Error enviando resumen: {str(e)}',
                    'error_type': type(e).__name__
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                
        except Exception as e:
            logger.error(f"Error inesperado enviando resumen: {e}")
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetStatusSUNATView(APIView):
    """Consulta estado de procesamiento por ticket"""
    
    def post(self, request):
        """
        Consulta estado por ticket
        
        Body:
        {
            "ticket": "202506281234567890"
        }
        """
        
        try:
            ticket = request.data.get('ticket')
            if not ticket:
                return Response({
                    'success': False,
                    'error': 'ticket es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                logger.info(f"Consultando estado de ticket: {ticket}")
                
                # Obtener cliente SUNAT
                client = get_sunat_client('factura')
                
                response = client.get_status(ticket)
                
                result = {
                    'success': True,
                    'ticket': ticket,
                    'status_code': response['status_code'],
                    'status_message': response['status_message'],
                    'processed': response.get('processed', False),
                    'in_progress': response.get('in_progress', False),
                    'has_errors': response.get('has_errors', False),
                    'sunat_response': {
                        'method': response['method'],
                        'duration_ms': response['duration_ms'],
                        'correlation_id': response['correlation_id']
                    },
                    'timestamp': timezone.now()
                }
                
                # Si hay CDR disponible, procesarlo
                if 'cdr_content' in response and response['cdr_content']:
                    cdr_data = cdr_processor.process_cdr_zip(response['cdr_content'])
                    
                    result['cdr_info'] = {
                        'cdr_id': cdr_data['cdr_id'],
                        'is_accepted': cdr_data['is_accepted'],
                        'is_rejected': cdr_data['is_rejected'],
                        'response_code': cdr_data['response_code'],
                        'response_description': cdr_data['response_description'],
                        'notes_count': len(cdr_data['notes']),
                        'status_summary': cdr_data['status_summary']
                    }
                    
                    if cdr_data['notes']:
                        result['cdr_info']['notes'] = cdr_data['notes']
                
                return Response(result)
                
            except SUNATError as e:
                return Response({
                    'success': False,
                    'error': f'Error consultando ticket: {str(e)}',
                    'error_type': type(e).__name__
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                
        except Exception as e:
            logger.error(f"Error consultando ticket: {e}")
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetStatusCDRView(APIView):
    """Consulta CDR por datos del comprobante"""
    
    def post(self, request):
        """
        Consulta CDR por datos del documento
        
        Body:
        {
            "ruc": "20123456789",
            "tipo_documento": "01",
            "serie": "F001",
            "numero": 1
        }
        """
        
        try:
            # Validar datos requeridos
            required_fields = ['ruc', 'tipo_documento', 'serie', 'numero']
            for field in required_fields:
                if field not in request.data:
                    return Response({
                        'success': False,
                        'error': f'Campo requerido: {field}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            ruc = request.data['ruc']
            tipo_documento = request.data['tipo_documento']
            serie = request.data['serie']
            numero = int(request.data['numero'])
            
            try:
                logger.info(f"Consultando CDR: {ruc}-{tipo_documento}-{serie}-{numero:08d}")
                
                # Obtener cliente SUNAT
                client = get_sunat_client('factura')
                
                response = client.get_status_cdr(ruc, tipo_documento, serie, numero)
                
                result = {
                    'success': True,
                    'document_id': response['document_id'],
                    'status_code': response['status_code'],
                    'status_message': response['status_message'],
                    'cdr_available': response['cdr_available'],
                    'sunat_response': {
                        'method': response['method'],
                        'duration_ms': response['duration_ms'],
                        'correlation_id': response['correlation_id']
                    },
                    'timestamp': timezone.now()
                }
                
                # Si hay CDR disponible, procesarlo
                if response['cdr_available'] and 'cdr_content' in response:
                    cdr_data = cdr_processor.process_cdr_zip(response['cdr_content'])
                    
                    result['cdr_info'] = {
                        'cdr_id': cdr_data['cdr_id'],
                        'is_accepted': cdr_data['is_accepted'],
                        'is_rejected': cdr_data['is_rejected'],
                        'response_code': cdr_data['response_code'],
                        'response_description': cdr_data['response_description'],
                        'notes_count': len(cdr_data['notes']),
                        'status_summary': cdr_data['status_summary']
                    }
                    
                    if cdr_data['notes']:
                        result['cdr_info']['notes'] = cdr_data['notes']
                
                return Response(result)
                
            except SUNATError as e:
                return Response({
                    'success': False,
                    'error': f'Error consultando CDR: {str(e)}',
                    'error_type': type(e).__name__
                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                
        except Exception as e:
            logger.error(f"Error consultando CDR: {e}")
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SUNATStatusView(APIView):
    """Información general del estado de integración SUNAT"""
    
    def get(self, request):
        """Retorna estado general de la integración"""
        
        try:
            from django.conf import settings
            from sunat_integration import MODULE_INFO
            
            config = settings.SUNAT_CONFIG
            
            # Probar conexión rápida
            try:
                client = get_sunat_client('factura')
                connection_test = client.test_connection()
                connection_status = connection_test['success']
                connection_error = None if connection_status else connection_test.get('error')
            except Exception as e:
                connection_status = False
                connection_error = str(e)
            
            # Estadísticas de documentos
            from documentos.models import DocumentoElectronico
            
            doc_stats = {
                'total_documentos': DocumentoElectronico.objects.count(),
                'documentos_firmados': DocumentoElectronico.objects.exclude(xml_firmado__isnull=True).count(),
                'documentos_enviados': DocumentoElectronico.objects.filter(estado__in=['ENVIADO', 'ACEPTADO']).count(),
                'documentos_aceptados': DocumentoElectronico.objects.filter(estado='ACEPTADO').count(),
                'documentos_rechazados': DocumentoElectronico.objects.filter(estado='RECHAZADO').count(),
            }
            
            return Response({
                'success': True,
                'sunat_integration': {
                    'version': MODULE_INFO['version'],
                    'environment': config['ENVIRONMENT'],
                    'ruc': config['RUC'],
                    'connection_status': connection_status,
                    'connection_error': connection_error,
                    'supported_documents': MODULE_INFO['supported_documents'],
                    'supported_operations': MODULE_INFO['supported_operations']
                },
                'document_statistics': doc_stats,
                'timestamp': timezone.now()
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo estado SUNAT: {e}")
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)