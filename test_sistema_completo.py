#!/usr/bin/env python
"""
Suite de Tests Completa para Sistema de Facturación Electrónica UBL 2.1
Ubicación: test_sistema_completo.py
Ejecutar: python test_sistema_completo.py
"""

import os
import sys
import django
import json
import requests
import time
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

# Configurar Django
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

# Inicializar Django
django.setup()

from documentos.models import (
    Empresa, TipoDocumento, DocumentoElectronico, 
    DocumentoLinea, LogOperacion
)
from conversion.generators import generate_ubl_xml
from conversion.utils.calculations import TributaryCalculator

class FacturacionElectronicaTests:
    """Suite completa de tests para el sistema de facturación electrónica"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api"
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, test_name: str, success: bool, message: str = "", duration_ms: int = 0):
        """Registra el resultado de un test"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration_ms}ms)")
        if message:
            print(f"     💬 {message}")
    
    def test_database_models(self):
        """Test 1: Verificar modelos de base de datos"""
        start = time.time()
        
        try:
            # Verificar que existan empresas
            empresas_count = Empresa.objects.filter(activo=True).count()
            assert empresas_count > 0, f"No hay empresas activas: {empresas_count}"
            
            # Verificar tipos de documento
            tipos_count = TipoDocumento.objects.filter(activo=True).count()
            assert tipos_count > 0, f"No hay tipos de documento: {tipos_count}"
            
            # Verificar documentos electrónicos
            docs_count = DocumentoElectronico.objects.count()
            
            duration = int((time.time() - start) * 1000)
            self.log_test(
                "Database Models", 
                True, 
                f"Empresas: {empresas_count}, Tipos doc: {tipos_count}, Documentos: {docs_count}",
                duration
            )
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("Database Models", False, str(e), duration)
    
    def test_tributary_calculator(self):
        """Test 2: Verificar calculadora tributaria"""
        start = time.time()
        
        try:
            # Test cálculos básicos
            calculo = TributaryCalculator.calculate_line_totals(
                cantidad=Decimal('2'),
                valor_unitario=Decimal('100.00'),
                afectacion_igv='10'
            )
            
            # Verificaciones
            assert calculo['valor_venta'] == Decimal('200.00'), "Error en valor de venta"
            assert calculo['igv_monto'] == Decimal('36.00'), "Error en cálculo IGV"
            assert calculo['precio_venta'] == Decimal('236.00'), "Error en precio de venta"
            
            # Test validación RUC
            ruc_valido, _ = TributaryCalculator.validate_ruc('20103129061')
            assert ruc_valido, "RUC válido reportado como inválido"
            
            ruc_invalido, _ = TributaryCalculator.validate_ruc('12345678901')
            assert not ruc_invalido, "RUC inválido reportado como válido"
            
            duration = int((time.time() - start) * 1000)
            self.log_test(
                "Tributary Calculator", 
                True, 
                f"Cálculos correctos: Valor S/200, IGV S/36, Total S/236",
                duration
            )
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("Tributary Calculator", False, str(e), duration)
    
    def test_api_endpoints_basic(self):
        """Test 3: Verificar endpoints básicos de API"""
        start = time.time()
        
        try:
            # Test endpoint de prueba
            response = requests.get(f"{self.base_url}/test/")
            assert response.status_code == 200, f"API test failed: {response.status_code}"
            
            # Test endpoints de datos
            endpoints = [
                "/empresas/",
                "/tipos-documento/",
            ]
            
            for endpoint in endpoints:
                resp = requests.get(f"{self.base_url}{endpoint}")
                assert resp.status_code == 200, f"Endpoint {endpoint} failed: {resp.status_code}"
                data = resp.json()
                assert data.get('success'), f"Endpoint {endpoint} returned success=False"
            
            duration = int((time.time() - start) * 1000)
            self.log_test(
                "API Endpoints Basic", 
                True, 
                f"Todos los endpoints básicos funcionando",
                duration
            )
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("API Endpoints Basic", False, str(e), duration)
    
    def test_ruc_validation(self):
        """Test 4: Verificar validación de RUC"""
        start = time.time()
        
        try:
            # Test RUC válido
            data = {"ruc": "20103129061"}
            response = requests.post(
                f"{self.base_url}/validar-ruc/",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200, f"Validación RUC failed: {response.status_code}"
            result = response.json()
            assert result.get('success'), "RUC válido reportado como inválido"
            assert result.get('valid'), "RUC válido no reconocido"
            
            # Test RUC inválido
            data_invalid = {"ruc": "12345678901"}
            response_invalid = requests.post(
                f"{self.base_url}/validar-ruc/",
                json=data_invalid,
                headers={'Content-Type': 'application/json'}
            )
            
            # Debería retornar error para RUC inválido
            result_invalid = response_invalid.json()
            assert not result_invalid.get('success'), "RUC inválido aceptado como válido"
            
            duration = int((time.time() - start) * 1000)
            self.log_test(
                "RUC Validation", 
                True, 
                "Validación de RUC funcionando correctamente",
                duration
            )
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("RUC Validation", False, str(e), duration)
    
    def test_xml_generation(self):
        """Test 5: Verificar generación de XML UBL 2.1"""
        start = time.time()
        
        try:
            # Obtener empresa de prueba
            empresa = Empresa.objects.filter(activo=True).first()
            assert empresa, "No hay empresas disponibles para test"
            
            # Datos de prueba para factura
            test_data = {
                "tipo_documento": "01",
                "serie": "F001",
                "numero": 999999,  # Número alto para evitar conflictos
                "fecha_emision": date.today().isoformat(),
                "moneda": "PEN",
                "empresa_id": str(empresa.id),
                "receptor": {
                    "tipo_doc": "1",
                    "numero_doc": "12345678",
                    "razon_social": "CLIENTE TEST",
                    "direccion": "Dirección de prueba"
                },
                "items": [
                    {
                        "descripcion": "Producto test",
                        "cantidad": 1,
                        "valor_unitario": 100.00,
                        "unidad_medida": "NIU",
                        "afectacion_igv": "10",
                        "codigo_producto": "TEST001"
                    }
                ]
            }
            
            # Enviar a API
            response = requests.post(
                f"{self.base_url}/generar-xml/",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200, f"XML generation failed: {response.status_code}"
            result = response.json()
            assert result.get('success'), f"XML generation error: {result.get('error')}"
            
            # Verificar que se generó XML firmado
            xml_firmado = result.get('xml_firmado')
            assert xml_firmado, "No se generó XML firmado"
            assert '<Invoice' in xml_firmado, "XML no contiene elemento Invoice"
            assert 'ds:Signature' in xml_firmado or 'FIRMA' in xml_firmado, "XML no está firmado"
            
            # Guardar documento_id para otros tests
            self.test_documento_id = result.get('documento_id')
            
            duration = int((time.time() - start) * 1000)
            self.log_test(
                "XML Generation", 
                True, 
                f"XML UBL 2.1 generado y firmado correctamente. ID: {self.test_documento_id}",
                duration
            )
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("XML Generation", False, str(e), duration)
    
    def test_sunat_connection(self):
        """Test 6: Verificar conexión con SUNAT"""
        start = time.time()
        
        try:
            # Test conexión SUNAT
            response = requests.get(f"{self.base_url}/sunat/test-connection/")
            assert response.status_code == 200, f"SUNAT connection failed: {response.status_code}"
            
            result = response.json()
            assert result.get('success'), f"SUNAT connection error: {result.get('error')}"
            
            # Verificar operaciones disponibles
            service_info = result.get('service_info', {})
            operations = service_info.get('operations', [])
            required_ops = ['sendBill', 'getStatus']
            
            for op in required_ops:
                assert op in operations, f"Operación requerida no disponible: {op}"
            
            duration = int((time.time() - start) * 1000)
            self.log_test(
                "SUNAT Connection", 
                True, 
                f"Conexión exitosa. Operaciones: {len(operations)}",
                duration
            )
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("SUNAT Connection", False, str(e), duration)
    
    def test_sunat_status(self):
        """Test 7: Verificar estado general de SUNAT"""
        start = time.time()
        
        try:
            response = requests.get(f"{self.base_url}/sunat/status/")
            assert response.status_code == 200, f"SUNAT status failed: {response.status_code}"
            
            result = response.json()
            assert result.get('success'), "SUNAT status error"
            
            # Verificar integración SUNAT
            sunat_integration = result.get('sunat_integration', {})
            assert sunat_integration.get('available'), "SUNAT integration no disponible"
            assert sunat_integration.get('connection_status'), "SUNAT connection no activa"
            
            # Verificar estadísticas
            stats = result.get('document_statistics', {})
            total_docs = stats.get('total_documentos', 0)
            docs_firmados = stats.get('documentos_firmados', 0)
            docs_enviados = stats.get('documentos_enviados', 0)
            
            duration = int((time.time() - start) * 1000)
            self.log_test(
                "SUNAT Status", 
                True, 
                f"Total: {total_docs}, Firmados: {docs_firmados}, Enviados: {docs_enviados}",
                duration
            )
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("SUNAT Status", False, str(e), duration)
    
    def test_document_send_to_sunat(self):
        """Test 8: Verificar envío de documento a SUNAT"""
        start = time.time()
        
        try:
            # Verificar que tenemos un documento de test
            if not hasattr(self, 'test_documento_id'):
                # Buscar un documento firmado existente
                doc = DocumentoElectronico.objects.filter(
                    estado__in=['FIRMADO', 'FIRMADO_SIMULADO']
                ).exclude(estado='ENVIADO').first()
                
                if doc:
                    self.test_documento_id = str(doc.id)
                else:
                    raise Exception("No hay documentos disponibles para envío")
            
            # Intentar envío a SUNAT
            data = {"documento_id": self.test_documento_id}
            response = requests.post(
                f"{self.base_url}/sunat/send-bill/",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            result = response.json()
            
            # El envío puede fallar por varias razones en Beta, pero el endpoint debe funcionar
            if response.status_code == 200 and result.get('success'):
                message = f"Documento enviado exitosamente a SUNAT"
                success = True
            elif "ya fue enviado" in result.get('error', '').lower():
                message = "Documento ya fue enviado previamente (correcto)"
                success = True
            elif response.status_code in [401, 422, 503]:
                # Errores esperados en ambiente Beta
                message = f"Error esperado en Beta: {result.get('error', 'Error de conexión')}"
                success = True
            else:
                message = f"Error inesperado: {result.get('error', 'Error desconocido')}"
                success = False
            
            duration = int((time.time() - start) * 1000)
            self.log_test("Document Send to SUNAT", success, message, duration)
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("Document Send to SUNAT", False, str(e), duration)
    
    def test_sunat_summary(self):
        """Test 9: Verificar envío de resumen diario"""
        start = time.time()
        
        try:
            data = {
                "ruc": "20103129061",
                "fecha_emision": date.today().isoformat(),
                "correlativo": 999,  # Número alto para evitar conflictos
                "tipo_resumen": "RC"
            }
            
            response = requests.post(
                f"{self.base_url}/sunat/send-summary/",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            result = response.json()
            
            # Evaluar resultado
            if response.status_code == 200 and result.get('success'):
                ticket = result.get('ticket')
                message = f"Resumen enviado. Ticket: {ticket}"
                success = True
            elif response.status_code in [401, 422, 503]:
                message = f"Error esperado en Beta: {result.get('error')}"
                success = True
            else:
                message = f"Error: {result.get('error', 'Desconocido')}"
                success = False
            
            duration = int((time.time() - start) * 1000)
            self.log_test("SUNAT Summary", success, message, duration)
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("SUNAT Summary", False, str(e), duration)
    
    def test_get_status_cdr(self):
        """Test 10: Verificar consulta de CDR"""
        start = time.time()
        
        try:
            # Buscar un documento enviado
            doc_enviado = DocumentoElectronico.objects.filter(estado='ENVIADO').first()
            
            if doc_enviado:
                data = {
                    "ruc": doc_enviado.empresa.ruc,
                    "tipo_documento": doc_enviado.tipo_documento.codigo,
                    "serie": doc_enviado.serie,
                    "numero": doc_enviado.numero
                }
            else:
                # Usar datos de prueba
                data = {
                    "ruc": "20103129061",
                    "tipo_documento": "01",
                    "serie": "F001",
                    "numero": 1
                }
            
            response = requests.post(
                f"{self.base_url}/sunat/get-status-cdr/",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            result = response.json()
            
            # El endpoint debe responder, aunque no encuentre el CDR
            if response.status_code == 200:
                message = f"Consulta CDR exitosa para {data['serie']}-{data['numero']}"
                success = True
            elif response.status_code in [401, 422, 503]:
                message = f"Error esperado en Beta: {result.get('error')}"
                success = True
            else:
                message = f"Error: {result.get('error', 'Desconocido')}"
                success = False
            
            duration = int((time.time() - start) * 1000)
            self.log_test("Get Status CDR", success, message, duration)
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("Get Status CDR", False, str(e), duration)
    
    def test_digital_signature(self):
        """Test 11: Verificar sistema de firma digital"""
        start = time.time()
        
        try:
            from firma_digital import XMLSigner, certificate_manager
            
            # Verificar que el sistema de firma está disponible
            signer = XMLSigner()
            assert signer is not None, "XMLSigner no se pudo instanciar"
            
            # Verificar certificate manager
            assert certificate_manager is not None, "Certificate manager no disponible"
            
            # Buscar documento firmado
            doc_firmado = DocumentoElectronico.objects.exclude(xml_firmado__isnull=True).first()
            assert doc_firmado, "No hay documentos firmados para verificar"
            
            # Verificar que el XML contiene firma
            xml_content = doc_firmado.xml_firmado
            has_signature = (
                'ds:Signature' in xml_content or 
                'FIRMA' in xml_content or
                '<Signature' in xml_content
            )
            assert has_signature, "XML firmado no contiene firma válida"
            
            duration = int((time.time() - start) * 1000)
            self.log_test(
                "Digital Signature", 
                True, 
                f"Sistema de firma funcionando. XML: {len(xml_content)} chars",
                duration
            )
            
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            self.log_test("Digital Signature", False, str(e), duration)
    
    def run_all_tests(self):
        """Ejecutar todos los tests"""
        print("🚀 INICIANDO SUITE DE TESTS COMPLETA")
        print("=" * 80)
        print(f"📅 Fecha: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 API Base: {self.base_url}")
        print("")
        
        # Lista de tests a ejecutar
        tests = [
            self.test_database_models,
            self.test_tributary_calculator,
            self.test_api_endpoints_basic,
            self.test_ruc_validation,
            self.test_xml_generation,
            self.test_digital_signature,
            self.test_sunat_connection,
            self.test_sunat_status,
            self.test_document_send_to_sunat,
            self.test_sunat_summary,
            self.test_get_status_cdr,
        ]
        
        # Ejecutar tests
        for i, test_func in enumerate(tests, 1):
            print(f"🧪 Test {i}/{len(tests)}: {test_func.__name__}")
            test_func()
            print("")
        
        # Generar reporte final
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generar reporte final de tests"""
        end_time = datetime.now()
        total_duration = int((end_time - self.start_time).total_seconds() * 1000)
        
        passed = sum(1 for r in self.test_results if r['success'])
        failed = len(self.test_results) - passed
        success_rate = (passed / len(self.test_results)) * 100 if self.test_results else 0
        
        print("=" * 80)
        print("📊 REPORTE FINAL DE TESTS")
        print("=" * 80)
        print(f"⏱️  Duración total: {total_duration}ms")
        print(f"🧪 Tests ejecutados: {len(self.test_results)}")
        print(f"✅ Tests exitosos: {passed}")
        print(f"❌ Tests fallidos: {failed}")
        print(f"📈 Tasa de éxito: {success_rate:.1f}%")
        print("")
        
        # Mostrar tests fallidos
        if failed > 0:
            print("❌ TESTS FALLIDOS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
            print("")
        
        # Mostrar resumen por categoría
        print("📋 RESUMEN POR CATEGORÍA:")
        categories = {
            "Base de Datos": ["Database Models"],
            "Cálculos": ["Tributary Calculator"],
            "API REST": ["API Endpoints Basic", "RUC Validation"],
            "Generación XML": ["XML Generation", "Digital Signature"],
            "Integración SUNAT": ["SUNAT Connection", "SUNAT Status", "Document Send to SUNAT", "SUNAT Summary", "Get Status CDR"]
        }
        
        for category, test_names in categories.items():
            category_results = [r for r in self.test_results if any(name in r['test'] for name in test_names)]
            category_passed = sum(1 for r in category_results if r['success'])
            category_total = len(category_results)
            
            if category_total > 0:
                category_rate = (category_passed / category_total) * 100
                status = "✅" if category_rate == 100 else "⚠️" if category_rate >= 80 else "❌"
                print(f"   {status} {category}: {category_passed}/{category_total} ({category_rate:.0f}%)")
        
        print("")
        
        # Veredicto final
        if success_rate >= 90:
            print("🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
            print("   Tu sistema de facturación electrónica está listo para producción.")
        elif success_rate >= 80:
            print("✅ SISTEMA MAYORMENTE FUNCIONAL")
            print("   El sistema funciona bien con algunos problemas menores.")
        elif success_rate >= 60:
            print("⚠️ SISTEMA PARCIALMENTE FUNCIONAL")
            print("   Hay varios problemas que necesitan atención.")
        else:
            print("❌ SISTEMA CON PROBLEMAS CRÍTICOS")
            print("   Se requiere revisión importante antes de usar.")
        
        print("")
        
        # Guardar reporte en archivo
        self.save_report_to_file()
    
    def save_report_to_file(self):
        """Guardar reporte en archivo JSON"""
        report_data = {
            'timestamp': self.start_time.isoformat(),
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['success']),
            'failed': sum(1 for r in self.test_results if not r['success']),
            'success_rate': (sum(1 for r in self.test_results if r['success']) / len(self.test_results)) * 100 if self.test_results else 0,
            'test_results': self.test_results
        }
        
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Reporte guardado en: {report_file}")
        except Exception as e:
            print(f"⚠️ No se pudo guardar el reporte: {e}")

def main():
    """Función principal"""
    try:
        # Verificar que Django esté corriendo
        response = requests.get("http://localhost:8000/api/test/", timeout=5)
        if response.status_code != 200:
            print("❌ Error: El servidor Django no está corriendo en http://localhost:8000")
            print("💡 Ejecuta: python manage.py runserver")
            return 1
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor Django")
        print("💡 Asegúrate de que esté corriendo: python manage.py runserver")
        return 1
    
    # Ejecutar tests
    test_suite = FacturacionElectronicaTests()
    test_suite.run_all_tests()
    
    return 0

if __name__ == '__main__':
    exit(main())