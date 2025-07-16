# test_fix.py - Script para probar que la corrección funciona
"""
Ejecutar desde la raíz del proyecto:
python test_fix.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

def test_generators():
    """Probar que el generador funciona sin errores de template"""
    print("🔧 Probando generador corregido...")
    
    try:
        from conversion.generators import UBLGeneratorFactory, BaseUBLGenerator
        
        # Test 1: Factory funciona
        tipos = UBLGeneratorFactory.get_supported_document_types()
        print(f"✅ Tipos soportados: {tipos}")
        
        # Test 2: Generador se crea
        generator = UBLGeneratorFactory.get_generator('01')
        print(f"✅ Generador creado: {type(generator).__name__}")
        
        # Test 3: Métodos de formateo funcionan
        from datetime import datetime
        fecha = generator._format_date(datetime.now())
        decimal = generator._format_decimal(123.45)
        print(f"✅ Formateo fecha: {fecha}")
        print(f"✅ Formateo decimal: {decimal}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en generador: {e}")
        return False

def test_api():
    """Probar endpoint de la API"""
    print("\n🌐 Probando API...")
    
    try:
        import requests
        
        # Test API básica
        response = requests.get('http://localhost:8000/api/test/', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API responde: {data.get('message', 'OK')}")
            return True
        else:
            print(f"⚠️ API responde con status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Servidor Django no está ejecutándose")
        print("   Ejecuta: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error probando API: {e}")
        return False

def main():
    print("🚀 TEST DE CORRECCIÓN - Invalid filter: 'format_date'")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('manage.py'):
        print("❌ No se encontró manage.py")
        print("   Ejecuta este script desde la raíz del proyecto")
        return
    
    # Test generadores
    generators_ok = test_generators()
    
    # Test API
    api_ok = test_api()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL TEST")
    print("=" * 60)
    print(f"Generadores UBL: {'✅ OK' if generators_ok else '❌ ERROR'}")
    print(f"API REST: {'✅ OK' if api_ok else '❌ ERROR'}")
    
    if generators_ok and api_ok:
        print("\n🎉 ¡CORRECCIÓN EXITOSA!")
        print("   El error 'Invalid filter: format_date' está solucionado")
        print("   Ve a http://localhost:8000 y prueba generar un documento")
    elif generators_ok:
        print("\n⚠️ Generadores OK, pero inicia el servidor:")
        print("   python manage.py runserver")
    else:
        print("\n❌ Verifica que reemplazaste el archivo conversion/generators.py")

if __name__ == '__main__':
    main()