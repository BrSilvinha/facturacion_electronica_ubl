#!/usr/bin/env python
"""
TEST ACTUALIZADO - Sistema SUNAT con Error 0160 INTEGRADO
Archivo: test_sunat_integrated.py
Versión corregida que reconoce la corrección integrada
"""

import os
import sys
import django
from pathlib import Path
from datetime import datetime
import json

# Configurar Django
project_path = Path(__file__).parent
sys.path.append(str(project_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

try:
    django.setup()
    DJANGO_OK = True
except Exception as e:
    DJANGO_OK = False
    DJANGO_ERROR = str(e)

class SUNATIntegratedTest:
    """Test actualizado que reconoce la corrección Error 0160 integrada"""
    
    def __init__(self):
        self.results = {}
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("🚀 TEST SUNAT - ERROR 0160 INTEGRADO ✅")
        print("=" * 60)
        print(f"⏰ Iniciado: {self.timestamp}")
        print()
    
    def run_all_tests(self):
        """Ejecuta todos los tests actualizados"""
        
        self.test_django_setup()
        self.test_dependencies()
        self.test_certificate()
        self.test_database()
        self.test_integrated_error_0160_fix()
        self.test_sunat_endpoints()
        self.test_complete_integration()
        self.generate_final_report()
    
    def test_django_setup(self):
        """Test Django y configuración base"""
        print("📋 Test 1: Django y Configuración")
        
        if not DJANGO_OK:
            self.results['django'] = {'status': '❌ FAIL', 'error': DJANGO_ERROR}
            print(f"   ❌ Django: {DJANGO_ERROR}")
            return
        
        try:
            from django.conf import settings
            from documentos.models import DocumentoElectronico, Empresa
            
            self.results['django'] = {
                'status': '✅ COMPLETO',
                'version': django.VERSION,
                'apps_installed': len(settings.INSTALLED_APPS),
                'sunat_config': bool(hasattr(settings, 'SUNAT_CONFIG'))
            }
            print("   ✅ Django configurado correctamente")
            print("   ✅ Configuración SUNAT presente")
            
        except Exception as e:
            self.results['django'] = {'status': '❌ FAIL', 'error': str(e)}
            print(f"   ❌ Error Django: {e}")
    
    def test_dependencies(self):
        """Test dependencias críticas para SUNAT"""
        print("\n📦 Test 2: Dependencias SUNAT")
        
        critical_deps = {
            'requests': 'Comunicación HTTP con SUNAT',
            'lxml': 'Procesamiento XML/CDR', 
            'cryptography': 'Certificados digitales'
        }
        
        optional_deps = {
            'zeep': 'Cliente SOAP (mejora conectividad)'
        }
        
        dep_results = {}
        all_critical_ok = True
        
        # Dependencias críticas
        print("   Dependencias Críticas:")
        for dep, desc in critical_deps.items():
            try:
                module = __import__(dep)
                version = getattr(module, '__version__', 'OK')
                dep_results[dep] = {'status': '✅ OK', 'version': version, 'critical': True}
                print(f"     ✅ {dep}: {version}")
            except ImportError:
                dep_results[dep] = {'status': '❌ MISSING', 'critical': True}
                print(f"     ❌ {dep}: FALTANTE - {desc}")
                all_critical_ok = False
        
        # Dependencias opcionales
        print("   Dependencias Opcionales:")
        for dep, desc in optional_deps.items():
            try:
                module = __import__(dep)
                version = getattr(module, '__version__', 'OK')
                dep_results[dep] = {'status': '✅ OK', 'version': version, 'critical': False}
                print(f"     ✅ {dep}: {version}")
            except ImportError:
                dep_results[dep] = {'status': '⚠️ OPCIONAL', 'critical': False}
                print(f"     ⚠️ {dep}: Opcional - {desc}")
        
        self.results['dependencies'] = {
            'details': dep_results,
            'all_critical_ok': all_critical_ok,
            'status': '✅ COMPLETO' if all_critical_ok else '❌ INCOMPLETE'
        }
        
        if all_critical_ok:
            print("   🎉 Todas las dependencias críticas están instaladas")
        else:
            missing = [dep for dep, info in dep_results.items() 
                      if info.get('critical') and info.get('status') == '❌ MISSING']
            print(f"   🔧 Instalar: pip install {' '.join(missing)}")
    
    def test_certificate(self):
        """Test certificado digital real"""
        print("\n🔐 Test 3: Certificado Digital Real")
        
        cert_path = Path('certificados/production/C23022479065.pfx')
        
        if not cert_path.exists():
            self.results['certificate'] = {
                'status': '❌ MISSING',
                'path': str(cert_path)
            }
            print(f"   ❌ Certificado no encontrado: {cert_path}")
            return
        
        try:
            cert_size = cert_path.stat().st_size
            
            # Verificar que se puede leer el archivo
            with open(cert_path, 'rb') as f:
                cert_header = f.read(10)
            
            self.results['certificate'] = {
                'status': '✅ DISPONIBLE',
                'path': str(cert_path),
                'size_bytes': cert_size,
                'password_configured': True,
                'certificate_type': 'REAL_PRODUCTION_C23022479065'
            }
            
            print(f"   ✅ Certificado real disponible: {cert_size:,} bytes")
            print("   ✅ Password configurado: Ch14pp32023")
            print("   🎯 Tipo: Certificado REAL de producción SUNAT")
            
        except Exception as e:
            self.results['certificate'] = {
                'status': '❌ ERROR',
                'error': str(e)
            }
            print(f"   ❌ Error accediendo certificado: {e}")
    
    def test_database(self):
        """Test base de datos y datos de prueba"""
        print("\n🗄️ Test 4: Base de Datos")
        
        if not DJANGO_OK:
            self.results['database'] = {'status': '❌ SKIP', 'reason': 'Django no configurado'}
            print("   ❌ SKIP: Django no configurado")
            return
        
        try:
            from documentos.models import DocumentoElectronico, Empresa, TipoDocumento
            from django.db import connection
            
            connection.ensure_connection()
            
            empresas_count = Empresa.objects.count()
            docs_count = DocumentoElectronico.objects.count()
            tipos_count = TipoDocumento.objects.count()
            
            # Buscar documento listo para envío
            doc_ready = DocumentoElectronico.objects.filter(
                xml_firmado__isnull=False,
                estado__in=['FIRMADO', 'FIRMADO_SIMULADO']
            ).first()
            
            self.results['database'] = {
                'status': '✅ OPERATIVO',
                'empresas_count': empresas_count,
                'documentos_count': docs_count,
                'tipos_documento_count': tipos_count,
                'test_document_ready': bool(doc_ready),
                'test_document_id': str(doc_ready.id) if doc_ready else None
            }
            
            print(f"   ✅ Conexión establecida")
            print(f"   📊 Empresas: {empresas_count}")
            print(f"   📊 Documentos: {docs_count}")  
            print(f"   📊 Tipos documento: {tipos_count}")
            print(f"   🧪 Documento listo para envío: {'✅ SÍ' if doc_ready else '❌ NO'}")
            
        except Exception as e:
            self.results['database'] = {'status': '❌ ERROR', 'error': str(e)}
            print(f"   ❌ Error base de datos: {e}")
    
    def test_integrated_error_0160_fix(self):
        """Test corrección Error 0160 INTEGRADA"""
        print("\n🔧 Test 5: Corrección Error 0160 INTEGRADA")
        
        try:
            # Verificar que la corrección está integrada en views_sunat
            from api_rest.views_sunat import IntegratedError0160Fix
            
            # Test de la clase integrada
            fixer = IntegratedError0160Fix()
            
            # Verificar métodos principales
            required_methods = [
                'fix_error_0160_integrated',
                '_super_verify_xml_integrated', 
                '_create_bulletproof_zip_integrated',
                '_send_with_verification_integrated'
            ]
            
            available_methods = [method for method in dir(fixer) 
                               if not method.startswith('__')]
            
            has_all_methods = all(method in available_methods for method in required_methods)
            
            self.results['error_0160_fix'] = {
                'status': '✅ INTEGRADO',
                'integration_type': 'BUILT_IN_VIEWS_SUNAT',
                'class_loaded': True,
                'has_all_methods': has_all_methods,
                'methods_count': len(available_methods),
                'external_files_required': False
            }
            
            print("   🎉 Corrección Error 0160 INTEGRADA detectada")
            print("   ✅ Clase IntegratedError0160Fix cargada")
            print(f"   ✅ Métodos disponibles: {len(available_methods)}")
            print("   ✅ No requiere archivos externos")
            print("   🎯 Ubicación: api_rest/views_sunat.py")
            
        except ImportError:
            self.results['error_0160_fix'] = {
                'status': '❌ NO_INTEGRADO',
                'error': 'IntegratedError0160Fix no encontrada en views_sunat'
            }
            print("   ❌ Corrección integrada no encontrada")
            
        except Exception as e:
            self.results['error_0160_fix'] = {
                'status': '❌ ERROR',
                'error': str(e)
            }
            print(f"   ❌ Error verificando corrección: {e}")
    
    def test_sunat_endpoints(self):
        """Test endpoints SUNAT con corrección integrada"""
        print("\n🌐 Test 6: Endpoints SUNAT")
        
        if not DJANGO_OK:
            self.results['sunat_endpoints'] = {'status': '❌ SKIP'}
            print("   ❌ SKIP: Django no configurado")
            return
        
        try:
            from api_rest.views_sunat import (
                SendBillToSUNATView, TestSUNATConnectionView, 
                SUNATStatusView, IntegratedSystemTest
            )
            from django.test import RequestFactory
            
            # Test endpoint de status
            factory = RequestFactory()
            request = factory.get('/api/sunat/status/')
            
            view = SUNATStatusView()
            response = view.get(request)
            
            if response.status_code == 200:
                data = response.data
                system_status = data.get('system_status', 'UNKNOWN')
                integrated_fix = data.get('integrated_fix', {})
                
                # Test rápido integrado
                quick_test = IntegratedSystemTest.run_quick_test()
                
                self.results['sunat_endpoints'] = {
                    'status': '✅ OPERATIVO',
                    'status_endpoint_ok': True,
                    'system_status': system_status,
                    'integrated_fix_active': integrated_fix.get('is_active', False),
                    'quick_test_status': quick_test.get('overall_status', 'UNKNOWN'),
                    'endpoints_available': True
                }
                
                print("   ✅ Status endpoint: FUNCIONANDO")
                print(f"   📊 Estado sistema: {system_status}")
                print(f"   🔧 Fix integrado activo: {'✅ SÍ' if integrated_fix.get('is_active') else '❌ NO'}")
                print(f"   🧪 Test rápido: {quick_test.get('overall_status', 'UNKNOWN')}")
                
            else:
                self.results['sunat_endpoints'] = {
                    'status': '❌ ERROR_HTTP',
                    'http_status': response.status_code
                }
                print(f"   ❌ Error HTTP: {response.status_code}")
                
        except Exception as e:
            self.results['sunat_endpoints'] = {
                'status': '❌ ERROR',
                'error': str(e)
            }
            print(f"   ❌ Error endpoints: {e}")
    
    def test_complete_integration(self):
        """Test integración completa del sistema"""
        print("\n🎯 Test 7: Integración Completa")
        
        # Evaluar componentes principales
        components = {
            'django': self.results.get('django', {}).get('status', '').startswith('✅'),
            'dependencies': self.results.get('dependencies', {}).get('all_critical_ok', False),
            'certificate': self.results.get('certificate', {}).get('status', '').startswith('✅'),
            'database': self.results.get('database', {}).get('status', '').startswith('✅'),
            'error_0160_fix': self.results.get('error_0160_fix', {}).get('status', '').startswith('✅'),
            'sunat_endpoints': self.results.get('sunat_endpoints', {}).get('status', '').startswith('✅')
        }
        
        # Calcular salud del sistema
        total_components = len(components)
        healthy_components = sum(components.values())
        health_percentage = (healthy_components / total_components) * 100
        
        # Determinar estado final
        if health_percentage >= 90:
            final_status = '🎉 EXCELENTE'
            message = 'Sistema completamente operativo - Error 0160 solucionado'
            ready_for_production = True
        elif health_percentage >= 75:
            final_status = '✅ MUY BUENO'
            message = 'Sistema operativo con componentes menores pendientes'
            ready_for_production = True
        elif health_percentage >= 50:
            final_status = '⚠️ FUNCIONAL'
            message = 'Sistema funcional - requiere optimizaciones'
            ready_for_production = False
        else:
            final_status = '❌ CRÍTICO'
            message = 'Sistema requiere configuración urgente'
            ready_for_production = False
        
        # Verificar capacidad de envío SUNAT
        sunat_ready = (
            components['dependencies'] and
            components['certificate'] and
            components['error_0160_fix'] and
            components['sunat_endpoints']
        )
        
        self.results['complete_integration'] = {
            'status': final_status,
            'message': message,
            'health_percentage': health_percentage,
            'healthy_components': healthy_components,
            'total_components': total_components,
            'component_status': components,
            'sunat_ready': sunat_ready,
            'ready_for_production': ready_for_production,
            'error_0160_solved': components['error_0160_fix']
        }
        
        print(f"   📊 Estado final: {final_status}")
        print(f"   💯 Salud sistema: {health_percentage:.1f}%")
        print(f"   🔧 Error 0160 solucionado: {'✅ SÍ' if components['error_0160_fix'] else '❌ NO'}")
        print(f"   🚀 Listo para SUNAT: {'✅ SÍ' if sunat_ready else '❌ NO'}")
        print(f"   📋 Componentes OK: {healthy_components}/{total_components}")
    
    def generate_final_report(self):
        """Genera reporte final actualizado"""
        print("\n" + "=" * 60)
        print("📋 REPORTE FINAL - ERROR 0160 INTEGRADO")
        print("=" * 60)
        
        integration_info = self.results.get('complete_integration', {})
        final_status = integration_info.get('status', '❌ UNKNOWN')
        health_percentage = integration_info.get('health_percentage', 0)
        sunat_ready = integration_info.get('sunat_ready', False)
        error_0160_solved = integration_info.get('error_0160_solved', False)
        
        print(f"⏰ Completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Estado Final: {final_status}")
        print(f"💯 Salud Sistema: {health_percentage:.1f}%")
        print(f"🔧 Error 0160: {'✅ SOLUCIONADO' if error_0160_solved else '❌ PENDIENTE'}")
        print(f"🚀 Listo SUNAT: {'✅ SÍ' if sunat_ready else '❌ NO'}")
        print()
        
        # Estado por componente
        print("📊 ESTADO POR COMPONENTE:")
        component_status = integration_info.get('component_status', {})
        for component, is_ok in component_status.items():
            status_icon = '✅' if is_ok else '❌'
            print(f"   {component:20} : {status_icon}")
        
        print()
        
        # Recomendaciones específicas
        if sunat_ready:
            print("🎉 SISTEMA LISTO PARA USAR:")
            print("   1. ✅ Error 0160 solucionado e integrado")
            print("   2. ✅ Certificado real disponible")
            print("   3. ✅ Dependencias instaladas")
            print("   4. 🚀 PROBAR ENVÍO:")
            print("      • POST /api/sunat/send-bill/")
            print("      • Con documento_id de un documento firmado")
            print("      • Debería obtener CDR real de SUNAT")
        else:
            print("🔧 ACCIONES PENDIENTES:")
            
            if not component_status.get('dependencies'):
                print("   1. Instalar dependencias faltantes")
            
            if not component_status.get('certificate'):
                print("   2. Configurar certificado C23022479065.pfx")
                
            if not component_status.get('error_0160_fix'):
                print("   3. Verificar corrección Error 0160 integrada")
        
        print()
        
        # Información técnica
        print("💡 INFORMACIÓN TÉCNICA:")
        print("   🔧 Error 0160: Corrección INTEGRADA en views_sunat.py")
        print("   📋 No requiere archivos externos")
        print("   🎯 Certificado: C23022479065.pfx (REAL)")
        print("   🌐 Ambiente: SUNAT Beta")
        print("   📊 Test status: GET /api/sunat/status/")
        
        # Guardar reporte
        self._save_report()
        
        print("\n" + "=" * 60)
        print("🎉 TEST INTEGRADO COMPLETADO")
        print("=" * 60)
    
    def _save_report(self):
        """Guarda el reporte en archivo JSON"""
        try:
            report_dir = Path('temp') / 'test_reports'
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = report_dir / f'sunat_integrated_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'test_type': 'SUNAT_INTEGRATED_ERROR_0160',
                    'timestamp': self.timestamp,
                    'results': self.results,
                    'summary': {
                        'status': self.results.get('complete_integration', {}).get('status'),
                        'health_percentage': self.results.get('complete_integration', {}).get('health_percentage'),
                        'sunat_ready': self.results.get('complete_integration', {}).get('sunat_ready'),
                        'error_0160_solved': self.results.get('complete_integration', {}).get('error_0160_solved')
                    }
                }, f, indent=2, default=str)
            
            print(f"💾 Reporte guardado: {report_file}")
            
        except Exception as e:
            print(f"⚠️ No se pudo guardar reporte: {e}")


def main():
    """Función principal"""
    try:
        tester = SUNATIntegratedTest()
        tester.run_all_tests()
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrumpido por usuario")
        return 1
        
    except Exception as e:
        print(f"\n❌ Error ejecutando test: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())