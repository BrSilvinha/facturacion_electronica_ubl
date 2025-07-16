# api_rest/views_test_scenarios.py - VIEWS DE ESCENARIOS DE PRUEBA BÁSICOS

"""
Views para escenarios de prueba de facturación electrónica
VERSIÓN BÁSICA - Para testing y desarrollo
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import uuid
import logging

logger = logging.getLogger('api_rest')

@method_decorator(csrf_exempt, name="dispatch")
class TestScenariosMenuView(APIView):
    """Menú de escenarios de prueba disponibles"""
    
    def get(self, request):
        """Retorna menú de escenarios de prueba"""
        
        scenarios = {
            'title': 'Escenarios de Prueba - Facturación Electrónica UBL 2.1',
            'description': 'Escenarios predefinidos para testing de documentos',
            'scenarios': [
                {
                    'id': 'scenario-1',
                    'name': 'Boleta Completa',
                    'description': 'Boleta con IGV gravado y productos variados',
                    'endpoint': '/api/test/scenario-1-boleta-completa/',
                    'method': 'POST',
                    'status': 'available'
                },
                {
                    'id': 'scenario-2', 
                    'name': 'Factura Gravada',
                    'description': 'Factura con IGV gravado estándar',
                    'endpoint': '/api/test/scenario-2-factura-gravada/',
                    'method': 'POST',
                    'status': 'available'
                },
                {
                    'id': 'scenario-3',
                    'name': 'Factura Exonerada',
                    'description': 'Factura con productos exonerados de IGV',
                    'endpoint': '/api/test/scenario-3-factura-exonerada/',
                    'method': 'POST',
                    'status': 'in_development'
                },
                {
                    'id': 'scenario-4',
                    'name': 'Factura Mixta',
                    'description': 'Factura con productos gravados y exonerados',
                    'endpoint': '/api/test/scenario-4-factura-mixta/',
                    'method': 'POST',
                    'status': 'in_development'
                },
                {
                    'id': 'scenario-5',
                    'name': 'Factura Exportación',
                    'description': 'Factura de exportación',
                    'endpoint': '/api/test/scenario-5-factura-exportacion/',
                    'method': 'POST',
                    'status': 'in_development'
                }
            ],
            'instructions': {
                'usage': 'Usar POST en los endpoints para ejecutar escenarios',
                'example': 'curl -X POST http://localhost:8000/api/test/scenario-1-boleta-completa/',
                'note': 'Los escenarios crean documentos de prueba automáticamente'
            },
            'system_info': {
                'api_ready': True,
                'timestamp': timezone.now(),
                'correlation_id': str(uuid.uuid4())
            }
        }
        
        return Response(scenarios, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name="dispatch")
class TestScenario1BoletaCompleta(APIView):
    """Escenario 1: Boleta completa con IGV"""
    
    def post(self, request):
        """Ejecuta escenario de boleta completa"""
        
        correlation_id = str(uuid.uuid4())
        
        try:
            logger.info(f"[{correlation_id}] Ejecutando Escenario 1: Boleta Completa")
            
            # Datos del escenario de prueba
            test_data = {
                'tipo_documento': '03',  # Boleta
                'serie': 'B001',
                'numero': 1,
                'fecha_emision': '2025-07-15',
                'moneda': 'PEN',
                'empresa_id': '00000000-0000-0000-0000-000000000000',  # Placeholder
                'receptor': {
                    'tipo_doc': '1',
                    'numero_doc': '12345678',
                    'razon_social': 'CLIENTE DE PRUEBA',
                    'direccion': 'AV. PRINCIPAL 123'
                },
                'items': [
                    {
                        'codigo_producto': 'PROD001',
                        'descripcion': 'PRODUCTO DE PRUEBA 1',
                        'unidad_medida': 'NIU',
                        'cantidad': 2,
                        'valor_unitario': 10.00,
                        'afectacion_igv': '10'
                    },
                    {
                        'codigo_producto': 'PROD002',
                        'descripcion': 'PRODUCTO DE PRUEBA 2',
                        'unidad_medida': 'NIU',
                        'cantidad': 1,
                        'valor_unitario': 25.00,
                        'afectacion_igv': '10'
                    }
                ]
            }
            
            response_data = {
                'scenario': {
                    'id': 'scenario-1',
                    'name': 'Boleta Completa',
                    'status': 'executed'
                },
                'test_data': test_data,
                'result': {
                    'success': True,
                    'message': 'Escenario de prueba preparado',
                    'note': 'Para ejecutar realmente, usar /api/generar-xml/ con estos datos'
                },
                'instructions': {
                    'next_step': 'Crear empresa de prueba y usar estos datos en /api/generar-xml/',
                    'example_curl': 'curl -X POST http://localhost:8000/api/generar-xml/ -H "Content-Type: application/json" -d \'...\''
                },
                'correlation_id': correlation_id
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"[{correlation_id}] Error en escenario 1: {e}")
            
            return Response({
                'success': False,
                'error': str(e),
                'scenario': 'scenario-1',
                'correlation_id': correlation_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name="dispatch")
class TestScenario2FacturaGravada(APIView):
    """Escenario 2: Factura gravada estándar"""
    
    def post(self, request):
        """Ejecuta escenario de factura gravada"""
        
        correlation_id = str(uuid.uuid4())
        
        try:
            logger.info(f"[{correlation_id}] Ejecutando Escenario 2: Factura Gravada")
            
            test_data = {
                'tipo_documento': '01',  # Factura
                'serie': 'F001',
                'numero': 1,
                'fecha_emision': '2025-07-15',
                'fecha_vencimiento': '2025-08-15',
                'moneda': 'PEN',
                'empresa_id': '00000000-0000-0000-0000-000000000000',  # Placeholder
                'receptor': {
                    'tipo_doc': '6',
                    'numero_doc': '20123456789',
                    'razon_social': 'EMPRESA CLIENTE SAC',
                    'direccion': 'AV. COMERCIAL 456'
                },
                'items': [
                    {
                        'codigo_producto': 'SERV001',
                        'descripcion': 'SERVICIO DE CONSULTORÍA',
                        'unidad_medida': 'ZZ',
                        'cantidad': 1,
                        'valor_unitario': 1000.00,
                        'afectacion_igv': '10'
                    }
                ]
            }
            
            response_data = {
                'scenario': {
                    'id': 'scenario-2',
                    'name': 'Factura Gravada',
                    'status': 'executed'
                },
                'test_data': test_data,
                'result': {
                    'success': True,
                    'message': 'Escenario de factura preparado',
                    'note': 'Para ejecutar realmente, usar /api/generar-xml/ con estos datos'
                },
                'instructions': {
                    'next_step': 'Crear empresa de prueba y usar estos datos en /api/generar-xml/',
                    'total_estimated': 1180.00,  # 1000 + 18% IGV
                    'igv_amount': 180.00
                },
                'correlation_id': correlation_id
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"[{correlation_id}] Error en escenario 2: {e}")
            
            return Response({
                'success': False,
                'error': str(e),
                'scenario': 'scenario-2',
                'correlation_id': correlation_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Clases stub para los otros escenarios
@method_decorator(csrf_exempt, name="dispatch")
class TestScenario3FacturaExonerada(APIView):
    def post(self, request):
        return Response({
            'success': False,
            'message': 'Escenario en desarrollo',
            'scenario': 'scenario-3-factura-exonerada',
            'status': 'not_implemented'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

@method_decorator(csrf_exempt, name="dispatch")
class TestScenario4FacturaMixta(APIView):
    def post(self, request):
        return Response({
            'success': False,
            'message': 'Escenario en desarrollo',
            'scenario': 'scenario-4-factura-mixta', 
            'status': 'not_implemented'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

@method_decorator(csrf_exempt, name="dispatch")
class TestScenario5FacturaExportacion(APIView):
    def post(self, request):
        return Response({
            'success': False,
            'message': 'Escenario en desarrollo',
            'scenario': 'scenario-5-factura-exportacion',
            'status': 'not_implemented'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)

@method_decorator(csrf_exempt, name="dispatch")
class TestAllScenariosView(APIView):
    def post(self, request):
        return Response({
            'success': False,
            'message': 'Función en desarrollo',
            'note': 'Ejecutar escenarios individualmente por ahora',
            'status': 'not_implemented'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)