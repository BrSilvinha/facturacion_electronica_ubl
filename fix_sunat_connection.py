#!/usr/bin/env python
"""
Script para corregir problemas de conexión SUNAT
Ejecutar: python fix_sunat_connection.py
VERSIÓN CORREGIDA - Sin errores de encoding
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    exit(1)

def verificar_env():
    """Verifica archivo .env con manejo de encoding mejorado"""
    
    print("📝 Verificando archivo .env...")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ Archivo .env no encontrado")
        print("📋 Creando archivo .env...")
        crear_env_file()
        return True
    
    try:
        # Intentar múltiples encodings
        encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin1']
        env_content = None
        
        for encoding in encodings:
            try:
                with open(env_file, 'r', encoding=encoding) as f:
                    env_content = f.read()
                print(f"✅ Archivo .env leído con encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if env_content is None:
            print("❌ No se pudo leer el archivo .env")
            print("📋 Recreando archivo .env...")
            crear_env_file()
            return True
        
        # Verificar variables requeridas
        required_vars = [
            'SUNAT_ENVIRONMENT=beta',
            'SUNAT_RUC=20123456789',
            'SUNAT_BETA_USER=MODDATOS',
            'SUNAT_BETA_PASSWORD=MODDATOS'
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in env_content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Variables faltantes: {missing_vars}")
            print("📋 Corrigiendo archivo .env...")
            crear_env_file()
            return True
        
        print("✅ Archivo .env correcto")
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo .env: {e}")
        print("📋 Recreando archivo .env...")
        crear_env_file()
        return True

def crear_env_file():
    """Crea archivo .env correcto"""
    
    env_content = """# Configuración existente
DB_NAME=facturacion_electronica_db
DB_USER=facturacion_user
DB_PASSWORD=facturacion123
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=tu-clave-secreta-super-segura-para-facturacion-electronica-2025
DEBUG=True

# === CONFIGURACION SUNAT CORREGIDA ===
# Ambiente (beta o production)
SUNAT_ENVIRONMENT=beta

# RUC de tu empresa (DEBE SER 11 DIGITOS)
SUNAT_RUC=20123456789

# Credenciales SUNAT Beta (EXACTAS - CASE SENSITIVE)
SUNAT_BETA_USER=MODDATOS
SUNAT_BETA_PASSWORD=MODDATOS

# Credenciales SUNAT Produccion
SUNAT_PROD_USER=
SUNAT_PROD_PASSWORD=

# URLs de Servicios SUNAT (CORREGIDAS SIN PARAMETROS EXTRA)
SUNAT_BETA_WSDL_FACTURA=https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl
SUNAT_BETA_WSDL_GUIA=https://e-beta.sunat.gob.pe/ol-ti-itemision-guia-gem-beta/billService?wsdl
SUNAT_BETA_WSDL_RETENCION=https://e-beta.sunat.gob.pe/ol-ti-itemision-otroscpe-gem-beta/billService?wsdl

SUNAT_PROD_WSDL_FACTURA=https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService?wsdl
SUNAT_PROD_WSDL_GUIA=https://e-guiaremision.sunat.gob.pe/ol-ti-itemision-guiagem/billService?wsdl
SUNAT_PROD_WSDL_RETENCION=https://e-factura.sunat.gob.pe/ol-ti-itemision-otroscpe-gem/billService?wsdl

# Configuracion adicional
SUNAT_TIMEOUT=120
SUNAT_MAX_RETRIES=3
SUNAT_ENABLE_LOGGING=True"""

    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Archivo .env creado/corregido")
        return True
    except Exception as e:
        print(f"❌ Error creando .env: {e}")
        return False

def verificar_configuracion():
    """Verifica y corrige la configuración SUNAT"""
    
    print("\n🔍 Verificando configuración SUNAT...")
    
    try:
        from django.conf import settings
        config = settings.SUNAT_CONFIG
        
        print(f"✅ Ambiente: {config['ENVIRONMENT']}")
        print(f"✅ RUC: {config['RUC']}")
        print(f"✅ Usuario Beta: {config['BETA_USER']}")
        print(f"✅ Password Beta: {config['BETA_PASSWORD']}")
        
        # Verificar URLs
        wsdl_urls = config['WSDL_URLS']['beta']
        print(f"✅ WSDL Factura: {wsdl_urls['factura']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

def probar_credenciales():
    """Prueba las credenciales SUNAT"""
    
    print("\n🔐 Probando credenciales SUNAT...")
    
    try:
        from sunat_integration.utils import get_sunat_credentials
        
        credentials = get_sunat_credentials('beta')
        username_completo = f"{credentials['ruc']}{credentials['username']}"
        
        print(f"✅ RUC: {credentials['ruc']}")
        print(f"✅ Usuario base: {credentials['username']}")
        print(f"✅ Username completo: {username_completo}")
        print(f"✅ Password: {'*' * len(credentials['password'])}")
        
        # Validar formato
        if len(credentials['ruc']) != 11:
            print(f"❌ RUC debe tener 11 dígitos, tiene {len(credentials['ruc'])}")
            return False
            
        if credentials['username'] != 'MODDATOS':
            print(f"❌ Usuario debe ser 'MODDATOS', es '{credentials['username']}'")
            return False
            
        if credentials['password'] != 'MODDATOS':
            print(f"❌ Password debe ser 'MODDATOS'")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando credenciales: {e}")
        return False

def probar_wsdl():
    """Prueba acceso al WSDL de SUNAT"""
    
    print("\n🌐 Probando acceso WSDL...")
    
    try:
        import requests
        from sunat_integration.utils import get_wsdl_url
        
        wsdl_url = get_wsdl_url('factura', 'beta')
        print(f"📡 Probando: {wsdl_url}")
        
        response = requests.get(wsdl_url, timeout=30)
        
        if response.status_code == 200:
            print("✅ WSDL accesible")
            if 'wsdl:definitions' in response.text:
                print("✅ WSDL válido")
                return True
            else:
                print("❌ WSDL inválido")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error accediendo WSDL: {e}")
        return False

def crear_cliente_sunat():
    """Crea y prueba cliente SUNAT"""
    
    print("\n🔧 Creando cliente SUNAT...")
    
    try:
        from sunat_integration.soap_client import SUNATSoapClient
        
        # Crear cliente sin lazy loading
        client = SUNATSoapClient('factura', 'beta', lazy_init=False)
        
        if client._initialized:
            print("✅ Cliente SOAP inicializado")
            
            # Probar test_connection
            result = client.test_connection()
            
            if result['success']:
                print("✅ Test de conexión exitoso")
                print(f"   Username configurado: {result['service_info']['username_configured']}")
                return True
            else:
                print(f"❌ Test de conexión falló: {result['error']}")
                print(f"   Tipo error: {result.get('error_type', 'No especificado')}")
                return False
        else:
            print("❌ Cliente no se pudo inicializar")
            return False
            
    except Exception as e:
        print(f"❌ Error creando cliente: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_modulos():
    """Verifica que los módulos estén disponibles"""
    
    print("\n📦 Verificando módulos...")
    
    try:
        import zeep
        print("✅ zeep disponible")
    except ImportError:
        print("❌ zeep no disponible - Instalar: pip install zeep")
        return False
    
    try:
        import requests
        print("✅ requests disponible")
    except ImportError:
        print("❌ requests no disponible - Instalar: pip install requests")
        return False
    
    try:
        from sunat_integration import get_sunat_client
        print("✅ sunat_integration disponible")
    except ImportError as e:
        print(f"❌ sunat_integration no disponible: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    
    print("🚀 Script de Corrección SUNAT")
    print("=" * 50)
    
    all_ok = True
    
    # 1. Verificar módulos
    if not verificar_modulos():
        print("\n❌ Faltan módulos requeridos")
        print("Ejecuta: pip install zeep requests urllib3")
        all_ok = False
    
    # 2. Verificar .env
    if not verificar_env():
        print("\n❌ Problema con archivo .env")
        all_ok = False
    
    # 3. Verificar configuración Django
    if not verificar_configuracion():
        print("\n❌ Problema con configuración Django")
        all_ok = False
    
    # 4. Probar credenciales
    if not probar_credenciales():
        print("\n❌ Problema con credenciales")
        all_ok = False
    
    # 5. Probar WSDL
    if not probar_wsdl():
        print("\n❌ Problema accediendo WSDL")
        all_ok = False
    
    # 6. Probar cliente SUNAT
    if not crear_cliente_sunat():
        print("\n❌ Problema con cliente SUNAT")
        all_ok = False
    
    print("\n" + "=" * 50)
    
    if all_ok:
        print("🎉 ¡TODO CORRECTO!")
        print("✅ Reinicia el servidor Django: python manage.py runserver")
        print("✅ Prueba el endpoint: GET /api/sunat/test-connection/")
        
        print("\n📋 Comandos para probar:")
        print("1. GET  /api/sunat/test-connection/")
        print("2. POST /api/generar-xml/ (con datos válidos)")
        print("3. POST /api/sunat/send-bill/ (con documento_id)")
        
    else:
        print("❌ HAY PROBLEMAS QUE CORREGIR")
        print("📋 Revisa los errores mostrados arriba")
        
        print("\n🔧 Pasos recomendados:")
        print("1. Verifica que tengas: pip install zeep requests urllib3")
        print("2. Reinicia el servidor: python manage.py runserver")
        print("3. Ejecuta este script nuevamente")
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    exit(main())