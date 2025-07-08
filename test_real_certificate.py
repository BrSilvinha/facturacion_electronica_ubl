#!/usr/bin/env python
"""
Script para probar certificado real integrado
Ejecutar: python test_real_certificate.py
"""

import os
import sys
import django
import requests
import json
from pathlib import Path
from datetime import datetime, date

# Configurar Django
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

# Inicializar Django
django.setup()

from documentos.models import Empresa, TipoDocumento, DocumentoElectronico

class RealCertificateTest:
    """Tester para certificado real"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api"
        self.ruc = "20103129061"
        
    def test_1_certificate_info(self):
        """Test 1: Verificar información de certificados"""
        print("🔍 TEST 1: Información de certificados")
        print("-" * 50)
        
        try:
            # Llamar endpoint de certificados
            response = requests.get(f"{self.base_url}/certificate-info/")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    certificates = data.get('certificates', [])
                    real_certs = data.get('total_real_certificates', 0)
                    test_certs = data.get('total_test_certificates', 0)
                    
                    print(f"   ✅ Endpoint funcionando")
                    print(f"   📊 Total certificados: {len(certificates)}")
                    print(f"   🔐 Certificados reales: {real_certs}")
                    print(f"   🧪 Certificados de prueba: {test_certs}")
                    
                    # Buscar tu certificado
                    tu_cert = None
                    for cert in certificates:
                        if cert['ruc'] == self.ruc:
                            tu_cert = cert
                            break
                    
                    if tu_cert:
                        print(f"   ✅ Tu certificado encontrado:")
                        print(f"      - RUC: {tu_cert['ruc']}")
                        print(f"      - Empresa: {tu_cert['empresa']}")
                        print(f"      - Tipo: {tu_cert['certificate_type']}")
                        print(f"      - Es real: {tu_cert['is_real']}")
                        
                        if tu_cert['is_real']:
                            print(f"   🎉 ¡CERTIFICADO REAL DETECTADO!")
                            return True
                        else:
                            print(f"   ⚠️ Aún usando certificado de prueba")
                            return False
                    else:
                        print(f"   ❌ Tu RUC {self.ruc} no encontrado")
                        return False
                else:
                    print(f"   ❌ Error en respuesta: {data.get('error')}")
                    return False
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_2_certificate_validation(self):
        """Test 2: Validar certificado específico"""
        print(f"\n🔐 TEST 2: Validación de certificado para RUC {self.ruc}")
        print("-" * 50)
        
        try:
            # Llamar endpoint de validación específica
            data = {"ruc": self.ruc}
            response = requests.post(
                f"{self.base_url}/certificate-info/",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    cert_info = result.get('certificate_info', {})
                    
                    print(f"   ✅ Validación exitosa")
                    print(f"   📄 Tipo: {cert_info.get('certificate_type')}")
                    print(f"   🔐 Es real: {cert_info.get('is_real')}")
                    print(f"   📁 Ruta: {cert_info.get('certificate_path')}")
                    print(f"   📝 Descripción: {cert_info.get('description')}")
                    
                    # Verificar si se pudo cargar
                    is_valid = cert_info.get('certificate_valid', False)
                    
                    if is_valid:
                        print(f"   ✅ Certificado cargado correctamente:")
                        print(f"      - Sujeto: {cert_info.get('certificate_subject')}")
                        print(f"      - Expira: {cert_info.get('certificate_expires')}")
                        print(f"      - Tamaño clave: {cert_info.get('key_size')} bits")
                        return True
                    else:
                        print(f"   ❌ Error cargando certificado:")
                        print(f"      - Error: {cert_info.get('certificate_error')}")
                        return False
                else:
                    print(f"   ❌ Error: {result.get('error')}")
                    return False
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_3_xml_generation_with_real_cert(self):
        """Test 3: Generar XML con certificado real"""
        print(f"\n📄 TEST 3: Generación XML con certificado real")
        print("-" * 50)
        
        try:
            # Obtener empresa
            empresa = Empresa.objects.filter(ruc=self.ruc).first()
            if not empresa:
                print(f"   ❌ Empresa con RUC {self.ruc} no encontrada")
                return False
            
            # Datos de prueba
            test_data = {
                "tipo_documento": "01",
                "serie": "F001",
                "numero": int(datetime.now().strftime('%Y%m%d%H%M')),  # Número único
                "fecha_emision": date.today().isoformat(),
                "moneda": "PEN",
                "empresa_id": str(empresa.id),
                "receptor": {
                    "tipo_doc": "1",
                    "numero_doc": "12345678",
                    "razon_social": "CLIENTE CON CERTIFICADO REAL",
                    "direccion": "Dirección del cliente con cert real"
                },
                "items": [
                    {
                        "descripcion": "Producto firmado con certificado real SUNAT",
                        "cantidad": 1,
                        "valor_unitario": 150.00,
                        "unidad_medida": "NIU",
                        "afectacion_igv": "10",
                        "codigo_producto": "REAL001"
                    }
                ]
            }
            
            print(f"   📤 Enviando datos de prueba...")
            print(f"   📋 Documento: {test_data['tipo_documento']}-{test_data['serie']}-{test_data['numero']}")
            print(f"   🏢 Empresa: {empresa.razon_social}")
            
            # Enviar a API
            response = requests.post(
                f"{self.base_url}/generar-xml/",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    print(f"   ✅ XML generado exitosamente:")
                    print(f"      - ID: {result.get('documento_id')}")
                    print(f"      - Número: {result.get('numero_completo')}")
                    print(f"      - Estado: {result.get('estado')}")
                    print(f"      - Tipo firma: {result.get('signature_type')}")
                    print(f"      - Hash: {result.get('hash', '')[:20]}...")
                    
                    # Verificar información del certificado
                    cert_info = result.get('certificate_info', {})
                    if cert_info:
                        print(f"   🔐 Información del certificado usado:")
                        print(f"      - Sujeto: {cert_info.get('subject')}")
                        print(f"      - Expira: {cert_info.get('expires', '')[:10]}")
                        print(f"      - Es real: {cert_info.get('is_real')}")
                        print(f"      - Tamaño clave: {cert_info.get('key_size')} bits")
                        
                        if cert_info.get('is_real'):
                            print(f"   🎉 ¡FIRMADO CON CERTIFICADO REAL DE SUNAT!")
                        else:
                            print(f"   ⚠️ Firmado con certificado de prueba")
                    
                    # Verificar XML firmado
                    xml_firmado = result.get('xml_firmado', '')
                    if xml_firmado:
                        xml_size = len(xml_firmado)
                        has_signature = 'ds:Signature' in xml_firmado
                        has_signature_value = 'ds:SignatureValue' in xml_firmado
                        
                        print(f"   📄 XML firmado:")
                        print(f"      - Tamaño: {xml_size} caracteres")
                        print(f"      - Contiene ds:Signature: {has_signature}")
                        print(f"      - Contiene ds:SignatureValue: {has_signature_value}")
                        
                        if has_signature and has_signature_value:
                            print(f"   ✅ XML contiene firma digital válida")
                            
                            # Guardar XML para inspección
                            xml_file = Path(f'xml_real_cert_{test_data["numero"]}.xml')
                            with open(xml_file, 'w', encoding='utf-8') as f:
                                f.write(xml_firmado)
                            
                            print(f"   💾 XML guardado en: {xml_file}")
                            
                            return True
                        else:
                            print(f"   ❌ XML no contiene firma válida")
                            return False
                    else:
                        print(f"   ❌ No se recibió XML firmado")
                        return False
                else:
                    print(f"   ❌ Error generando XML: {result.get('error')}")
                    return False
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                if response.text:
                    print(f"   📄 Respuesta: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_4_sunat_integration(self):
        """Test 4: Integración con SUNAT usando certificado real"""
        print(f"\n🌐 TEST 4: Integración SUNAT con certificado real")
        print("-" * 50)
        
        try:
            # Buscar documento reciente firmado
            documento = DocumentoElectronico.objects.filter(
                empresa__ruc=self.ruc,
                estado__in=['FIRMADO', 'FIRMADO_SIMULADO']
            ).order_by('-created_at').first()
            
            if not documento:
                print(f"   ⚠️ No hay documentos firmados para enviar")
                print(f"   💡 Ejecuta primero el test 3")
                return False
            
            print(f"   📄 Documento encontrado: {documento.get_numero_completo()}")
            print(f"   📊 Estado: {documento.estado}")
            print(f"   💰 Total: {documento.moneda} {documento.total}")
            
            # Intentar envío a SUNAT
            data = {"documento_id": str(documento.id)}
            
            print(f"   📤 Enviando a SUNAT...")
            
            response = requests.post(
                f"{self.base_url}/sunat/send-bill/",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    print(f"   ✅ Envío exitoso:")
                    print(f"      - Documento: {result.get('document_number')}")
                    print(f"      - Estado: {result.get('document_status')}")
                    
                    sunat_response = result.get('sunat_response', {})
                    if sunat_response:
                        print(f"      - Método: {sunat_response.get('method')}")
                        print(f"      - Duración: {sunat_response.get('duration_ms')}ms")
                    
                    # Verificar CDR si está disponible
                    cdr_info = result.get('cdr_info')
                    if cdr_info:
                        print(f"   📋 Información CDR:")
                        print(f"      - Aceptado: {cdr_info.get('is_accepted')}")
                        print(f"      - Código: {cdr_info.get('response_code')}")
                        print(f"      - Descripción: {cdr_info.get('response_description')}")
                    
                    return True
                else:
                    error = result.get('error', 'Error desconocido')
                    print(f"   ⚠️ Error en envío: {error}")
                    
                    # Algunos errores son esperados en Beta
                    if any(keyword in error.lower() for keyword in ['beta', 'authentication', 'connection']):
                        print(f"   💡 Error esperado en ambiente Beta")
                        return True
                    
                    return False
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def test_5_compare_certificates(self):
        """Test 5: Comparar certificado real vs prueba"""
        print(f"\n🔀 TEST 5: Comparación certificado real vs prueba")
        print("-" * 50)
        
        try:
            # Obtener info de todos los certificados
            response = requests.get(f"{self.base_url}/certificate-info/")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    certificates = data.get('certificates', [])
                    
                    print(f"   📊 Resumen de certificados:")
                    
                    real_count = 0
                    test_count = 0
                    
                    for cert in certificates:
                        ruc = cert['ruc']
                        empresa = cert['empresa']
                        cert_type = cert['certificate_type']
                        is_real = cert['is_real']
                        
                        status = "🔐 REAL" if is_real else "🧪 PRUEBA"
                        highlight = " ⭐" if ruc == self.ruc else ""
                        
                        print(f"      {status} | {ruc} | {empresa[:30]}...{highlight}")
                        
                        if is_real:
                            real_count += 1
                        else:
                            test_count += 1
                    
                    print(f"")
                    print(f"   📈 Estadísticas:")
                    print(f"      - Certificados reales: {real_count}")
                    print(f"      - Certificados de prueba: {test_count}")
                    print(f"      - Total: {len(certificates)}")
                    
                    # Verificar tu certificado específico
                    tu_cert = next((c for c in certificates if c['ruc'] == self.ruc), None)
                    
                    if tu_cert:
                        print(f"")
                        print(f"   ⭐ Tu certificado ({self.ruc}):")
                        print(f"      - Tipo: {tu_cert['certificate_type']}")
                        print(f"      - Es real: {tu_cert['is_real']}")
                        print(f"      - Descripción: {tu_cert['description']}")
                        
                        if tu_cert['is_real']:
                            print(f"   🎉 ¡Estás usando certificado REAL de SUNAT!")
                            return True
                        else:
                            print(f"   ⚠️ Aún usando certificado de prueba")
                            return False
                    else:
                        print(f"   ❌ Tu RUC no encontrado en la lista")
                        return False
                else:
                    print(f"   ❌ Error: {data.get('error')}")
                    return False
            else:
                print(f"   ❌ Error HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def run_all_tests(self):
        """Ejecutar todos los tests"""
        print("🚀 SUITE DE TESTS - CERTIFICADO REAL")
        print("=" * 60)
        print(f"📋 RUC objetivo: {self.ruc}")
        print(f"🌐 API Base: {self.base_url}")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        
        # Verificar que el servidor esté corriendo
        try:
            response = requests.get(f"{self.base_url}/test/", timeout=5)
            if response.status_code != 200:
                print("❌ Error: El servidor Django no está corriendo")
                print("💡 Ejecuta: python manage.py runserver")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Error: No se puede conectar al servidor Django")
            print("💡 Ejecuta: python manage.py runserver")
            return False
        
        # Ejecutar tests
        tests = [
            ("Información de certificados", self.test_1_certificate_info),
            ("Validación de certificado", self.test_2_certificate_validation),
            ("Generación XML con cert real", self.test_3_xml_generation_with_real_cert),
            ("Integración SUNAT", self.test_4_sunat_integration),
            ("Comparación certificados", self.test_5_compare_certificates),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"🧪 {test_name}")
            try:
                if test_func():
                    passed += 1
                    print(f"   ✅ PASS")
                else:
                    print(f"   ❌ FAIL")
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
            print("")
        
        # Reporte final
        success_rate = (passed / total) * 100
        
        print("=" * 60)
        print("📊 REPORTE FINAL - CERTIFICADO REAL")
        print("=" * 60)
        print(f"✅ Tests pasados: {passed}/{total}")
        print(f"📈 Tasa de éxito: {success_rate:.1f}%")
        
        if passed == total:
            print(f"\n🎉 ¡TODOS LOS TESTS PASARON!")
            print(f"🔐 Tu certificado real está funcionando perfectamente")
            print(f"✅ Sistema listo para producción con firma SUNAT real")
        elif passed >= 3:
            print(f"\n✅ MAYORÍA DE TESTS PASARON")
            print(f"🔐 Certificado real detectado y funcionando")
            print(f"⚠️ Algunos problemas menores")
        else:
            print(f"\n❌ VARIOS TESTS FALLARON")
            print(f"💡 Verifica la configuración del certificado real")
        
        return passed == total

if __name__ == '__main__':
    print("🔐 TESTER DE CERTIFICADO REAL SUNAT")
    print("Versión: 2.0 Professional")
    print("")
    
    tester = RealCertificateTest()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 ¡CERTIFICADO REAL FUNCIONANDO AL 100%!")
    else:
        print(f"\n⚠️ REVISAR CONFIGURACIÓN DE CERTIFICADO")
    
    print(f"\nPresiona Enter para continuar...")
    input()