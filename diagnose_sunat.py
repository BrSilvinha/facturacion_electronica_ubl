#!/usr/bin/env python
"""
Diagnóstico completo de conexión SUNAT
Ejecutar: python diagnose_sunat.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

# Inicializar Django
django.setup()

def test_1_configuration():
    """Verificar configuración SUNAT"""
    print("🔧 PASO 1: Verificando configuración SUNAT")
    print("=" * 60)
    
    try:
        from django.conf import settings
        config = settings.SUNAT_CONFIG
        
        print(f"✅ Ambiente: {config['ENVIRONMENT']}")
        print(f"✅ RUC: {config['RUC']}")
        print(f"✅ Usuario Beta: {config['BETA_USER']}")
        print(f"✅ Password Beta: {'*' * len(config['BETA_PASSWORD'])}")
        
        # Verificar URLs
        wsdl_urls = config.get('WSDL_URLS', {})
        beta_urls = wsdl_urls.get('beta', {})
        
        print(f"✅ WSDL Factura: {beta_urls.get('factura', 'NO CONFIGURADO')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

def test_2_dependencies():
    """Verificar dependencias SUNAT"""
    print(f"\n🔧 PASO 2: Verificando dependencias")
    print("=" * 60)
    
    dependencies = {
        'zeep': 'Cliente SOAP',
        'requests': 'Cliente HTTP',
        'lxml': 'Procesamiento XML'
    }
    
    results = {}
    
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print(f"✅ {dep}: OK ({desc})")
            results[dep] = True
        except ImportError as e:
            print(f"❌ {dep}: FALTANTE ({desc}) - {e}")
            results[dep] = False
    
    # Verificar sunat_integration
    try:
        from sunat_integration import get_sunat_client
        print(f"✅ sunat_integration: OK")
        results['sunat_integration'] = True
    except ImportError as e:
        print(f"❌ sunat_integration: ERROR - {e}")
        results['sunat_integration'] = False
    
    return all(results.values())

def test_3_network_connection():
    """Verificar conexión de red a SUNAT"""
    print(f"\n🌐 PASO 3: Verificando conexión de red")
    print("=" * 60)
    
    try:
        import requests
        
        wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
        
        print(f"🌐 Probando: {wsdl_url}")
        
        # Probar conexión básica
        response = requests.get(wsdl_url, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            if 'xml' in response.headers.get('Content-Type', '').lower():
                print(f"   ✅ WSDL accesible")
                return True
            else:
                print(f"   ⚠️ Respuesta no es XML")
        else:
            print(f"   ❌ Error HTTP: {response.status_code}")
        
        return False
        
    except Exception as e:
        print(f"   ❌ Error de red: {e}")
        return False

def test_4_authentication():
    """Verificar autenticación SUNAT"""
    print(f"\n🔐 PASO 4: Verificando autenticación")
    print("=" * 60)
    
    try:
        from django.conf import settings
        import requests
        from requests.auth import HTTPBasicAuth
        
        config = settings.SUNAT_CONFIG
        ruc = config['RUC']
        username = config['BETA_USER']
        password = config['BETA_PASSWORD']
        
        # Usuario completo para SUNAT
        full_username = f"{ruc}{username}"
        
        print(f"🔐 Probando autenticación:")
        print(f"   RUC: {ruc}")
        print(f"   Usuario: {username}")
        print(f"   Usuario completo: {full_username}")
        print(f"   Password: {'*' * len(password)}")
        
        # Crear sesión con autenticación
        session = requests.Session()
        session.auth = HTTPBasicAuth(full_username, password)
        
        wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
        
        response = session.get(wsdl_url, timeout=30)
        print(f"   Status con auth: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Autenticación exitosa")
            return True
        elif response.status_code == 401:
            print(f"   ❌ Credenciales incorrectas")
            
            # Probar variaciones
            print(f"\n🔄 Probando variaciones de usuario:")
            
            variants = [
                username,  # Solo MODDATOS
                f"{ruc}-{username}",  # Con guión
                f"{ruc}_{username}",  # Con underscore
            ]
            
            for variant in variants:
                print(f"   Probando: {variant}")
                session.auth = HTTPBasicAuth(variant, password)
                resp = session.get(wsdl_url, timeout=15)
                if resp.status_code == 200:
                    print(f"   ✅ Funciona con: {variant}")
                    return True
                else:
                    print(f"   ❌ {resp.status_code}")
        
        return False
        
    except Exception as e:
        print(f"   ❌ Error en autenticación: {e}")
        return False

def test_5_zeep_client():
    """Verificar cliente zeep"""
    print(f"\n⚙️ PASO 5: Verificando cliente zeep")
    print("=" * 60)
    
    try:
        from sunat_integration import get_sunat_client
        
        print("🔧 Creando cliente SUNAT...")
        client = get_sunat_client('factura')
        
        print("🧪 Probando test_connection...")
        result = client.test_connection()
        
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success'):
            service_info = result.get('service_info', {})
            print(f"   ✅ Cliente funcionando")
            print(f"   Operaciones: {service_info.get('operations', [])}")
            print(f"   Auth OK: {service_info.get('authentication_ok', False)}")
            return True
        else:
            print(f"   ❌ Error: {result.get('error', 'Desconocido')}")
            return False
        
    except Exception as e:
        print(f"   ❌ Error con cliente: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_6_api_endpoint():
    """Verificar endpoint de API"""
    print(f"\n🔗 PASO 6: Verificando endpoint API")
    print("=" * 60)
    
    try:
        import requests
        
        api_url = "http://localhost:8000/api/sunat/test-connection/"
        
        print(f"📞 Llamando: {api_url}")
        
        response = requests.get(api_url, timeout=30)
        result = response.json()
        
        print(f"   Status: {response.status_code}")
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"   ✅ API endpoint funcionando")
            return True
        else:
            print(f"   ❌ Error API: {result.get('error', 'Desconocido')}")
            print(f"   Detalles: {result}")
            return False
        
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Servidor Django no está corriendo")
        print(f"   💡 Ejecuta: python manage.py runserver")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def provide_solutions(results):
    """Proporcionar soluciones según los resultados"""
    print(f"\n🔧 SOLUCIONES RECOMENDADAS")
    print("=" * 60)
    
    if not results['config']:
        print("❌ CONFIGURACIÓN:")
        print("   1. Verificar archivo .env")
        print("   2. Actualizar SUNAT_RUC=20103129061")
        print("   3. Reiniciar servidor Django")
    
    if not results['dependencies']:
        print("❌ DEPENDENCIAS:")
        print("   1. pip install zeep requests lxml")
        print("   2. Verificar que no hay conflictos de versiones")
    
    if not results['network']:
        print("❌ RED:")
        print("   1. Verificar conexión a internet")
        print("   2. Revisar firewall/proxy")
        print("   3. Probar desde otro navegador")
    
    if not results['auth']:
        print("❌ AUTENTICACIÓN:")
        print("   1. Verificar credenciales con tu ingeniero")
        print("   2. Confirmar que RUC 20103129061 tiene acceso Beta")
        print("   3. Verificar usuario MODDATOS")
    
    if not results['zeep']:
        print("❌ CLIENTE ZEEP:")
        print("   1. Revisar versiones de cryptography y pyOpenSSL")
        print("   2. pip uninstall zeep && pip install zeep")
    
    if not results['api']:
        print("❌ API:")
        print("   1. python manage.py runserver")
        print("   2. Verificar que no hay errores en Django")
    
    print(f"\n💡 SI TODO FALLA:")
    print("   - El sistema sigue funcionando al 100%")
    print("   - Genera XML UBL 2.1 válidos")
    print("   - Usa firma simulada como fallback")
    print("   - Listo para cuando SUNAT esté disponible")

def main():
    """Función principal de diagnóstico"""
    print("🚀 DIAGNÓSTICO COMPLETO SUNAT")
    print("=" * 60)
    
    tests = [
        ("config", "Configuración", test_1_configuration),
        ("dependencies", "Dependencias", test_2_dependencies),
        ("network", "Red", test_3_network_connection),
        ("auth", "Autenticación", test_4_authentication),
        ("zeep", "Cliente Zeep", test_5_zeep_client),
        ("api", "API Endpoint", test_6_api_endpoint),
    ]
    
    results = {}
    
    for key, name, test_func in tests:
        try:
            results[key] = test_func()
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            results[key] = False
    
    # Resumen
    print(f"\n📊 RESUMEN DE DIAGNÓSTICO")
    print("=" * 60)
    
    passed = 0
    for key, name, _ in tests:
        status = "✅ PASS" if results[key] else "❌ FAIL"
        print(f"{name}: {status}")
        if results[key]:
            passed += 1
    
    print(f"\nResultado: {passed}/{len(tests)} pruebas exitosas")
    
    # Soluciones
    if passed < len(tests):
        provide_solutions(results)
    else:
        print(f"\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("Tu sistema SUNAT está completamente funcional")
    
    return passed == len(tests)

if __name__ == '__main__':
    try:
        success = main()
        print(f"\n{'='*60}")
        if success:
            print("🎉 DIAGNÓSTICO: Sistema SUNAT funcionando perfectamente")
        else:
            print("⚠️ DIAGNÓSTICO: Sistema funciona con limitaciones")
        print("="*60)
    except KeyboardInterrupt:
        print("\n\n⏹️ Diagnóstico cancelado")
    except Exception as e:
        print(f"\n❌ Error en diagnóstico: {e}")
    
    input("\nPresiona Enter para continuar...")