"""
Debug SUNAT - Análisis de logs y respuestas detalladas
Archivo: debug_sunat.py
"""

import requests
import json
from datetime import datetime
import os
import glob

def debug_sunat_complete():
    """Debug completo de SUNAT con captura de logs"""
    
    print("🐛 DEBUG SUNAT COMPLETO")
    print("=" * 50)
    
    # 1. Verificar archivos de debug existentes
    print("\n📁 PASO 1: Revisar archivos de debug existentes...")
    check_debug_files()
    
    # 2. Verificar logs de Django
    print("\n📄 PASO 2: Revisar logs de Django...")
    check_django_logs()
    
    # 3. Test directo con captura detallada
    print("\n🧪 PASO 3: Test directo con captura de errores...")
    test_direct_with_capture()
    
    # 4. Revisar estado de documentos recientes
    print("\n📋 PASO 4: Revisar documentos recientes...")
    check_recent_documents()

def check_debug_files():
    """Revisar archivos de debug generados"""
    
    debug_patterns = [
        'cdr_*.xml',
        'soap_response_*.xml',
        '*.log'
    ]
    
    found_files = []
    for pattern in debug_patterns:
        files = glob.glob(pattern)
        found_files.extend(files)
    
    if found_files:
        print(f"✅ Archivos de debug encontrados ({len(found_files)}):")
        for file in sorted(found_files)[-10:]:  # Últimos 10
            size = os.path.getsize(file) if os.path.exists(file) else 0
            print(f"   📄 {file} ({size} bytes)")
            
            # Mostrar contenido si es pequeño
            if size < 2000 and file.endswith('.xml'):
                print(f"      Contenido:")
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()[:500]
                        print(f"      {content}...")
                except:
                    pass
    else:
        print("⚠️ No se encontraron archivos de debug")

def check_django_logs():
    """Revisar logs de Django"""
    
    log_files = [
        'logs/sunat.log',
        'logs/signature.log',
        'logs/certificates.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n📄 Log: {log_file}")
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Mostrar últimas 20 líneas
                recent_lines = lines[-20:] if len(lines) > 20 else lines
                
                print(f"   📊 Total líneas: {len(lines)}")
                print(f"   📄 Últimas entradas:")
                
                for line in recent_lines:
                    line = line.strip()
                    if line:
                        # Colorear por nivel
                        if 'ERROR' in line:
                            print(f"   ❌ {line}")
                        elif 'WARNING' in line:
                            print(f"   ⚠️ {line}")
                        elif 'INFO' in line:
                            print(f"   ℹ️ {line}")
                        else:
                            print(f"   📝 {line}")
            except Exception as e:
                print(f"   ❌ Error leyendo log: {e}")
        else:
            print(f"⚠️ Log no encontrado: {log_file}")

def test_direct_with_capture():
    """Test directo con captura de errores detallada"""
    
    # Obtener empresa ID
    empresa_id = get_empresa_id()
    if not empresa_id:
        return
    
    # Generar documento simple
    numero_unico = int(datetime.now().strftime('%M%S'))
    
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
            "razon_social": "CLIENTE DEBUG SUNAT",
            "direccion": "AV. DEBUG 123"
        },
        "items": [
            {
                "descripcion": "Producto debug SUNAT",
                "cantidad": 1.0,
                "valor_unitario": 50.0,
                "unidad_medida": "NIU",
                "afectacion_igv": "10"
            }
        ]
    }
    
    print(f"📋 Generando documento debug: F001-{numero_unico:08d}")
    
    try:
        # 1. Generar XML
        xml_response = requests.post(
            'http://localhost:8000/api/generar-xml/',
            json=documento_data,
            timeout=30
        )
        
        if xml_response.status_code != 200:
            print(f"❌ Error generando XML: {xml_response.status_code}")
            print(f"   Response: {xml_response.text}")
            return
        
        xml_result = xml_response.json()
        if not xml_result.get('success'):
            print(f"❌ Error XML: {xml_result.get('error')}")
            return
        
        documento_id = xml_result['documento_id']
        print(f"✅ XML generado: {documento_id}")
        
        # 2. Enviar a SUNAT con captura detallada
        print(f"📤 Enviando a SUNAT...")
        
        # Activar modo debug en Django (si existe)
        headers = {
            'Content-Type': 'application/json',
            'X-Debug-Mode': 'true',  # Header personalizado para debug
            'X-Capture-Response': 'true'
        }
        
        sunat_response = requests.post(
            'http://localhost:8000/api/sunat/send-bill/',
            json={'documento_id': documento_id},
            headers=headers,
            timeout=60
        )
        
        print(f"📊 Status Code: {sunat_response.status_code}")
        print(f"📄 Response Headers: {dict(sunat_response.headers)}")
        
        if sunat_response.status_code == 200:
            result = sunat_response.json()
            print(f"📋 Response JSON:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
            
            # Analizar el fault específico
            if result.get('error_type') == 'SOAP_FAULT':
                analyze_soap_fault(result)
                
        else:
            print(f"❌ Error HTTP: {sunat_response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error en test directo: {e}")

def analyze_soap_fault(result):
    """Analizar SOAP Fault específico"""
    
    print(f"\n🔍 ANÁLISIS DE SOAP FAULT:")
    
    fault_info = result.get('fault_info', {})
    error_code = result.get('error_code')
    error_message = result.get('error_message')
    
    print(f"   🔢 Error Code: {error_code}")
    print(f"   💬 Error Message: {error_message}")
    
    if fault_info:
        print(f"   📋 Fault Info:")
        for key, value in fault_info.items():
            print(f"      {key}: {value}")
    
    # Troubleshooting específico
    troubleshooting = result.get('troubleshooting', {})
    if troubleshooting:
        print(f"   🔧 Troubleshooting:")
        if isinstance(troubleshooting, dict):
            for key, value in troubleshooting.items():
                print(f"      {key}: {value}")
        else:
            print(f"      {troubleshooting}")
    
    # Diagnóstico basado en código de error
    if error_code:
        provide_specific_diagnosis(error_code, error_message)

def provide_specific_diagnosis(error_code, error_message):
    """Proporcionar diagnóstico específico"""
    
    print(f"\n💡 DIAGNÓSTICO ESPECÍFICO:")
    
    if '0102' in str(error_code):
        print(f"   🎯 PROBLEMA: Credenciales incorrectas")
        print(f"   🔧 SOLUCIÓN:")
        print(f"      1. Verificar que el usuario sea: 20103129061MODDATOS")
        print(f"      2. Verificar que el password sea: MODDATOS")
        print(f"      3. Verificar formato del envelope SOAP")
        
    elif '0111' in str(error_code):
        print(f"   🎯 PROBLEMA: Usuario sin perfil")
        print(f"   🔧 SOLUCIÓN:")
        print(f"      1. Crear usuario secundario en SOL SUNAT")
        print(f"      2. Asignar perfil 'Emisor electrónico'")
        
    elif '0154' in str(error_code):
        print(f"   🎯 PROBLEMA: RUC no autorizado")
        print(f"   🔧 SOLUCIÓN:")
        print(f"      1. Verificar que el RUC 20103129061 esté activo")
        print(f"      2. Solicitar autorización para facturación electrónica")
        
    elif 'Unauthorized' in str(error_message):
        print(f"   🎯 PROBLEMA: Error de autenticación HTTP")
        print(f"   🔧 SOLUCIÓN:")
        print(f"      1. Verificar headers de autenticación")
        print(f"      2. Verificar formato del envelope SOAP")
        print(f"      3. Verificar URL del servicio")
        
    elif 'WSDL' in str(error_message):
        print(f"   🎯 PROBLEMA: Error accediendo al WSDL")
        print(f"   🔧 SOLUCIÓN:")
        print(f"      1. El método actual evita el WSDL")
        print(f"      2. Verificar que el envelope SOAP sea correcto")
        
    else:
        print(f"   🎯 PROBLEMA: Error no catalogado")
        print(f"   🔧 SOLUCIÓN:")
        print(f"      1. Revisar logs de Django para más detalles")
        print(f"      2. Verificar conectividad con SUNAT")
        print(f"      3. Contactar soporte técnico")

def check_recent_documents():
    """Revisar documentos recientes en la BD"""
    
    try:
        # Usar API para obtener documentos
        response = requests.get('http://localhost:8000/api/empresas/', timeout=10)
        if response.status_code == 200:
            print(f"✅ Conexión con API funcionando")
        
        # Ejecutar check_cdr.py
        import subprocess
        result = subprocess.run([
            'python', 'check_cdr.py'
        ], capture_output=True, text=True, timeout=30)
        
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines[-15:]:  # Últimas 15 líneas
                if line.strip():
                    print(f"   {line}")
                    
    except Exception as e:
        print(f"⚠️ Error verificando documentos: {e}")

def get_empresa_id():
    """Obtener ID de empresa"""
    try:
        response = requests.get('http://localhost:8000/api/empresas/', timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                return result['data'][0]['id']
    except Exception as e:
        print(f"❌ Error obteniendo empresa: {e}")
    return None

def show_next_steps():
    """Mostrar próximos pasos según el diagnóstico"""
    
    print(f"\n🎯 PRÓXIMOS PASOS RECOMENDADOS:")
    
    print(f"\n1️⃣ VERIFICAR CREDENCIALES:")
    print(f"   - Usuario: 20103129061MODDATOS")
    print(f"   - Password: MODDATOS")
    print(f"   - Ambiente: SUNAT Beta")
    
    print(f"\n2️⃣ VERIFICAR CONFIGURACIÓN:")
    print(f"   - Revisar archivo .env")
    print(f"   - Verificar settings.py")
    print(f"   - Confirmar URLs de SUNAT Beta")
    
    print(f"\n3️⃣ REVISAR LOGS:")
    print(f"   - logs/sunat.log")
    print(f"   - Archivos soap_response_*.xml")
    print(f"   - Consola de Django (terminal donde corre el servidor)")
    
    print(f"\n4️⃣ PROBAR ALTERNATIVAS:")
    print(f"   - Probar con diferentes formatos de envelope")
    print(f"   - Verificar conectividad directa a SUNAT")
    print(f"   - Probar con certificado diferente")

if __name__ == "__main__":
    debug_sunat_complete()
    show_next_steps()