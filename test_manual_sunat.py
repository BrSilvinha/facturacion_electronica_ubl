#!/usr/bin/env python
"""
Prueba manual rápida de credenciales SUNAT
Ejecutar: python test_manual_sunat.py
"""

import requests
from requests.auth import HTTPBasicAuth

def test_manual_credentials():
    print("🔐 PRUEBA MANUAL DE CREDENCIALES SUNAT")
    print("=" * 50)
    
    # Credenciales reales
    ruc = "20103129061"
    username = "MODDATOS"
    password = "MODDATOS"
    
    # Usuario completo
    full_username = f"{ruc}{username}"
    
    print(f"RUC: {ruc}")
    print(f"Usuario: {username}")
    print(f"Usuario completo: {full_username}")
    print(f"Password: {'*' * len(password)}")
    
    # URL WSDL
    wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
    
    print(f"\n🌐 Probando: {wsdl_url}")
    
    try:
        # Sin autenticación
        print("\n1. Sin autenticación...")
        response = requests.get(wsdl_url, timeout=30)
        print(f"   Status: {response.status_code}")
        
        # Con autenticación
        print("\n2. Con autenticación...")
        session = requests.Session()
        session.auth = HTTPBasicAuth(full_username, password)
        
        response = session.get(wsdl_url, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ CREDENCIALES CORRECTAS")
            return True
        elif response.status_code == 401:
            print("   ❌ CREDENCIALES INCORRECTAS")
            
            # Probar variantes
            print("\n3. Probando variantes...")
            variants = [
                username,
                f"{ruc}-{username}",
                f"{username}{ruc}"
            ]
            
            for variant in variants:
                print(f"   Probando: {variant}")
                session.auth = HTTPBasicAuth(variant, password)
                resp = session.get(wsdl_url, timeout=15)
                print(f"   Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"   ✅ FUNCIONA CON: {variant}")
                    return True
        
        return False
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = test_manual_credentials()
    
    if success:
        print("\n🎉 ¡Credenciales funcionan!")
        print("💡 El problema puede estar en zeep o en la configuración Django")
    else:
        print("\n❌ Credenciales no funcionan")
        print("💡 Contacta a tu ingeniero para verificar:")
        print("   - RUC: 20103129061")
        print("   - Usuario: MODDATOS") 
        print("   - Password: MODDATOS")
        print("   - Acceso al ambiente Beta")
    
    input("\nPresiona Enter para continuar...")