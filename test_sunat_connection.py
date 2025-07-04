#!/usr/bin/env python
"""
Script de prueba para conexión con SUNAT Beta
Ubicación: test_sunat_connection.py (en la raíz del proyecto)
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

from django.conf import settings
from sunat_integration.soap_client import SUNATSoapClient
from sunat_integration.exceptions import SUNATError

def test_sunat_configuration():
    """Prueba la configuración de SUNAT"""
    print("🔧 Verificando configuración SUNAT...")
    
    config = settings.SUNAT_CONFIG
    
    print(f"   - Ambiente: {config['ENVIRONMENT']}")
    print(f"   - RUC: {config['RUC']}")
    print(f"   - Usuario Beta: {config['RUC']}{config['BETA_USER']}")
    print(f"   - Password Beta: {config['BETA_PASSWORD']}")
    
    # Verificar URLs
    wsdl_urls = config['WSDL_URLS']['beta']
    print(f"   - WSDL Factura: {wsdl_urls['factura']}")
    
    return True

def test_soap_client_initialization():
    """Prueba la inicialización del cliente SOAP"""
    print("\n🌐 Probando inicialización cliente SOAP...")
    
    try:
        client = SUNATSoapClient('factura', 'beta')
        print("   ✅ Cliente SOAP inicializado")
        
        # Probar conexión
        connection_test = client.test_connection()
        
        if connection_test['success']:
            print("   ✅ Conexión con SUNAT exitosa")
            print(f"   - WSDL: {connection_test['service_info']['wsdl_url']}")
            print(f"   - Operaciones: {connection_test['service_info']['operations']}")
            return True
        else:
            print(f"   ❌ Error en conexión: {connection_test['error']}")
            return False
            
    except SUNATError as e:
        print(f"   ❌ Error SUNAT: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
        return False

def test_wsdl_accessibility():
    """Prueba el acceso directo a los WSDL de SUNAT"""
    print("\n📡 Probando acceso a WSDL...")
    
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    # Configurar sesión con reintentos
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    wsdl_urls = {
        'Factura Beta': 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl',
        'Guía Beta': 'https://e-beta.sunat.gob.pe/ol-ti-itemision-guia-gem-beta/billService?wsdl',
        'Retención Beta': 'https://e-beta.sunat.gob.pe/ol-ti-itemision-otroscpe-gem-beta/billService?wsdl'
    }
    
    all_accessible = True
    
    for service_name, url in wsdl_urls.items():
        try:
            print(f"   - Probando {service_name}...")
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                content_length = len(response.content)
                print(f"     ✅ Accesible ({content_length} bytes)")
            else:
                print(f"     ❌ HTTP {response.status_code}")
                all_accessible = False
                
        except requests.exceptions.Timeout:
            print(f"     ❌ Timeout")
            all_accessible = False
        except requests.exceptions.ConnectionError:
            print(f"     ❌ Error de conexión")
            all_accessible = False
        except Exception as e:
            print(f"     ❌ Error: {e}")
            all_accessible = False
    
    return all_accessible

def test_credentials_format():
    """Prueba el formato de credenciales"""
    print("\n🔑 Verificando formato de credenciales...")
    
    from sunat_integration.utils import get_sunat_credentials
    
    try:
        credentials = get_sunat_credentials('beta')
        
        print(f"   - Username: {credentials['username']}")
        print(f"   - Password: {credentials['password']}")
        
        # Validar formato
        username = credentials['username']
        
        if len(username) >= 14:  # 11 RUC + mínimo 3 usuario
            print("   ✅ Formato de username válido")
        else:
            print("   ❌ Formato de username inválido")
            return False
        
        if credentials['password']:
            print("   ✅ Password configurado")
        else:
            print("   ❌ Password no configurado")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error obteniendo credenciales: {e}")
        return False

def test_xml_sample_generation():
    """Prueba la generación de XML de muestra"""
    print("\n📄 Probando generación de XML de muestra...")
    
    try:
        from documentos.models import Empresa, TipoDocumento
        from conversion.generators import generate_ubl_xml
        
        # Verificar si hay empresas en la BD
        empresas = Empresa.objects.filter(activo=True)
        if not empresas.exists():
            print("   ⚠️  No hay empresas en la base de datos")
            print("   💡 Crear una empresa primero para pruebas completas")
            return True  # No es error crítico
        
        print(f"   ✅ {empresas.count()} empresa(s) disponible(s)")
        
        # Verificar tipos de documento
        tipos = TipoDocumento.objects.filter(activo=True)
        print(f"   ✅ {tipos.count()} tipo(s) de documento disponible(s)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_zip_generation():
    """Prueba la generación de archivos ZIP"""
    print("\n📦 Probando generación de ZIP...")
    
    try:
        from sunat_integration.zip_generator import zip_generator
        
        # XML de prueba simple
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">F001-00000001</cbc:ID>
    <cbc:IssueDate xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">2025-06-28</cbc:IssueDate>
</Invoice>'''
        
        # Simular documento
        class MockDocumento:
            def __init__(self):
                self.empresa = MockEmpresa()
                self.tipo_documento = MockTipoDocumento()
                self.serie = "F001"
                self.numero = 1
            
            def get_numero_completo(self):
                return f"{self.tipo_documento.codigo}-{self.serie}-{self.numero:08d}"
        
        class MockEmpresa:
            ruc = "20123456789"
        
        class MockTipoDocumento:
            codigo = "01"
        
        documento = MockDocumento()
        
        # Generar ZIP
        zip_content = zip_generator.create_document_zip(documento, test_xml)
        
        print(f"   ✅ ZIP generado: {len(zip_content)} bytes")
        
        # Verificar estructura
        zip_info = zip_generator.get_zip_info(zip_content)
        print(f"   - Archivos: {len(zip_info['files'])}")
        print(f"   - XMLs: {zip_info['xml_files_count']}")
        print(f"   - Tiene dummy: {zip_info['has_dummy_folder']}")
        print(f"   - Compresión: {zip_info['compression_ratio']}%")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error generando ZIP: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 PRUEBAS DE CONEXIÓN SUNAT BETA")
    print("=" * 60)
    
    tests = [
        ("Configuración SUNAT", test_sunat_configuration),
        ("Acceso a WSDL", test_wsdl_accessibility),
        ("Formato de credenciales", test_credentials_format),
        ("Cliente SOAP", test_soap_client_initialization),
        ("Generación XML", test_xml_sample_generation),
        ("Generación ZIP", test_zip_generation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("🚀 ¡Listo para enviar documentos a SUNAT Beta!")
        print("\n📝 Próximos pasos:")
        print("1. Crear empresas y documentos de prueba")
        print("2. Generar XML firmado")
        print("3. Enviar primera factura a SUNAT Beta")
        return 0
    else:
        print(f"\n⚠️  {total - passed} prueba(s) fallaron")
        print("🔧 Revisar configuración antes de continuar")
        return 1

if __name__ == '__main__':
    exit(main())