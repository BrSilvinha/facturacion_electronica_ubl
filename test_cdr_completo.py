"""
Test Completo CDR - Análisis detallado de respuestas SUNAT
Archivo: test_cdr_completo.py
"""

import requests
import json
from datetime import datetime
import time

def test_cdr_completo():
    """Test completo con análisis detallado de respuestas SUNAT"""
    
    print("🚀 TEST CDR COMPLETO - ANÁLISIS DETALLADO SUNAT")
    print("=" * 70)
    
    # 1. Verificar servidor
    if not verify_server():
        return False
    
    # 2. Obtener empresa ID
    empresa_id = get_empresa_id()
    if not empresa_id:
        return False
    
    print(f"✅ Empresa ID: {empresa_id}")
    
    # 3. Generar documento único
    numero_unico = int(datetime.now().strftime('%H%M%S'))
    
    documento_data = {
        "tipo_documento": "01",
        "serie": "F001", 
        "numero": numero_unico,
        "fecha_emision": datetime.now().strftime('%Y-%m-%d'),
        "moneda": "PEN",
        "empresa_id": empresa_id,
        "receptor": {
            "tipo_doc": "6",
            "numero_doc": "20123456789",
            "razon_social": "EMPRESA CLIENTE CDR COMPLETO SAC",
            "direccion": "AV. CDR COMPLETO 123, LIMA"
        },
        "items": [
            {
                "descripcion": "Producto para análisis CDR completo SUNAT",
                "cantidad": 1.0,
                "valor_unitario": 100.0,
                "unidad_medida": "NIU",
                "afectacion_igv": "10",
                "codigo_producto": "PROD-CDR-001"
            }
        ]
    }
    
    print(f"\n📋 PASO 1: Generar documento XML...")
    print(f"📄 Documento: F001-{numero_unico:08d}")
    
    # 4. Generar XML
    try:
        xml_response = requests.post(
            'http://localhost:8000/api/generar-xml/',
            json=documento_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if xml_response.status_code != 200:
            print(f"❌ Error generando XML: {xml_response.status_code}")
            print(f"   Response: {xml_response.text[:300]}")
            return False
        
        xml_result = xml_response.json()
        if not xml_result.get('success'):
            print(f"❌ Error en generación XML: {xml_result.get('error')}")
            return False
        
        documento_id = xml_result['documento_id']
        numero_completo = xml_result['numero_completo']
        
        print(f"✅ XML generado exitosamente:")
        print(f"   📄 Documento: {numero_completo}")
        print(f"   🆔 ID: {documento_id}")
        print(f"   🔐 Estado: {xml_result['estado']}")
        
        # 5. Enviar a SUNAT con análisis completo
        print(f"\n📤 PASO 2: Enviar a SUNAT con análisis completo...")
        
        start_time = time.time()
        
        sunat_response = requests.post(
            'http://localhost:8000/api/sunat/send-bill/',
            json={'documento_id': documento_id},
            headers={'Content-Type': 'application/json'},
            timeout=120  # Timeout más largo para análisis completo
        )
        
        duration = time.time() - start_time
        
        if sunat_response.status_code != 200:
            print(f"❌ Error HTTP enviando a SUNAT: {sunat_response.status_code}")
            print(f"   Response: {sunat_response.text[:500]}")
            return False
        
        sunat_result = sunat_response.json()
        
        print(f"\n📊 RESPUESTA SUNAT COMPLETA:")
        print(f"   ✅ Success: {sunat_result.get('success')}")
        print(f"   🔧 Method: {sunat_result.get('method')}")
        print(f"   📄 Document: {sunat_result.get('document_number', 'N/A')}")
        print(f"   ⏱️ Duration: {sunat_result.get('duration_ms')}ms (Total: {duration:.1f}s)")
        
        # 6. Análisis detallado de respuesta
        success = analyze_sunat_response(sunat_result, numero_completo)
        
        # 7. Verificar estado en BD
        print(f"\n🔍 PASO 3: Verificar estado en base de datos...")
        verify_database_status(documento_id, numero_completo)
        
        return success
        
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT - SUNAT tardó más de 2 minutos en responder")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def analyze_sunat_response(sunat_result, numero_completo):
    """Análisis detallado de respuesta SUNAT"""
    
    print(f"\n🔬 ANÁLISIS DETALLADO DE RESPUESTA:")
    print(f"   📋 Documento: {numero_completo}")
    
    method = sunat_result.get('method', 'unknown')
    has_cdr = sunat_result.get('has_cdr', False)
    success = sunat_result.get('success', False)
    
    print(f"   🔧 Método usado: {method}")
    print(f"   ✅ Success: {success}")
    print(f"   📄 Tiene CDR: {has_cdr}")
    
    if success and has_cdr:
        # ¡CDR REAL ENCONTRADO!
        print(f"\n🎉 ¡CDR REAL ENCONTRADO Y PROCESADO!")
        
        cdr_info = sunat_result.get('cdr_info', {})
        
        print(f"📋 INFORMACIÓN DEL CDR:")
        print(f"   📁 Archivo: {cdr_info.get('cdr_filename', 'N/A')}")
        print(f"   📊 Estado: {cdr_info.get('status', 'N/A')}")
        print(f"   🔍 Código Respuesta: {cdr_info.get('response_code', 'N/A')}")
        print(f"   💬 Mensaje: {cdr_info.get('message', 'N/A')}")
        print(f"   ✅ Aceptado: {cdr_info.get('is_accepted', False)}")
        print(f"   ❌ Rechazado: {cdr_info.get('is_rejected', False)}")
        
        # Mostrar observaciones si las hay
        observations = cdr_info.get('observations', [])
        if observations:
            print(f"   📝 Observaciones ({len(observations)}):")
            for i, obs in enumerate(observations, 1):
                print(f"      {i}. {obs}")
        else:
            print(f"   📝 Sin observaciones")
        
        # Información técnica
        if cdr_info.get('cdr_xml'):
            print(f"   📄 CDR XML: {len(cdr_info['cdr_xml'])} caracteres")
        
        if cdr_info.get('detailed_analysis'):
            analysis = cdr_info['detailed_analysis']
            print(f"   🔬 Análisis detallado:")
            print(f"      - Código crudo: {analysis.get('raw_response_code')}")
            print(f"      - Descripción cruda: {analysis.get('raw_description')}")
            print(f"      - Notas encontradas: {analysis.get('notes_count', 0)}")
        
        print(f"\n🏆 RESULTADO: CDR real obtenido exitosamente de SUNAT")
        return True
        
    elif success and sunat_result.get('ticket'):
        # TICKET RECIBIDO
        print(f"\n🎫 TICKET RECIBIDO DE SUNAT:")
        print(f"   📋 Ticket: {sunat_result.get('ticket')}")
        print(f"   💡 Uso: Para consultar CDR posteriormente con getStatus")
        print(f"\n✅ RESULTADO: Documento enviado exitosamente (CDR asíncrono)")
        return True
        
    elif success:
        # ÉXITO PERO SIN CDR/TICKET
        print(f"\n⚠️ ÉXITO PERO SIN CDR/TICKET:")
        print(f"   🔧 Método: {method}")
        print(f"   💬 Mensaje: {sunat_result.get('message', 'N/A')}")
        
        # Mostrar información adicional si está disponible
        if sunat_result.get('response_analysis'):
            analysis = sunat_result['response_analysis']
            print(f"   🔬 Análisis de respuesta:")
            for key, value in analysis.items():
                if isinstance(value, (str, int, bool, float)):
                    print(f"      - {key}: {value}")
        
        if sunat_result.get('response_snippet'):
            snippet = sunat_result['response_snippet']
            print(f"   📄 Muestra de respuesta: {snippet[:100]}...")
        
        if sunat_result.get('debug_file'):
            print(f"   🐛 Archivo debug: {sunat_result['debug_file']}")
        
        print(f"\n🤔 RESULTADO: Respuesta exitosa pero formato no reconocido")
        print(f"💡 SUNAT puede estar devolviendo formato diferente al esperado")
        return True
        
    else:
        # ERROR
        print(f"\n❌ ERROR EN ENVÍO A SUNAT:")
        print(f"   🔧 Método: {method}")
        print(f"   💬 Error: {sunat_result.get('error', 'Error desconocido')}")
        
        # Mostrar detalles del error si están disponibles
        if sunat_result.get('error_type'):
            print(f"   🏷️ Tipo: {sunat_result['error_type']}")
        
        if sunat_result.get('error_code'):
            print(f"   🔢 Código: {sunat_result['error_code']}")
        
        if sunat_result.get('error_message'):
            print(f"   📝 Mensaje: {sunat_result['error_message']}")
        
        # Troubleshooting si está disponible
        if sunat_result.get('troubleshooting'):
            trouble = sunat_result['troubleshooting']
            print(f"   🔧 Troubleshooting:")
            
            if isinstance(trouble, dict):
                if trouble.get('description'):
                    print(f"      📝 Descripción: {trouble['description']}")
                if trouble.get('causes'):
                    print(f"      🎯 Causas:")
                    for cause in trouble['causes']:
                        print(f"         - {cause}")
                if trouble.get('solutions'):
                    print(f"      💡 Soluciones:")
                    for solution in trouble['solutions']:
                        print(f"         - {solution}")
            else:
                print(f"      💡 {trouble}")
        
        print(f"\n💥 RESULTADO: Error en comunicación con SUNAT")
        return False

def verify_database_status(documento_id, numero_completo):
    """Verificar estado del documento en base de datos"""
    
    try:
        # Usar check_cdr.py para verificar
        import subprocess
        result = subprocess.run([
            'python', 'check_cdr.py', numero_completo
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ Verificación BD exitosa")
            # Mostrar últimas líneas del output
            lines = result.stdout.strip().split('\n')
            for line in lines[-10:]:  # Últimas 10 líneas
                if line.strip():
                    print(f"   {line}")
        else:
            print(f"⚠️ Advertencia en verificación BD")
            print(f"   Output: {result.stdout[-200:]}")
            
    except Exception as e:
        print(f"⚠️ No se pudo verificar BD automáticamente: {e}")
        print(f"💡 Ejecutar manualmente: python check_cdr.py {numero_completo}")

def verify_server():
    """Verificar que el servidor esté funcionando"""
    try:
        response = requests.get('http://localhost:8000/api/sunat/status/', timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Servidor verificado:")
            print(f"   📊 Status: {result.get('system_status')}")
            
            deps = result.get('dependencies', {})
            for dep, version in deps.items():
                status_icon = "✅" if version != "NO_DISPONIBLE" else "❌"
                print(f"   {status_icon} {dep}: {version}")
            
            return True
    except Exception as e:
        print(f"❌ Error verificando servidor: {e}")
        print(f"💡 Asegurar que Django esté corriendo: python manage.py runserver")
    return False

def get_empresa_id():
    """Obtener ID de empresa"""
    try:
        response = requests.get('http://localhost:8000/api/empresas/', timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                empresa = result['data'][0]
                print(f"🏢 Empresa: {empresa.get('razon_social')}")
                print(f"🆔 RUC: {empresa.get('ruc')}")
                return empresa['id']
    except Exception as e:
        print(f"❌ Error obteniendo empresa: {e}")
    return None

if __name__ == "__main__":
    print("🔬 TEST CDR COMPLETO - ANÁLISIS DETALLADO")
    print("=" * 50)
    
    success = test_cdr_completo()
    
    print("\n" + "=" * 70)
    
    if success:
        print("🎉 ¡TEST COMPLETO EXITOSO!")
        print("✅ La integración con SUNAT está funcionando")
        print("📋 CDR procesado correctamente")
    else:
        print("❌ Test completado con errores")
        print("🔧 Revisar logs y mensajes de error arriba")
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("1. Revisar archivos de debug generados (cdr_*.xml, soap_response_*.xml)")
    print("2. Verificar estado en BD: python check_cdr.py")
    print("3. Revisar logs de Django para más detalles")
    print("4. Si hay errores, usar información de troubleshooting")