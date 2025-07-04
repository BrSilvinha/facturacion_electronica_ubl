#!/usr/bin/env python
"""
Script para obtener UUID de empresa y generar JSON de prueba válido
Ubicación: get_empresa_uuid.py
"""

import os
import sys
import django
import json
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

def get_empresas_info():
    """Obtiene información de todas las empresas"""
    print("🏢 Obteniendo información de empresas...")
    
    try:
        from documentos.models import Empresa
        
        empresas = Empresa.objects.filter(activo=True)
        
        if not empresas.exists():
            print("   ⚠️  No hay empresas activas")
            return None
        
        print(f"   📊 Encontradas {empresas.count()} empresas activas:")
        
        empresas_info = []
        for i, empresa in enumerate(empresas, 1):
            info = {
                'id': str(empresa.id),
                'ruc': empresa.ruc,
                'razon_social': empresa.razon_social,
                'nombre_comercial': empresa.nombre_comercial or empresa.razon_social
            }
            empresas_info.append(info)
            
            print(f"   {i}. RUC: {empresa.ruc}")
            print(f"      ID: {empresa.id}")
            print(f"      Razón Social: {empresa.razon_social}")
            print()
        
        return empresas_info
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def create_valid_test_json():
    """Crea JSON de prueba con UUID real"""
    print("📝 Creando JSON de prueba válido...")
    
    empresas = get_empresas_info()
    
    if not empresas:
        print("   ❌ No se puede crear JSON sin empresas")
        return None
    
    # Usar la primera empresa
    empresa = empresas[0]
    
    test_data = {
        "tipo_documento": "01",
        "serie": "F001",
        "numero": 999,
        "fecha_emision": "2025-07-04",
        "moneda": "PEN",
        "empresa_id": empresa['id'],  # UUID real
        "receptor": {
            "tipo_doc": "6",
            "numero_doc": "20987654321",
            "razon_social": "CLIENTE DE PRUEBA SAC",
            "direccion": "AV. CLIENTE 456, LIMA"
        },
        "items": [
            {
                "descripcion": "Producto de prueba para facturación",
                "cantidad": 2,
                "valor_unitario": 50.00,
                "unidad_medida": "NIU",
                "afectacion_igv": "10",
                "codigo_producto": "PROD001"
            },
            {
                "descripcion": "Servicio de consultoría",
                "cantidad": 1,
                "valor_unitario": 100.00,
                "unidad_medida": "ZZ",
                "afectacion_igv": "10",
                "codigo_producto": "SERV001"
            }
        ]
    }
    
    print("   ✅ JSON creado con datos válidos")
    print(f"   🏢 Empresa: {empresa['razon_social']} (RUC: {empresa['ruc']})")
    
    return test_data

def save_test_json(test_data):
    """Guarda JSON de prueba en archivo"""
    if not test_data:
        return None
    
    try:
        output_file = Path('test_request.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 JSON guardado en: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"   ❌ Error guardando JSON: {e}")
        return None

def print_curl_command(test_data):
    """Imprime comando curl para probar"""
    if not test_data:
        return
    
    json_str = json.dumps(test_data, ensure_ascii=False)
    
    print("\n🌐 COMANDO CURL PARA PROBAR:")
    print("=" * 60)
    print("curl -X POST http://localhost:8000/api/generar-xml/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print(f"  -d '{json_str}'")
    print("=" * 60)

def print_postman_instructions(test_data):
    """Imprime instrucciones para Postman"""
    if not test_data:
        return
    
    print("\n📮 INSTRUCCIONES PARA POSTMAN:")
    print("=" * 60)
    print("1. Método: POST")
    print("2. URL: http://localhost:8000/api/generar-xml/")
    print("3. Headers:")
    print("   Content-Type: application/json")
    print("4. Body (raw JSON):")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    print("=" * 60)

def test_api_directly():
    """Prueba la API directamente desde Python"""
    print("\n🧪 PROBANDO API DIRECTAMENTE...")
    
    try:
        test_data = create_valid_test_json()
        if not test_data:
            return False
        
        from api_rest.views import GenerarXMLView
        from rest_framework.test import APIRequestFactory
        
        # Crear request
        factory = APIRequestFactory()
        request = factory.post(
            '/api/generar-xml/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        # Ejecutar vista
        view = GenerarXMLView()
        response = view.post(request)
        
        print(f"   📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ ¡API FUNCIONANDO CORRECTAMENTE!")
            
            # Mostrar información del resultado
            if hasattr(response, 'data'):
                data = response.data
                print(f"   📄 Documento: {data.get('numero_completo', 'N/A')}")
                print(f"   💰 Total: S/ {data.get('totales', {}).get('total_precio_venta', 'N/A')}")
                print(f"   ⏱️  Tiempo: {data.get('processing_time_ms', 'N/A')} ms")
                print(f"   🔐 Hash: {data.get('hash', 'N/A')[:16]}...")
            
            return True
        else:
            print(f"   ❌ Error en API:")
            if hasattr(response, 'data'):
                print(f"   {response.data}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🔍 OBTENIENDO UUID DE EMPRESA Y CREANDO PRUEBAS")
    print("=" * 60)
    
    # Obtener empresas
    empresas = get_empresas_info()
    
    if not empresas:
        print("\n❌ NO HAY EMPRESAS DISPONIBLES")
        print("Ejecuta: python manage.py shell")
        print(">>> from documentos.models import *")
        print(">>> empresa = Empresa.objects.create(")
        print("...     ruc='20123456789',")
        print("...     razon_social='EMPRESA TEST SAC',")
        print("...     direccion='AV. TEST 123'")
        print("... )")
        return 1
    
    # Crear JSON de prueba
    test_data = create_valid_test_json()
    
    # Guardar JSON
    save_test_json(test_data)
    
    # Mostrar instrucciones
    print_curl_command(test_data)
    print_postman_instructions(test_data)
    
    # Probar API directamente
    if test_api_directly():
        print("\n🎉 ¡TODO FUNCIONANDO CORRECTAMENTE!")
        print("\n📝 Próximos pasos:")
        print("1. Usa el JSON generado en Postman")
        print("2. O usa el comando curl mostrado arriba")
        print("3. El archivo test_request.json tiene el JSON válido")
        return 0
    else:
        print("\n⚠️  API con problemas, pero JSON generado correctamente")
        return 1

if __name__ == '__main__':
    exit(main())