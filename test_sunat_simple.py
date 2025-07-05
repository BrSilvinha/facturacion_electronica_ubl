#!/usr/bin/env python
"""
Prueba mejorada de conectividad SUNAT
Maneja mejor la autenticación y configuración
Ejecutar: python test_sunat_enhanced.py
"""

import os
import sys
import requests
from pathlib import Path
import base64

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
                    return True
                elif response.status_code == 401:
                    print(f"  ❌ Credenciales incorrectas")
                else:
                    print(f"  ⚠️ Código: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Error configurando sesión: {e}")
        return False

def test_zeep_with_auth():
    """Prueba cliente zeep con autenticación mejorada"""
    print("\n🔧 Probando cliente zeep con autenticación...")
    
    try:
        from zeep import Client, Settings
        from zeep.transports import Transport
        from zeep.wsse.username import UsernameToken
        from requests import Session
        from requests.auth import HTTPBasicAuth
        
        # Credenciales
        username = "20123456789MODDATOS"
        password = "MODDATOS"
        
        # Configurar sesión con autenticación HTTP Y WS-Security
        session = Session()
        session.auth = HTTPBasicAuth(username, password)
        
        # Headers adicionales
        session.headers.update({
            'User-Agent': 'Python-SUNAT/1.0',
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        })
        
        # Configurar transporte
        transport = Transport(session=session, timeout=60)
        
        # Configurar settings para ser más permisivo
        settings = Settings(strict=False, xml_huge_tree=True)
        
        # URL del WSDL
        wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
        
        print(f"Creando cliente con:")
        print(f"  Usuario: {username}")
        print(f"  WSDL: {wsdl_url}")
        
        # Crear cliente
        client = Client(wsdl_url, transport=transport, settings=settings)
        print("✅ Cliente zeep creado exitosamente")
        
        # Agregar WS-Security
        wsse = UsernameToken(username=username, password=password)
        client.wsse = wsse
        print("✅ WS-Security configurado")
        
        # Verificar operaciones
        if hasattr(client, 'service'):
            operations = [op for op in dir(client.service) if not op.startswith('_')]
            print(f"✅ Operaciones disponibles: {operations}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando cliente zeep: {e}")
        
        # Análisis del error
        error_msg = str(e)
        if '401' in error_msg:
            print("💡 Error 401: Problema de autenticación")
            print("   - Verificar credenciales SUNAT")
            print("   - Verificar formato de usuario (RUC + usuario)")
        elif 'timeout' in error_msg.lower():
            print("💡 Error de timeout: Conexión lenta")
        elif 'ssl' in error_msg.lower():
            print("💡 Error SSL: Problema de certificados")
        
        return False

def test_soap_call_advanced():
    """Prueba llamada SOAP con manejo avanzado"""
    print("\n📞 Probando llamada SOAP avanzada...")
    
    try:
        from zeep import Client, Settings
        from zeep.transports import Transport
        from zeep.wsse.username import UsernameToken
        from requests import Session
        from requests.auth import HTTPBasicAuth
        
        # Credenciales
        username = "20123456789MODDATOS"
        password = "MODDATOS"
        
        # Configurar sesión
        session = Session()
        session.auth = HTTPBasicAuth(username, password)
        
        # Configurar transporte y settings
        transport = Transport(session=session, timeout=60)
        settings = Settings(strict=False, xml_huge_tree=True)
        
        # Crear cliente
        wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
        client = Client(wsdl_url, transport=transport, settings=settings)
        
        # Configurar WS-Security
        wsse = UsernameToken(username=username, password=password)
        client.wsse = wsse
        
        # Crear ZIP dummy más realista
        dummy_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
    <ID>F001-00000001</ID>
</Invoice>'''
        
        # Simular un ZIP real
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("20123456789-01-F001-00000001.xml", dummy_xml)
        
        zip_content = zip_buffer.getvalue()
        zip_base64 = base64.b64encode(zip_content).decode('utf-8')
        
        print(f"Enviando ZIP de {len(zip_content)} bytes")
        print(f"Base64: {len(zip_base64)} chars")
        
        # Intentar llamada
        response = client.service.sendBill(
            fileName="20123456789-01-F001-00000001.zip",
            contentFile=zip_base64
        )
        
        print(f"✅ Respuesta recibida: {type(response)}")
        print(f"✅ Llamada SOAP exitosa")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error en llamada SOAP: {error_msg}")
        
        # Análisis del error
        if '401' in error_msg or 'authentication' in error_msg.lower():
            print("❌ Error de autenticación")
        elif 'validation' in error_msg.lower() or 'invalid' in error_msg.lower():
            print("✅ Autenticación OK - Error de validación (esperado)")
            return True
        elif 'timeout' in error_msg.lower():
            print("⏱️ Timeout - Servidor lento")
        
        return False

def test_direct_post():
    """Prueba POST directo al servicio"""
    print("\n📤 Probando POST directo...")
    
    try:
        from requests.auth import HTTPBasicAuth
        
        # Credenciales
        username = "20123456789MODDATOS"
        password = "MODDATOS"
        
        # URL del servicio
        service_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService"
        
        # SOAP envelope básico
        soap_envelope = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:ser="http://service.sunat.gob.pe">
    <soap:Header>
        <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
            <wsse:UsernameToken>
                <wsse:Username>{username}</wsse:Username>
                <wsse:Password>{password}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soap:Header>
    <soap:Body>
        <ser:sendBill>
            <fileName>test.zip</fileName>
            <contentFile>UEsDBBQAAAAIAA==</contentFile>
        </ser:sendBill>
    </soap:Body>
</soap:Envelope>'''.format(username=username, password=password)
        
        # Headers
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'urn:sendBill',
            'User-Agent': 'Python-SUNAT/1.0'
        }
        
        # Crear sesión
        session = requests.Session()
        session.auth = HTTPBasicAuth(username, password)
        
        print(f"Enviando POST a: {service_url}")
        print(f"Con usuario: {username}")
        
        response = session.post(
            service_url,
            data=soap_envelope,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ POST exitoso")
            print(f"Respuesta: {response.text[:500]}...")
            return True
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en POST: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Prueba Mejorada SUNAT")
    print("=" * 50)
    
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
    
    # Ejecutar pruebas
    tests = [
        ("Acceso WSDL", test_wsdl_access),
        ("Sesión Autenticada", test_authenticated_session),
        ("Cliente Zeep", test_zeep_with_auth),
        ("Llamada SOAP", test_soap_call_advanced),
        ("POST Directo", test_direct_post)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"EJECUTANDO: {name}")
        print(f"{'='*50}")
        
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
    
    # Resumen
    print(f"\n{'='*50}")
    print("RESUMEN DE PRUEBAS")
    print(f"{'='*50}")
    
    for name, result in results:
        status = "✅ EXITOSO" if result else "❌ FALLIDO"
        print(f"{name}: {status}")
    
    # Diagnóstico
    print(f"\n{'='*50}")
    print("DIAGNÓSTICO")
    print(f"{'='*50}")
    
    successful_tests = [name for name, result in results if result]
    failed_tests = [name for name, result in results if not result]
    
    if len(successful_tests) == len(tests):
        print("🎉 ¡Todas las pruebas pasaron!")
        print("✅ Conexión SUNAT completamente funcional")
    elif "Acceso WSDL" in successful_tests:
        print("✅ Conectividad básica OK")
        if "Sesión Autenticada" in failed_tests:
            print("❌ Problema de autenticación HTTP")
            print("💡 Verificar credenciales en .env")
        if "Cliente Zeep" in failed_tests:
            print("❌ Problema con cliente SOAP")
            print("💡 Posible problema de configuración zeep")
    else:
        print("❌ Problemas de conectividad básica")
        print("💡 Verificar conexión de red y URLs")
    
    return len(failed_tests) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)