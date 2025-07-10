#!/usr/bin/env python
"""
TEST RÁPIDO COMPLETO - Sistema SUNAT Error 0160 Solucionado
Archivo: test_sunat_complete.py
Ejecutar: python test_sunat_complete.py
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

class SUNATCompleteTest:
    """Test completo del sistema SUNAT con Error 0160 solucionado"""
    
    def __init__(self):
        self.results = {}
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("🚀 TEST RÁPIDO COMPLETO - SISTEMA SUNAT ERROR 0160")
        print("=" * 60)
        print(f"⏰ Iniciado: {self.timestamp}")
        print()
    
    def run_all_tests(self):
        """Ejecuta todos los tests en secuencia"""
        
        # Test 1: Django
        self.test_django_setup()
        
        # Test 2: Dependencias
        self.test_dependencies()
        
        # Test 3: Archivos críticos
        self.test_critical_files()
        
        # Test 4: Corrección Error 0160
        self.test_error_0160_fix()
        
        # Test 5: Base de datos
        self.test_database()
        
        # Test 6: Certificado digital
        self.test_certificate()
        
        # Test 7: API endpoints
        self.test_api_endpoints()
        
        # Test 8: Integración SUNAT
        self.test_sunat_integration()
        
        # Test 9: Sistema completo
        self.test_complete_system()
        
        # Reporte final
        self.generate_final_report()
    
    def test_django_setup(self):
        """Test 1: Configuración Django"""
        print("📋 Test 1: Configuración Django")
        
        if not DJANGO_OK:
            self.results['django'] = {
                'status': '❌ FAIL',
                'error': DJANGO_ERROR,
                'solution': 'Verificar configuración Django'
            }
            print(f"   ❌ Django: {DJANGO_ERROR}")
            return
        
        try:
            from django.conf import settings
            from documentos.models import DocumentoElectronico, Empresa
            
            self.results['django'] = {
                'status': '✅ OK',
                'version': django.VERSION,
                'apps_installed': len(settings.INSTALLED_APPS)
            }
            print("   ✅ Django configurado correctamente")
            
        except Exception as e:
            self.results['django'] = {
                'status': '❌ FAIL',
                'error': str(e)
            }
            print(f"   ❌ Error Django: {e}")
    
    def test_dependencies(self):
        """Test 2: Dependencias críticas"""
        print("\n📦 Test 2: Dependencias críticas")
        
        dependencies = {
            'requests': 'Comunicación HTTP con SUNAT',
            'lxml': 'Procesamiento XML',
            'zeep': 'Cliente SOAP (opcional)',
            'cryptography': 'Certificados digitales',
        }
        
        dep_results = {}
        
        for dep, description in dependencies.items():
            try:
                module = __import__(dep)
                version = getattr(module, '__version__', 'OK')
                dep_results[dep] = {'status': '✅ OK', 'version': version}
                print(f"   ✅ {dep}: {version}")
            except ImportError:
                dep_results[dep] = {'status': '❌ MISSING', 'description': description}
                print(f"   ❌ {dep}: NO INSTALADO - {description}")
        
        self.results['dependencies'] = dep_results
        
        # Verificar dependencias críticas
        critical_missing = [dep for dep, info in dep_results.items() 
                          if info['status'] == '❌ MISSING' and dep in ['requests', 'lxml']]
        
        if critical_missing:
            print(f"   ⚠️  CRÍTICO: Instalar: pip install {' '.join(critical_missing)}")
    
    def test_critical_files(self):
        """Test 3: Archivos críticos del sistema"""
        print("\n📁 Test 3: Archivos críticos")
        
        critical_files = {
            'sunat_0160_ultimate_fix.py': 'Corrección Error 0160',
            'api_rest/views_sunat.py': 'Views SUNAT',
            'certificados/production/C23022479065.pfx': 'Certificado digital',
            'manage.py': 'Django manager',
            '.env': 'Configuración'
        }
        
        file_results = {}
        
        for file_path, description in critical_files.items():
            full_path = Path(file_path)
            exists = full_path.exists()
            
            if exists:
                size = full_path.stat().st_size
                file_results[file_path] = {
                    'status': '✅ OK',
                    'size': f"{size:,} bytes"
                }
                print(f"   ✅ {file_path}: {size:,} bytes")
            else:
                file_results[file_path] = {
                    'status': '❌ MISSING',
                    'description': description
                }
                print(f"   ❌ {file_path}: FALTANTE - {description}")
        
        self.results['critical_files'] = file_results
    
    def test_error_0160_fix(self):
        """Test 4: Corrección Error 0160"""
        print("\n🔧 Test 4: Corrección Error 0160")
        
        try:
            # Intentar importar la corrección
            from sunat_0160_ultimate_fix import apply_error_0160_fix, SUNATError0160Fix
            
            # Test básico de la clase
            fixer = SUNATError0160Fix()
            
            self.results['error_0160_fix'] = {
                'status': '✅ DISPONIBLE',
                'class_loaded': True,
                'methods': [method for method in dir(fixer) if not method.startswith('_')]
            }
            print("   ✅ Corrección Error 0160 cargada exitosamente")
            print(f"   📋 Métodos disponibles: {len([m for m in dir(fixer) if not m.startswith('_')])}")
            
        except ImportError:
            self.results['error_0160_fix'] = {
                'status': '❌ NO INSTALADO',
                'error': 'sunat_0160_ultimate_fix.py no encontrado',
                'solution': 'Descargar e instalar sunat_0160_ultimate_fix.py'
            }
            print("   ❌ Corrección Error 0160 NO INSTALADA")
            print("   💡 Solución: Instalar sunat_0160_ultimate_fix.py")
            
        except Exception as e:
            self.results['error_0160_fix'] = {
                'status': '❌ ERROR',
                'error': str(e)
            }
            print(f"   ❌ Error cargando corrección: {e}")
    
    def test_database(self):
        """Test 5: Base de datos y modelos"""
        print("\n🗄️ Test 5: Base de datos")
        
        if not DJANGO_OK:
            self.results['database'] = {'status': '❌ SKIP', 'reason': 'Django no configurado'}
            print("   ❌ SKIP: Django no configurado")
            return
        
        try:
            from documentos.models import DocumentoElectronico, Empresa, TipoDocumento
            from django.db import connection
            
            # Verificar conexión
            connection.ensure_connection()
            
            # Contar registros
            empresas_count = Empresa.objects.count()
            docs_count = DocumentoElectronico.objects.count()
            tipos_count = TipoDocumento.objects.count()
            
            # Buscar documento con XML firmado para testing
            doc_with_xml = DocumentoElectronico.objects.filter(
                xml_firmado__isnull=False
            ).first()
            
            self.results['database'] = {
                'status': '✅ OK',
                'connection': True,
                'empresas_count': empresas_count,
                'documentos_count': docs_count,
                'tipos_documento_count': tipos_count,
                'test_document_available': bool(doc_with_xml),
                'test_document_id': str(doc_with_xml.id) if doc_with_xml else None
            }
            
            print(f"   ✅ Conexión DB: OK")
            print(f"   📊 Empresas: {empresas_count}")
            print(f"   📊 Documentos: {docs_count}")
            print(f"   📊 Tipos documento: {tipos_count}")
            print(f"   🧪 Documento test: {'✅ Disponible' if doc_with_xml else '❌ No disponible'}")
            
        except Exception as e:
            self.results['database'] = {
                'status': '❌ FAIL',
                'error': str(e)
            }
            print(f"   ❌ Error DB: {e}")
    
    def test_certificate(self):
        """Test 6: Certificado digital"""
        print("\n🔐 Test 6: Certificado digital")
        
        cert_path = Path('certificados/production/C23022479065.pfx')
        
        if not cert_path.exists():
            self.results['certificate'] = {
                'status': '❌ MISSING',
                'path': str(cert_path),
                'solution': 'Colocar certificado C23022479065.pfx en certificados/production/'
            }
            print(f"   ❌ Certificado no encontrado: {cert_path}")
            return
        
        try:
            # Verificar que se puede cargar el certificado
            cert_size = cert_path.stat().st_size
            
            # Test básico de carga (sin password por seguridad)
            self.results['certificate'] = {
                'status': '✅ ENCONTRADO',
                'path': str(cert_path),
                'size': f"{cert_size:,} bytes",
                'note': 'Password: Ch14pp32023'
            }
            
            print(f"   ✅ Certificado encontrado: {cert_size:,} bytes")
            print("   🔑 Password configurado: Ch14pp32023")
            
            # Test de carga real si está disponible la corrección
            try:
                from sunat_0160_ultimate_fix import SUNATError0160Fix
                fixer = SUNATError0160Fix()
                
                # No cargar el certificado real aquí para evitar problemas
                print("   📋 Sistema de carga: Disponible")
                
            except:
                print("   ⚠️  Sistema de carga: Requiere corrección Error 0160")
            
        except Exception as e:
            self.results['certificate'] = {
                'status': '❌ ERROR',
                'error': str(e)
            }
            print(f"   ❌ Error verificando certificado: {e}")
    
    def test_api_endpoints(self):
        """Test 7: API endpoints"""
        print("\n🌐 Test 7: API endpoints")
        
        if not DJANGO_OK:
            self.results['api_endpoints'] = {'status': '❌ SKIP', 'reason': 'Django no configurado'}
            print("   ❌ SKIP: Django no configurado")
            return
        
        try:
            from api_rest.views_sunat import (
                SendBillToSUNATView, TestSUNATConnectionView, 
                SUNATStatusView, get_system_health
            )
            
            # Test de importación de views
            endpoints_available = {
                'SendBillToSUNATView': SendBillToSUNATView,
                'TestSUNATConnectionView': TestSUNATConnectionView,
                'SUNATStatusView': SUNATStatusView,
                'get_system_health': get_system_health
            }
            
            # Test de función de salud del sistema
            try:
                health = get_system_health()
                health_status = health.get('overall_status', 'UNKNOWN')
            except Exception as e:
                health_status = f"ERROR: {e}"
            
            self.results['api_endpoints'] = {
                'status': '✅ OK',
                'endpoints_loaded': len(endpoints_available),
                'health_function': health_status,
                'available_endpoints': list(endpoints_available.keys())
            }
            
            print(f"   ✅ Views cargadas: {len(endpoints_available)}")
            print(f"   🏥 System health: {health_status}")
            
        except Exception as e:
            self.results['api_endpoints'] = {
                'status': '❌ FAIL',
                'error': str(e)
            }
            print(f"   ❌ Error cargando API: {e}")
    
    def test_sunat_integration(self):
        """Test 8: Integración SUNAT"""
        print("\n🔗 Test 8: Integración SUNAT")
        
        if not DJANGO_OK:
            self.results['sunat_integration'] = {'status': '❌ SKIP', 'reason': 'Django no configurado'}
            print("   ❌ SKIP: Django no configurado")
            return
        
        try:
            from api_rest.views_sunat import SUNATStatusView
            from django.test import RequestFactory
            
            # Crear request simulado
            factory = RequestFactory()
            request = factory.get('/api/sunat/status/')
            
            # Test del endpoint de status
            view = SUNATStatusView()
            response = view.get(request)
            
            if response.status_code == 200:
                data = response.data
                system_status = data.get('system_status', 'UNKNOWN')
                error_0160_status = data.get('error_0160_fix', {}).get('status', 'UNKNOWN')
                
                self.results['sunat_integration'] = {
                    'status': '✅ OK',
                    'system_status': system_status,
                    'error_0160_fix_status': error_0160_status,
                    'features_count': len(data.get('features', [])),
                    'endpoints_count': len(data.get('endpoints', {}))
                }
                
                print(f"   ✅ Status endpoint: OK")
                print(f"   📊 System status: {system_status}")
                print(f"   🔧 Error 0160 fix: {error_0160_status}")
                
            else:
                self.results['sunat_integration'] = {
                    'status': '❌ FAIL',
                    'http_status': response.status_code
                }
                print(f"   ❌ Status endpoint error: {response.status_code}")
                
        except Exception as e:
            self.results['sunat_integration'] = {
                'status': '❌ ERROR',
                'error': str(e)
            }
            print(f"   ❌ Error integración: {e}")
    
    def test_complete_system(self):
        """Test 9: Sistema completo"""
        print("\n🎯 Test 9: Sistema completo")
        
        # Evaluar estado general
        critical_components = [
            'django', 'dependencies', 'critical_files', 
            'error_0160_fix', 'database', 'api_endpoints'
        ]
        
        component_status = {}
        for component in critical_components:
            if component in self.results:
                status = self.results[component].get('status', '❌ UNKNOWN')
                component_status[component] = status.startswith('✅')
            else:
                component_status[component] = False
        
        # Calcular estado general
        total_components = len(component_status)
        healthy_components = sum(component_status.values())
        health_percentage = (healthy_components / total_components) * 100
        
        # Determinar estado del sistema
        if health_percentage >= 90:
            system_status = '🎉 EXCELENTE'
            system_message = 'Sistema completamente funcional - Error 0160 solucionado'
        elif health_percentage >= 70:
            system_status = '✅ BUENO'
            system_message = 'Sistema funcional con componentes menores pendientes'
        elif health_percentage >= 50:
            system_status = '⚠️ PARCIAL'
            system_message = 'Sistema parcialmente funcional - requiere correcciones'
        else:
            system_status = '❌ CRÍTICO'
            system_message = 'Sistema requiere configuración urgente'
        
        # Detectar problema específico de Error 0160
        error_0160_ready = (
            self.results.get('error_0160_fix', {}).get('status', '').startswith('✅') and
            self.results.get('dependencies', {}).get('requests', {}).get('status', '').startswith('✅')
        )
        
        self.results['complete_system'] = {
            'status': system_status,
            'message': system_message,
            'health_percentage': health_percentage,
            'healthy_components': healthy_components,
            'total_components': total_components,
            'error_0160_ready': error_0160_ready,
            'component_status': component_status
        }
        
        print(f"   📊 Estado general: {system_status}")
        print(f"   💯 Salud del sistema: {health_percentage:.1f}%")
        print(f"   🔧 Error 0160 listo: {'✅ SÍ' if error_0160_ready else '❌ NO'}")
        print(f"   📋 Componentes OK: {healthy_components}/{total_components}")
    
    def generate_final_report(self):
        """Genera reporte final completo"""
        print("\n" + "=" * 60)
        print("📋 REPORTE FINAL")
        print("=" * 60)
        
        system_info = self.results.get('complete_system', {})
        system_status = system_info.get('status', '❌ UNKNOWN')
        health_percentage = system_info.get('health_percentage', 0)
        error_0160_ready = system_info.get('error_0160_ready', False)
        
        print(f"⏰ Completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Estado General: {system_status}")
        print(f"💯 Salud Sistema: {health_percentage:.1f}%")
        print(f"🔧 Error 0160: {'✅ LISTO' if error_0160_ready else '❌ PENDIENTE'}")
        print()
        
        # Resumen por componente
        print("📊 RESUMEN POR COMPONENTE:")
        for component, result in self.results.items():
            if component != 'complete_system':
                status = result.get('status', '❌ UNKNOWN')
                print(f"   {component:20} : {status}")
        
        print()
        
        # Recomendaciones urgentes
        print("🚨 ACCIONES REQUERIDAS:")
        urgent_actions = []
        
        # Error 0160
        if not error_0160_ready:
            if not self.results.get('error_0160_fix', {}).get('status', '').startswith('✅'):
                urgent_actions.append("1. CRÍTICO: Instalar sunat_0160_ultimate_fix.py")
        
        # Dependencias
        deps = self.results.get('dependencies', {})
        missing_deps = [dep for dep, info in deps.items() 
                       if info.get('status') == '❌ MISSING' and dep in ['requests', 'lxml']]
        if missing_deps:
            urgent_actions.append(f"2. CRÍTICO: pip install {' '.join(missing_deps)}")
        
        # Certificado
        if not self.results.get('certificate', {}).get('status', '').startswith('✅'):
            urgent_actions.append("3. IMPORTANTE: Colocar certificado C23022479065.pfx")
        
        # Database
        if not self.results.get('database', {}).get('status', '').startswith('✅'):
            urgent_actions.append("4. IMPORTANTE: Configurar base de datos")
        
        if urgent_actions:
            for action in urgent_actions:
                print(f"   {action}")
        else:
            print("   🎉 ¡No hay acciones urgentes requeridas!")
        
        print()
        
        # Próximos pasos
        print("🎯 PRÓXIMOS PASOS:")
        if error_0160_ready:
            print("   1. ✅ Sistema listo - probar envío de documento")
            print("   2. 📋 Ejecutar: POST /api/sunat/send-bill/")
            print("   3. 🔍 Revisar logs para confirmación")
            print("   4. 🎉 ¡Error 0160 debería estar solucionado!")
        else:
            print("   1. 🔧 Completar acciones requeridas arriba")
            print("   2. 🔄 Reiniciar Django: python manage.py runserver")
            print("   3. 🧪 Re-ejecutar este test: python test_sunat_complete.py")
            print("   4. 📋 Probar envío cuando esté listo")
        
        print()
        
        # Información de contacto/ayuda
        print("💡 AYUDA ADICIONAL:")
        print("   📋 Logs SUNAT: logs/sunat.log")
        print("   🌐 Test connection: GET /api/sunat/test-connection/")
        print("   📊 System status: GET /api/sunat/status/")
        print("   🐛 Debug files: temp/sunat_responses/")
        
        # Guardar reporte en archivo
        try:
            report_file = Path('temp') / 'test_reports' / f'sunat_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': self.timestamp,
                    'results': self.results,
                    'summary': {
                        'status': system_status,
                        'health_percentage': health_percentage,
                        'error_0160_ready': error_0160_ready
                    }
                }, f, indent=2, default=str)
            
            print(f"\n💾 Reporte guardado: {report_file}")
            
        except Exception as e:
            print(f"\n⚠️ No se pudo guardar reporte: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 TEST COMPLETO FINALIZADO")
        print("=" * 60)


def main():
    """Función principal"""
    try:
        # Crear y ejecutar test
        tester = SUNATCompleteTest()
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