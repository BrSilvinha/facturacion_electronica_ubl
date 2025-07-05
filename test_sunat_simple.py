#!/usr/bin/env python
"""
Prueba básica de conectividad SUNAT
Ejecutar: python test_sunat_simple.py
"""

import os
import sys
import requests
from pathlib import Path

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
                print(f"Contenido: {response.text[:500]}...")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Contenido: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error accediendo WSDL: {e}")
        return False

def test_zeep_client():
    """Prueba creación de cliente zeep básico"""
    print("\n🔧 Probando cliente zeep básico...")
    
    try:
        from zeep import Client
        from zeep.transports import Transport
        from zeep.wsse.username import UsernameToken
        from requests import Session
        
        # Crear sesión simple
        session = Session()
        transport = Transport(session=session, timeout=30)
        
        wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
        
        # Crear cliente sin autenticación primero
        client = Client(wsdl_url, transport=transport)
        print("✅ Cliente zeep creado exitosamente")
        
        # Agregar autenticación WS-Security
        username = "20123456789MODDATOS"
        password = "MODDATOS"
        
        wsse = UsernameToken(username=username, password=password)
        client.wsse = wsse
        
        print("✅ Autenticación WS-Security configurada")
        
        # Verificar operaciones disponibles
        if hasattr(client, 'service'):
            operations = [op for op in dir(client.service) if not op.startswith('_')]
            print(f"✅ Operaciones disponibles: {operations}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando cliente zeep: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_soap_call():
    """Prueba llamada SOAP básica"""
    print("\n📞 Probando llamada SOAP...")
    
    try:
        from zeep import Client
        from zeep.transports import Transport
        from zeep.wsse.username import UsernameToken
        from requests import Session
        import base64
        
        # Crear cliente
        session = Session()
        transport = Transport(session=session, timeout=30)
        
        wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
        client = Client(wsdl_url, transport=transport)
        
        # Configurar autenticación
        username = "20123456789MODDATOS"
        password = "MODDATOS"
        wsse = UsernameToken(username=username, password=password)
        client.wsse = wsse
        
        # Preparar datos dummy
        dummy_zip = base64.b64encode(b"PK\x03\x04\x14\x00\x00\x00\x00\x00test").decode('utf-8')
        
        print(f"Enviando con usuario: {username}")
        print(f"Tamaño ZIP: {len(dummy_zip)} chars")
        
        # Intentar llamada
        response = client.service.sendBill(
            fileName="test.zip",
            contentFile=dummy_zip
        )
        
        print(f"✅ Respuesta recibida: {response}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error en llamada SOAP: {error_msg}")
        
        # Analizar el tipo de error
        if '401' in error_msg or 'authentication' in error_msg.lower():
            print("❌ Error de autenticación - Revisar credenciales")
        elif 'validation' in error_msg.lower() or 'invalid' in error_msg.lower():
            print("✅ Autenticación OK - Error de validación (esperado con datos dummy)")
            return True
        else:
            print(f"❌ Otro error: {error_msg}")
        
        return False

def main():
    """Función principal"""
    print("🚀 Prueba Simple SUNAT")
    print("=" * 50)
    
    # Verificar configuración
    try:
        from django.conf import settings
        print(f"✅ Django configurado")
        print(f"✅ RUC: {settings.SUNAT_CONFIG['RUC']}")
        print(f"✅ Ambiente: {settings.SUNAT_CONFIG['ENVIRONMENT']}")
        print(f"✅ Usuario: {settings.SUNAT_CONFIG['BETA_USER']}")
    except Exception as e:
        print(f"❌ Error configuración Django: {e}")
        return False
    
    # Ejecutar pruebas
    tests = [
        ("Acceso WSDL", test_wsdl_access),
        ("Cliente Zeep", test_zeep_client),
        ("Llamada SOAP", test_soap_call)
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
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 ¡Todas las pruebas pasaron!")
        print("✅ Puedes proceder con la integración completa")
    else:
        print("\n⚠️ Algunas pruebas fallaron")
        print("📋 Revisa los errores mostrados arriba")
    
    return all_passed

if __name__ == '__main__':
    main()