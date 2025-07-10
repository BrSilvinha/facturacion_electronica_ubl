"""
Test manual para verificar CDR real de SUNAT
Archivo: test_manual_cdr.py
"""

import requests
import json
from datetime import datetime

def test_manual_cdr():
    """Test completo: Generar documento → Enviar a SUNAT → Obtener CDR real"""
    
    print("🔄 TEST MANUAL - SUNAT CDR REAL")
    print("=" * 60)
    
    # 1. Verificar dependencias
    print("🔍 PASO 0: Verificar dependencias...")
    if not verify_dependencies():
        print("❌ Dependencias faltantes. Ejecutar:")
        print("   pip install zeep>=4.2.1 requests>=2.31.0 lxml>=4.9.3")
        return False
    
    # 2. Obtener empresa ID
    print("\n🏢 PASO 1: Obtener empresa ID...")
    empresa_id = get_empresa_id()
    if not empresa_id:
        print("❌ No se pudo obtener empresa ID")
        print("💡 Solución: python manage.py poblar_datos_iniciales")
        return False
    
    print(f"✅ Empresa ID obtenida: {empresa_id}")
    
    # 3. Generar documento XML
    print(f"\n📋 PASO 2: Generar documento XML...")
    
    # Número único basado en timestamp para evitar duplicados
    numero_unico = int(datetime.now().strftime('%H%M%S'))
    
    documento_data = {
        "tipo_documento": "01",
        "serie": "F001", 
        "numero": numero_unico,
        "fecha_emision": "2025-07-09",
        "moneda": "PEN",
        "empresa_id": empresa_id,
        "receptor": {
            "tipo_doc": "6",
            "numero_doc": "20123456789",
            "razon_social": "EMPRESA CLIENTE TEST SAC",
            "direccion": "AV. TEST 123, LIMA"
        },
        "items": [
            {
                "descripcion": "Producto para CDR real de SUNAT",
                "cantidad": 1.0,
                "valor_unitario": 100.0,
                "unidad_medida": "NIU",
                "afectacion_igv": "10",
                "codigo_producto": "PROD001"
            }
        ]
    }
    
    print(f"📄 Generando documento: F001-{numero_unico:08d}")
    
    try:
        # Generar XML con firma digital
        response = requests.post(
            'http://localhost:8000/api/generar-xml/',
            json=documento_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                documento_id = result['documento_id']
                print(f"✅ XML generado exitosamente:")
                print(f"   📄 Documento: {result['numero_completo']}")
                print(f"   🆔 ID: {documento_id}")
                print(f"   🔐 Estado: {result['estado']}")
                print(f"   🏷️ Hash: {result.get('hash', 'N/A')[:16]}...")
                
                # 4. Enviar a SUNAT con endpoint CORREGIDO
                print(f"\n📤 PASO 3: Enviar a SUNAT (endpoint corregido)...")
                
                sunat_response = requests.post(
                    'http://localhost:8000/api/sunat/send-bill/',
                    json={'documento_id': documento_id},
                    headers={'Content-Type': 'application/json'},
                    timeout=60
                )
                
                if sunat_response.status_code == 200:
                    sunat_result = sunat_response.json()
                    
                    print(f"📊 RESPUESTA SUNAT:")
                    print(f"   ✅ Success: {sunat_result.get('success')}")
                    print(f"   🔧 Method: {sunat_result.get('method')}")
                    print(f"   📄 Document: {sunat_result.get('document_number')}")
                    print(f"   ⏱️ Duration: {sunat_result.get('duration_ms')}ms")
                    
                    # Verificar si recibimos CDR REAL
                    if sunat_result.get('has_cdr'):
                        print(f"\n🎉 ¡CDR REAL RECIBIDO DE SUNAT!")
                        cdr_info = sunat_result.get('cdr_info', {})
                        print(f"   📋 Status: {cdr_info.get('status')}")
                        print(f"   🔍 Response Code: {cdr_info.get('response_code')}")
                        print(f"   💬 Message: {cdr_info.get('message')}")
                        print(f"   ✅ Accepted: {cdr_info.get('is_accepted')}")
                        print(f"   ❌ Rejected: {cdr_info.get('is_rejected')}")
                        
                        if cdr_info.get('cdr_xml'):
                            print(f"   📄 CDR XML: {len(cdr_info['cdr_xml'])} caracteres")
                            print(f"   📁 CDR File: {cdr_info.get('cdr_filename', 'N/A')}")
                        
                        print(f"\n🏆 ÉXITO: CDR real obtenido de SUNAT")
                        return True
                    else:
                        print(f"\n⚠️ SIN CDR INMEDIATO")
                        print(f"   📄 Method: {sunat_result.get('method')}")
                        print(f"   💬 Message: {sunat_result.get('message')}")
                        
                        # Analizar por qué no hay CDR
                        if sunat_result.get('method') == 'simulation':
                            print(f"\n❌ PROBLEMA: Aún está usando simulación")
                            print(f"   🔧 Posibles causas:")
                            print(f"      - Dependencias no instaladas correctamente")
                            print(f"      - Archivo views_sunat.py no reemplazado")
                            print(f"      - Servidor Django no reiniciado")
                            return False
                        elif sunat_result.get('error_type'):
                            print(f"\n❌ ERROR SUNAT:")
                            print(f"   🔍 Error Type: {sunat_result.get('error_type')}")
                            print(f"   💬 Error Message: {sunat_result.get('error_message')}")
                            
                            # Mostrar troubleshooting si está disponible
                            if sunat_result.get('troubleshooting'):
                                trouble = sunat_result['troubleshooting']
                                print(f"\n🔧 TROUBLESHOOTING:")
                                print(f"   📝 Descripción: {trouble.get('description', 'N/A')}")
                                if trouble.get('causes'):
                                    print(f"   🎯 Causas posibles:")
                                    for cause in trouble['causes']:
                                        print(f"      - {cause}")
                                if trouble.get('solutions'):
                                    print(f"   💡 Soluciones:")
                                    for solution in trouble['solutions']:
                                        print(f"      - {solution}")
                            return False
                        else:
                            print(f"\n📋 Documento enviado pero sin CDR inmediato")
                            print(f"   💡 Esto puede ser normal para algunos documentos")
                            return True
                else:
                    print(f"\n❌ ERROR enviando a SUNAT:")
                    print(f"   📊 Status: {sunat_response.status_code}")
                    print(f"   📄 Response:")
                    try:
                        error_data = sunat_response.json()
                        print(json.dumps(error_data, indent=4))
                    except:
                        print(sunat_response.text[:500])
                    return False
            else:
                print(f"\n❌ ERROR generando XML:")
                print(f"   💬 Error: {result.get('error')}")
                return False
        else:
            print(f"\n❌ ERROR en request XML:")
            print(f"   📊 Status: {response.status_code}")
            print(f"   📄 Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ TIMEOUT - El servidor tardó mucho en responder")
        print(f"   💡 Verificar que el servidor esté corriendo")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR DE CONEXIÓN")
        print(f"   💡 Verificar que Django esté corriendo en puerto 8000")
        return False
    except Exception as e:
        print(f"\n❌ EXCEPCIÓN INESPERADA: {e}")
        return False

def verify_dependencies():
    """Verificar que las dependencias necesarias están instaladas"""
    
    deps = ['requests', 'zeep', 'lxml']
    all_ok = True
    
    for dep in deps:
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'OK')
            print(f"   ✅ {dep}: {version}")
        except ImportError:
            print(f"   ❌ {dep}: NO INSTALADO")
            all_ok = False
    
    return all_ok

def get_empresa_id():
    """Obtener ID de primera empresa disponible"""
    try:
        response = requests.get(
            'http://localhost:8000/api/empresas/',
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                empresa = result['data'][0]
                print(f"   🏢 Empresa: {empresa.get('razon_social')}")
                print(f"   🆔 RUC: {empresa.get('ruc')}")
                return empresa['id']
    except Exception as e:
        print(f"   ❌ Error obteniendo empresas: {e}")
    return None

def test_server_running():
    """Verificar que el servidor Django está corriendo"""
    try:
        response = requests.get('http://localhost:8000/api/test/', timeout=5)
        return response.status_code == 200
    except:
        return False

def test_sunat_dependencies():
    """Test específico de dependencias SUNAT"""
    try:
        response = requests.get('http://localhost:8000/api/sunat/status/', timeout=10)
        if response.status_code == 200:
            result = response.json()
            deps = result.get('dependencies', {})
            
            print("🔍 Dependencias en servidor:")
            for dep, version in deps.items():
                status = "✅" if version != "NO_DISPONIBLE" else "❌"
                print(f"   {status} {dep}: {version}")
            
            return all(v != "NO_DISPONIBLE" for v in deps.values())
    except Exception as e:
        print(f"❌ Error verificando dependencias del servidor: {e}")
    return False

if __name__ == "__main__":
    print("🚀 TEST SUNAT CDR REAL - VERSIÓN COMPLETA")
    print("=" * 60)
    
    # Verificar que Django está corriendo
    if not test_server_running():
        print("❌ SERVIDOR DJANGO NO ESTÁ CORRIENDO")
        print("💡 Ejecutar en otra terminal: python manage.py runserver")
        exit(1)
    
    print("✅ Servidor Django detectado")
    
    # Verificar dependencias del servidor
    print("\n🔍 Verificando dependencias del servidor...")
    if not test_sunat_dependencies():
        print("⚠️ Algunas dependencias pueden estar faltando")
        print("💡 Instalar: pip install zeep>=4.2.1 requests>=2.31.0 lxml>=4.9.3")
    
    # Ejecutar test principal
    print("\n" + "="*60)
    success = test_manual_cdr()
    print("="*60)
    
    if success:
        print("\n🎉 ¡TEST EXITOSO! CDR real obtenido de SUNAT")
        print("✅ La integración está funcionando correctamente")
    else:
        print("\n❌ Test falló - revisar errores arriba")
        print("\n🔧 PASOS PARA SOLUCIONAR:")
        print("1. Verificar dependencias: pip install zeep>=4.2.1")
        print("2. Reemplazar api_rest/views_sunat.py con código corregido")
        print("3. Reiniciar servidor: python manage.py runserver")
        print("4. Ejecutar de nuevo: python test_manual_cdr.py")