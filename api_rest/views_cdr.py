# api_rest/views_cdr.py
"""
Views para procesamiento de CDR (Constancia de Recepción)
VERSIÓN CORREGIDA - Sin errores de importación
"""

import base64
import zipfile
import json
import time
from io import BytesIO
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone

from documentos.models import DocumentoElectronico, LogOperacion

# Importación segura del parser CDR
try:
    from sunat_integration.cdr_parser import cdr_parser, cdr_generator
    CDR_PARSER_AVAILABLE = True
except ImportError:
    CDR_PARSER_AVAILABLE = False
    print("⚠️ CDR Parser no disponible. Crear archivo: sunat_integration/cdr_parser.py")

@method_decorator(csrf_exempt, name="dispatch")
class ProcessCDRView(APIView):
    """Procesa CDR XML y actualiza estado del documento"""
    
    def post(self, request):
        """
        Procesa CDR XML recibido
        
        Payload esperado:
        {
            "documento_id": "uuid-del-documento",
            "cdr_xml": "XML del CDR",
            "cdr_base64": "CDR en base64 (alternativo)",
            "cdr_zip_base64": "ZIP CDR en base64 (alternativo)"
        }
        """
        try:
            # Verificar disponibilidad del parser
            if not CDR_PARSER_AVAILABLE:
                return Response({
                    'success': False,
                    'error': 'CDR Parser no disponible. Crear archivo: sunat_integration/cdr_parser.py',
                    'help': 'Instalar lxml: pip install lxml'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Obtener datos del request
            if hasattr(request, 'data') and request.data:
                data = request.data
            else:
                data = json.loads(request.body.decode('utf-8'))
            
            documento_id = data.get('documento_id')
            
            if not documento_id:
                return Response({
                    'success': False,
                    'error': 'documento_id es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener documento
            documento = get_object_or_404(DocumentoElectronico, id=documento_id)
            
            # Obtener XML CDR de diferentes formas
            cdr_xml = None
            
            if data.get('cdr_xml'):
                # XML directo
                cdr_xml = data['cdr_xml']
            elif data.get('cdr_base64'):
                # XML en base64
                try:
                    cdr_xml = base64.b64decode(data['cdr_base64']).decode('utf-8')
                except Exception as e:
                    return Response({
                        'success': False,
                        'error': f'Error decodificando cdr_base64: {e}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif data.get('cdr_zip_base64'):
                # ZIP CDR en base64
                try:
                    zip_data = base64.b64decode(data['cdr_zip_base64'])
                    cdr_xml = self._extract_xml_from_zip(zip_data)
                except Exception as e:
                    return Response({
                        'success': False,
                        'error': f'Error procesando ZIP CDR: {e}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'success': False,
                    'error': 'Se requiere cdr_xml, cdr_base64 o cdr_zip_base64'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Procesar CDR
            cdr_data = cdr_parser.parse_cdr_xml(cdr_xml)
            
            # Actualizar documento
            self._update_document_with_cdr(documento, cdr_data, cdr_xml)
            
            # Log de operación
            LogOperacion.objects.create(
                documento=documento,
                operacion='CDR_PROCESADO',
                estado='SUCCESS',
                mensaje=f'CDR procesado: {cdr_data.get("status", "PROCESADO")}',
                correlation_id=data.get('correlation_id', 'CDR-API')
            )
            
            return Response({
                'success': True,
                'documento_id': str(documento.id),
                'numero_completo': documento.get_numero_completo(),
                'cdr_data': cdr_data,
                'documento_estado': documento.estado,
                'message': f'CDR procesado exitosamente - Estado: {cdr_data.get("status", "PROCESADO")}'
            })
            
        except ValueError as e:
            return Response({
                'success': False,
                'error': f'Error de validación: {e}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error interno: {e}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _extract_xml_from_zip(self, zip_data: bytes) -> str:
        """Extrae XML CDR desde archivo ZIP"""
        with zipfile.ZipFile(BytesIO(zip_data), 'r') as zip_file:
            # Buscar archivo que comience con 'R-'
            cdr_files = [f for f in zip_file.namelist() 
                        if f.startswith('R-') and f.endswith('.xml')]
            
            if not cdr_files:
                raise ValueError("No se encontró archivo CDR en el ZIP")
            
            # Leer primer archivo CDR
            return zip_file.read(cdr_files[0]).decode('utf-8')
    
    def _update_document_with_cdr(self, documento, cdr_data: dict, cdr_xml: str):
        """Actualiza documento con información del CDR"""
        
        # Actualizar campos CDR
        documento.cdr_xml = cdr_xml
        documento.cdr_estado = cdr_data.get('status', 'PROCESADO')
        documento.cdr_codigo_respuesta = cdr_data.get('response_code', '0')
        documento.cdr_descripcion = cdr_data.get('response_description', 'CDR procesado')
        documento.cdr_fecha_recepcion = timezone.now()
        
        # Actualizar estado del documento
        if cdr_data.get('is_accepted'):
            documento.estado = 'ACEPTADO'
        elif cdr_data.get('is_rejected'):
            documento.estado = 'RECHAZADO'
        else:
            documento.estado = 'PROCESADO'
        
        documento.save()

@method_decorator(csrf_exempt, name="dispatch")
class GenerateCDRView(APIView):
    """Genera CDR simulado para testing"""
    
    def post(self, request):
        """
        Genera CDR simulado
        
        Payload:
        {
            "documento_id": "uuid-del-documento",
            "response_code": "0",  # Opcional, default "0"
            "description": "Descripción personalizada"  # Opcional
        }
        """
        try:
            # Verificar disponibilidad del generador
            if not CDR_PARSER_AVAILABLE:
                return Response({
                    'success': False,
                    'error': 'CDR Generator no disponible. Crear archivo: sunat_integration/cdr_parser.py'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Obtener datos del request
            if hasattr(request, 'data') and request.data:
                data = request.data
            else:
                data = json.loads(request.body.decode('utf-8'))
            
            documento_id = data.get('documento_id')
            
            if not documento_id:
                return Response({
                    'success': False,
                    'error': 'documento_id es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener documento
            documento = get_object_or_404(DocumentoElectronico, id=documento_id)
            
            # Parámetros del CDR
            response_code = data.get('response_code', '0')
            description = data.get('description')
            
            # Generar CDR
            cdr_xml = cdr_generator.generate_cdr_response(
                documento, response_code, description
            )
            
            # Procesar CDR generado
            cdr_data = cdr_parser.parse_cdr_xml(cdr_xml)
            
            # Actualizar documento si se solicita
            if data.get('update_document', True):
                self._update_document_with_cdr(documento, cdr_data, cdr_xml)
            
            # CDR en base64 para compatibilidad
            cdr_base64 = base64.b64encode(cdr_xml.encode('utf-8')).decode('ascii')
            
            return Response({
                'success': True,
                'documento_id': str(documento.id),
                'numero_completo': documento.get_numero_completo(),
                'cdr_xml': cdr_xml,
                'cdr_base64': cdr_base64,
                'cdr_data': cdr_data,
                'generated_at': timezone.now(),
                'message': 'CDR generado exitosamente'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error generando CDR: {e}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _update_document_with_cdr(self, documento, cdr_data: dict, cdr_xml: str):
        """Actualiza documento con CDR generado"""
        
        documento.cdr_xml = cdr_xml
        documento.cdr_estado = cdr_data.get('status', 'PROCESADO')
        documento.cdr_codigo_respuesta = cdr_data.get('response_code', '0')
        documento.cdr_descripcion = cdr_data.get('response_description', 'CDR generado')
        documento.cdr_fecha_recepcion = timezone.now()
        
        if cdr_data.get('is_accepted'):
            documento.estado = 'ACEPTADO'
        elif cdr_data.get('is_rejected'):
            documento.estado = 'RECHAZADO'
        
        documento.save()

@method_decorator(csrf_exempt, name="dispatch")
class CDRStatusView(APIView):
    """Consulta estado del CDR de un documento"""
    
    def get(self, request, documento_id):
        """Obtiene información completa del CDR"""
        try:
            documento = get_object_or_404(DocumentoElectronico, id=documento_id)
            
            response_data = {
                'success': True,
                'documento_id': str(documento.id),
                'numero_completo': documento.get_numero_completo(),
                'tiene_cdr': bool(documento.cdr_xml),
                'estado_documento': documento.estado
            }
            
            if documento.cdr_xml:
                # Procesar CDR existente si el parser está disponible
                if CDR_PARSER_AVAILABLE:
                    try:
                        cdr_data = cdr_parser.parse_cdr_xml(documento.cdr_xml)
                        response_data.update({
                            'cdr_info': {
                                'estado': documento.cdr_estado,
                                'codigo_respuesta': documento.cdr_codigo_respuesta,
                                'descripcion': documento.cdr_descripcion,
                                'fecha_recepcion': documento.cdr_fecha_recepcion,
                                'cdr_data': cdr_data
                            }
                        })
                    except Exception as e:
                        response_data['cdr_info'] = {
                            'error': f'Error procesando CDR: {e}',
                            'raw_cdr_available': True
                        }
                else:
                    response_data['cdr_info'] = {
                        'estado': documento.cdr_estado,
                        'codigo_respuesta': documento.cdr_codigo_respuesta,
                        'descripcion': documento.cdr_descripcion,
                        'fecha_recepcion': documento.cdr_fecha_recepcion,
                        'parser_available': False
                    }
            else:
                response_data.update({
                    'cdr_info': None,
                    'message': 'Documento sin CDR'
                })
            
            return Response(response_data)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error consultando CDR: {e}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name="dispatch")
class SimulateSUNATResponseView(APIView):
    """Simula respuesta completa de SUNAT con CDR"""
    
    def post(self, request):
        """
        Simula envío a SUNAT y generación de CDR
        
        Payload:
        {
            "documento_id": "uuid-del-documento",
            "simulate_acceptance": true,  # true=aceptado, false=rechazado
            "response_code": "0",  # Código específico
            "custom_description": "Descripción personalizada"
        }
        """
        try:
            # Verificar disponibilidad
            if not CDR_PARSER_AVAILABLE:
                return Response({
                    'success': False,
                    'error': 'CDR Generator no disponible. Crear archivo: sunat_integration/cdr_parser.py'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Obtener datos del request
            if hasattr(request, 'data') and request.data:
                data = request.data
            else:
                data = json.loads(request.body.decode('utf-8'))
            
            documento_id = data.get('documento_id')
            
            if not documento_id:
                return Response({
                    'success': False,
                    'error': 'documento_id es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            documento = get_object_or_404(DocumentoElectronico, id=documento_id)
            
            # Determinar tipo de respuesta
            simulate_acceptance = data.get('simulate_acceptance', True)
            
            if simulate_acceptance:
                response_code = data.get('response_code', '0')
                if not data.get('custom_description'):
                    description = f"La Factura numero {documento.get_numero_completo()}, ha sido aceptada"
                else:
                    description = data['custom_description']
            else:
                response_code = data.get('response_code', '2001')
                if not data.get('custom_description'):
                    description = f"La Factura numero {documento.get_numero_completo()}, ha sido rechazada por errores de validación"
                else:
                    description = data['custom_description']
            
            # Generar CDR
            cdr_xml = cdr_generator.generate_cdr_response(
                documento, response_code, description
            )
            
            # Procesar CDR
            cdr_data = cdr_parser.parse_cdr_xml(cdr_xml)
            
            # Actualizar documento
            self._update_document_with_cdr(documento, cdr_data, cdr_xml)
            
            # Simular tiempo de procesamiento
            time.sleep(1)
            
            # Log de simulación
            LogOperacion.objects.create(
                documento=documento,
                operacion='SUNAT_SIMULATION',
                estado='SUCCESS',
                mensaje=f'Simulación SUNAT completada - Estado: {cdr_data.get("status", "PROCESADO")}',
                correlation_id=data.get('correlation_id', 'SUNAT-SIM')
            )
            
            # Respuesta completa
            return Response({
                'success': True,
                'simulation': True,
                'documento_id': str(documento.id),
                'numero_completo': documento.get_numero_completo(),
                'sunat_response': {
                    'accepted': cdr_data.get('is_accepted', False),
                    'rejected': cdr_data.get('is_rejected', False),
                    'response_code': response_code,
                    'description': description,
                    'has_cdr': True
                },
                'cdr_xml': cdr_xml,
                'cdr_base64': base64.b64encode(cdr_xml.encode('utf-8')).decode('ascii'),
                'cdr_data': cdr_data,
                'documento_estado': documento.estado,
                'processed_at': timezone.now(),
                'message': f'Simulación SUNAT completada - Documento {cdr_data.get("status", "PROCESADO")}'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error en simulación SUNAT: {e}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _update_document_with_cdr(self, documento, cdr_data: dict, cdr_xml: str):
        """Actualiza documento con CDR"""
        documento.cdr_xml = cdr_xml
        documento.cdr_estado = cdr_data.get('status', 'PROCESADO')
        documento.cdr_codigo_respuesta = cdr_data.get('response_code', '0')
        documento.cdr_descripcion = cdr_data.get('response_description', 'Simulación SUNAT')
        documento.cdr_fecha_recepcion = timezone.now()
        
        if cdr_data.get('is_accepted'):
            documento.estado = 'ACEPTADO'
        elif cdr_data.get('is_rejected'):
            documento.estado = 'RECHAZADO'
        
        documento.save()

@method_decorator(csrf_exempt, name="dispatch")
class CDRTestView(APIView):
    """Vista de prueba para testing rápido del sistema CDR"""
    
    def get(self, request):
        """Información del sistema CDR"""
        return Response({
            'success': True,
            'system': 'CDR Processing System',
            'version': '1.0',
            'parser_available': CDR_PARSER_AVAILABLE,
            'endpoints': {
                'process': '/api/cdr/process/',
                'generate': '/api/cdr/generate/',
                'status': '/api/cdr/status/{id}/',
                'simulate': '/api/cdr/simulate-sunat/',
                'test': '/api/cdr/test/'
            },
            'supported_formats': [
                'cdr_xml - XML directo',
                'cdr_base64 - XML en base64',
                'cdr_zip_base64 - ZIP con CDR en base64'
            ],
            'response_codes': {
                '0': 'Aceptado',
                '2xxx': 'Rechazado por errores',
                '3xxx': 'Rechazado por contenido',
                '4xxx': 'Aceptado con observaciones'
            },
            'installation_help': {
                'missing_parser': 'Crear archivo: sunat_integration/cdr_parser.py',
                'install_lxml': 'pip install lxml'
            } if not CDR_PARSER_AVAILABLE else None
        })
    
    def post(self, request):
        """Prueba rápida con CDR de ejemplo"""
        try:
            # CDR de ejemplo mínimo
            cdr_ejemplo = '''<?xml version="1.0" encoding="UTF-8"?>
<ar:ApplicationResponse xmlns:ar="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
                        xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
                        xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
  <cbc:UBLVersionID>2.0</cbc:UBLVersionID>
  <cbc:ID>TEST123456789</cbc:ID>
  <cbc:ResponseDate>2025-07-14</cbc:ResponseDate>
  <cbc:ResponseTime>12:00:00</cbc:ResponseTime>
  
  <cac:SenderParty>
    <cac:PartyIdentification>
      <cbc:ID>20131312955</cbc:ID>
    </cac:PartyIdentification>
  </cac:SenderParty>
  
  <cac:DocumentResponse>
    <cac:Response>
      <cbc:ReferenceID>TEST-001</cbc:ReferenceID>
      <cbc:ResponseCode>0</cbc:ResponseCode>
      <cbc:Description>Documento de prueba aceptado</cbc:Description>
    </cac:Response>
  </cac:DocumentResponse>
</ar:ApplicationResponse>'''
            
            if not CDR_PARSER_AVAILABLE:
                return Response({
                    'success': False,
                    'error': 'CDR Parser no disponible',
                    'help': 'Crear archivo: sunat_integration/cdr_parser.py e instalar lxml'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Procesar CDR de prueba
            cdr_data = cdr_parser.parse_cdr_xml(cdr_ejemplo)
            
            return Response({
                'success': True,
                'test_result': 'CDR procesado correctamente',
                'sample_cdr_data': cdr_data,
                'parser_working': True,
                'message': 'Sistema CDR funcionando correctamente'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error en prueba CDR: {e}',
                'parser_working': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)