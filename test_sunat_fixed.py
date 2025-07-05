#!/usr/bin/env python
"""
Prueba SUNAT con corrección de autenticación para zeep
SOLUCIÓN: Manejar autenticación para todas las solicitudes WSDL
Ejecutar: python test_sunat_fixed.py
"""

import os
import sys
import requests
from pathlib import Path
import base64
import xml.etree.ElementTree as ET

# Configurar Django
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

import django
django.setup()

def test_wsdl_access():
    """Prueba acceso directo al WSDL"""
    print("🌐 Probando acceso directo al WSDL...")
    
    wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
    
    try:
        response = requests.get(wsdl_url, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            if 'wsdl:definitions' in response.text:
                print("✅ WSDL válido y accesible")
                return True
            else:
                print("❌ Respuesta no es WSDL válido")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error accediendo WSDL: {e}")
        return False

def test_authenticated_session():
    """Prueba sesión con autenticación básica"""
    print("\n🔐 Probando sesión con autenticación...")
    
    try:
        from requests.auth import HTTPBasicAuth
        
        # Credenciales
        username = "20123456789MODDATOS"
        password = "MODDATOS"
        
        # Crear sesión con autenticación
        session = requests.Session()
        session.auth = HTTPBasicAuth(username, password)
        
        # Probar diferentes URLs
        test_urls = [
            "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl",
            "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?ns1.wsdl"
        ]
        
        for url in test_urls:
            print(f"Probando: {url}")
            try:
                response = session.get(url, timeout=30)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"  ✅ Accesible con autenticación")
                elif response.status_code == 401:
                    print(f"  ❌ Credenciales incorrectas")
                    return False
                else:
                    print(f"  ⚠️ Código: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configurando sesión: {e}")
        return False

def test_zeep_with_auth_fixed():
    """Prueba cliente zeep con autenticación CORREGIDA"""
    print("\n🔧 Probando cliente zeep con autenticación CORREGIDA...")
    
    try:
        from zeep import Client, Settings
        from zeep.transports import Transport
        from zeep.wsse.username import UsernameToken
        from requests import Session
        from requests.auth import HTTPBasicAuth
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        # Credenciales
        username = "20123456789MODDATOS"
        password = "MODDATOS"
        
        # SOLUCIÓN 1: Configurar sesión con autenticación PERSISTENTE
        session = Session()
        session.auth = HTTPBasicAuth(username, password)
        
        # Headers adicionales
        session.headers.update({
            'User-Agent': 'Python-SUNAT/1.0',
            'Accept': 'text/xml,application/xml,application/soap+xml',
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        })
        
        # SOLUCIÓN 2: Configurar adaptador con reintentos
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # SOLUCIÓN 3: Configurar transporte con timeout más largo
        transport = Transport(
            session=session,
            timeout=120,  # Timeout más largo
            operation_timeout=120
        )
        
        # SOLUCIÓN 4: Configurar settings para ser más permisivo
        settings = Settings(
            strict=False,
            xml_huge_tree=True,
            forbid_dtd=False,
            forbid_entities=False,
            forbid_external=False
        )
        
        # URL del WSDL
        wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
        
        print(f"Creando cliente con:")
        print(f"  Usuario: {username}")
        print(f"  WSDL: {wsdl_url}")
        print(f"  Timeout: 120s")
        print(f"  Reintentos: 3")
        
        # SOLUCIÓN 5: Crear cliente con configuración robusta
        client = Client(
            wsdl_url, 
            transport=transport, 
            settings=settings
        )
        print("✅ Cliente zeep creado exitosamente")
        
        # SOLUCIÓN 6: Configurar WS-Security DESPUÉS de crear el cliente
        wsse = UsernameToken(
            username=username, 
            password=password,
            use_digest=False  # SUNAT usa texto plano
        )
        client.wsse = wsse
        print("✅ WS-Security configurado")
        
        # Verificar operaciones
        if hasattr(client, 'service'):
            operations = [op for op in dir(client.service) if not op.startswith('_')]
            print(f"✅ Operaciones disponibles: {operations}")
            
            # Verificar que las operaciones críticas estén disponibles
            required_ops = ['sendBill', 'getStatus', 'sendSummary']
            available_ops = [op for op in operations if op in required_ops]
            print(f"✅ Operaciones críticas: {available_ops}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando cliente zeep: {e}")
        
        # Análisis detallado del error
        error_msg = str(e)
        print(f"\nAnálisis del error:")
        print(f"Error completo: {error_msg}")
        
        if '401' in error_msg:
            print("💡 Error 401: Problema de autenticación")
            print("   - Verificar que las credenciales sean correctas")
            print("   - Verificar formato de usuario (RUC + usuario)")
            print("   - Verificar que el servidor acepte HTTP Basic Auth")
        elif 'timeout' in error_msg.lower():
            print("💡 Error de timeout: Conexión lenta")
            print("   - Intentar con timeout más largo")
            print("   - Verificar conectividad de red")
        elif 'ssl' in error_msg.lower():
            print("💡 Error SSL: Problema de certificados")
            print("   - Verificar certificados SSL")
        elif 'ns1.wsdl' in error_msg:
            print("💡 Error en WSDL secundario")
            print("   - zeep está intentando cargar WSDLs adicionales")
            print("   - La autenticación no se propaga a estas solicitudes")
        
        return False

def test_zeep_with_custom_wsdl():
    """Prueba zeep descargando y usando WSDL local"""
    print("\n📁 Probando zeep con WSDL local...")
    
    try:
        from zeep import Client, Settings
        from zeep.transports import Transport
        from zeep.wsse.username import UsernameToken
        from requests import Session
        from requests.auth import HTTPBasicAuth
        import tempfile
        import os
        
        # Credenciales
        username = "20123456789MODDATOS"
        password = "MODDATOS"
        
        # SOLUCIÓN: Descargar WSDL localmente con autenticación
        session = Session()
        session.auth = HTTPBasicAuth(username, password)
        
        wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
        
        print("Descargando WSDL con autenticación...")
        response = session.get(wsdl_url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error descargando WSDL: {response.status_code}")
            return False
        
        # Guardar WSDL localmente
        with tempfile.NamedTemporaryFile(mode='w', suffix='.wsdl', delete=False) as f:
            f.write(response.text)
            local_wsdl_path = f.name
        
        print(f"✅ WSDL guardado en: {local_wsdl_path}")
        
        try:
            # Crear cliente con WSDL local
            transport = Transport(session=session, timeout=120)
            settings = Settings(strict=False, xml_huge_tree=True)
            
            client = Client(
                f"file://{local_wsdl_path}",
                transport=transport,
                settings=settings
            )
            
            print("✅ Cliente zeep con WSDL local creado")
            
            # Configurar WS-Security
            wsse = UsernameToken(username=username, password=password, use_digest=False)
            client.wsse = wsse
            
            # Verificar operaciones
            if hasattr(client, 'service'):
                operations = [op for op in dir(client.service) if not op.startswith('_')]
                print(f"✅ Operaciones: {operations}")
            
            return True
            
        finally:
            # Limpiar archivo temporal
            try:
                os.unlink(local_wsdl_path)
            except:
                pass
        
    except Exception as e:
        print(f"❌ Error con WSDL local: {e}")
        return False

def test_soap_call_with_minimal_zip():
    """Prueba llamada SOAP con ZIP mínimo válido"""
    print("\n📞 Probando llamada SOAP con ZIP mínimo...")
    
    try:
        from zeep import Client, Settings
        from zeep.transports import Transport
        from zeep.wsse.username import UsernameToken
        from requests import Session
        from requests.auth import HTTPBasicAuth
        import zipfile
        import io
        
        # Credenciales
        username = "20123456789MODDATOS"
        password = "MODDATOS"
        
        # Configurar cliente (usando la estrategia que funcione)
        session = Session()
        session.auth = HTTPBasicAuth(username, password)
        
        transport = Transport(session=session, timeout=120)
        settings = Settings(strict=False, xml_huge_tree=True)
        
        wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
        
        try:
            client = Client(wsdl_url, transport=transport, settings=settings)
        except Exception as e:
            print(f"❌ No se pudo crear cliente: {e}")
            return False
        
        # Configurar WS-Security
        wsse = UsernameToken(username=username, password=password, use_digest=False)
        client.wsse = wsse
        
        # Crear XML mínimo pero más realista
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" 
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
    <cbc:ID>F001-00000001</cbc:ID>
    <cbc:IssueDate>2025-07-05</cbc:IssueDate>
    <cbc:InvoiceTypeCode>01</cbc:InvoiceTypeCode>
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">20123456789</cbc:ID>
            </cac:PartyIdentification>
        </cac:Party>
    </cac:AccountingSupplierParty>
</Invoice>'''
        
        # Crear ZIP con nombre correcto
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("20123456789-01-F001-00000001.xml", xml_content)
        
        zip_content = zip_buffer.getvalue()
        zip_base64 = base64.b64encode(zip_content).decode('utf-8')
        
        print(f"📦 ZIP creado: {len(zip_content)} bytes")
        print(f"📦 Base64: {len(zip_base64)} chars")
        
        # Parámetros de la llamada
        file_name = "20123456789-01-F001-00000001.zip"
        
        print(f"📞 Llamando sendBill con:")
        print(f"   fileName: {file_name}")
        print(f"   contentFile: {zip_base64[:50]}...")
        
        # Realizar llamada
        response = client.service.sendBill(
            fileName=file_name,
            contentFile=zip_base64
        )
        
        print(f"✅ Respuesta recibida: {type(response)}")
        
        # Analizar respuesta
        if hasattr(response, 'applicationResponse'):
            print("✅ Respuesta con CDR - Documento procesado")
            return True
        else:
            print(f"📄 Respuesta: {response}")
            return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error en llamada SOAP: {error_msg}")
        
        # Análisis del error
        if '401' in error_msg or 'authentication' in error_msg.lower():
            print("❌ Error de autenticación")
            return False
        elif 'validation' in error_msg.lower() or 'invalid' in error_msg.lower():
            print("✅ Autenticación OK - Error de validación (esperado con datos dummy)")
            return True
        elif 'zip' in error_msg.lower() or 'archivo' in error_msg.lower():
            print("✅ Autenticación OK - Error de formato de archivo (esperado)")
            return True
        elif 'timeout' in error_msg.lower():
            print("⏱️ Timeout - Servidor lento")
            return False
        else:
            print("❓ Error desconocido")
            return False

def test_sunat_client_integration():
    """Prueba integración con el cliente SUNAT del proyecto"""
    print("\n🔗 Probando integración con SUNATSoapClient...")
    
    try:
        # Importar el cliente del proyecto
        from sunat_integration.soap_client import SUNATSoapClient
        
        print("📦 Creando cliente SUNAT...")
        
        # Crear cliente
        client = SUNATSoapClient(
            service_type='factura',
            environment='beta',
            lazy_init=False
        )
        
        print("✅ Cliente SUNAT creado")
        
        # Probar conexión
        print("🧪 Probando conexión...")
        result = client.test_connection()
        
        if result['success']:
            print("✅ Test de conexión exitoso")
            print(f"   WSDL: {result['service_info']['wsdl_url']}")
            print(f"   Operaciones: {len(result['service_info']['operations'])}")
            print(f"   Autenticación: {result['service_info']['authentication_ok']}")
            return True
        else:
            print(f"❌ Test de conexión fallido: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Error en integración: {e}")
        return False

def main():
    """Función principal mejorada"""
    print("🚀 Prueba SUNAT CORREGIDA")
    print("=" * 60)
    
    # Verificar configuración
    try:
        from django.conf import settings
        print(f"✅ Django configurado")
        print(f"✅ RUC: {settings.SUNAT_CONFIG['RUC']}")
        print(f"✅ Ambiente: {settings.SUNAT_CONFIG['ENVIRONMENT']}")
        print(f"✅ Usuario: {settings.SUNAT_CONFIG['BETA_USER']}")
        print(f"✅ Password: {'*' * len(settings.SUNAT_CONFIG['BETA_PASSWORD'])}")
    except Exception as e:
        print(f"❌ Error configuración Django: {e}")
        return False
    
    # Ejecutar pruebas mejoradas
    tests = [
        ("1. Acceso WSDL", test_wsdl_access),
        ("2. Sesión Autenticada", test_authenticated_session),
        ("3. Cliente Zeep CORREGIDO", test_zeep_with_auth_fixed),
        ("4. Cliente Zeep WSDL Local", test_zeep_with_custom_wsdl),
        ("5. Llamada SOAP", test_soap_call_with_minimal_zip),
        ("6. Integración Cliente SUNAT", test_sunat_client_integration)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"EJECUTANDO: {name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results.append((name, result))
            
            if result:
                print(f"✅ {name}: EXITOSO")
            else:
                print(f"❌ {name}: FALLIDO")
                
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            results.append((name, False))
    
    # Resumen final
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print(f"{'='*60}")
    
    successful_tests = [name for name, result in results if result]
    failed_tests = [name for name, result in results if not result]
    
    for name, result in results:
        status = "✅ EXITOSO" if result else "❌ FALLIDO"
        print(f"{name}: {status}")
    
    # Diagnóstico final
    print(f"\n{'='*60}")
    print("DIAGNÓSTICO Y SOLUCIONES")
    print(f"{'='*60}")
    
    if len(successful_tests) == len(tests):
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ Conexión SUNAT completamente funcional")
        
    elif len(successful_tests) >= 4:
        print("🎯 MAYORÍA DE PRUEBAS EXITOSAS")
        print("✅ Conexión SUNAT funcional con algunas limitaciones")
        
        if "3. Cliente Zeep CORREGIDO" in successful_tests:
            print("✅ Problema de autenticación zeep SOLUCIONADO")
        
    else:
        print("⚠️ PROBLEMAS SIGNIFICATIVOS DETECTADOS")
        
        if "1. Acceso WSDL" in failed_tests:
            print("❌ Problema de conectividad básica")
            print("💡 Solución: Verificar conexión de red y firewall")
            
        if "2. Sesión Autenticada" in failed_tests:
            print("❌ Problema de credenciales")
            print("💡 Solución: Verificar credenciales en .env o settings")
            
        if "3. Cliente Zeep CORREGIDO" in failed_tests:
            print("❌ Problema con zeep persiste")
            print("💡 Solución: Usar método de WSDL local o POST directo")
    
    # Recomendaciones
    print(f"\n{'='*60}")
    print("RECOMENDACIONES")
    print(f"{'='*60}")
    
    if "3. Cliente Zeep CORREGIDO" in successful_tests:
        print("🎯 Usar configuración zeep corregida en el proyecto")
        print("🎯 Aplicar timeouts más largos (120s)")
        print("🎯 Usar configuración de reintentos")
        
    elif "4. Cliente Zeep WSDL Local" in successful_tests:
        print("🎯 Usar estrategia de WSDL local")
        print("🎯 Descargar WSDL con autenticación antes de crear cliente")
        
    elif "5. Llamada SOAP" in successful_tests:
        print("🎯 La autenticación funciona para llamadas SOAP")
        print("🎯 Problema solo en carga de WSDL")
    
    print(f"\n{'='*60}")
    print("PRÓXIMOS PASOS")
    print(f"{'='*60}")
    
    if len(successful_tests) >= 3:
        print("1. ✅ Aplicar correcciones al SOAPClient del proyecto")
        print("2. ✅ Aumentar timeouts de conexión")
        print("3. ✅ Implementar manejo robusto de errores")
        print("4. ✅ Probar con documentos reales")
    else:
        print("1. ❌ Resolver problemas de conectividad básica")
        print("2. ❌ Verificar configuración de red/firewall")
        print("3. ❌ Contactar administrador de sistemas")
    
    return len(successful_tests) >= 3

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)