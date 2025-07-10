"""
Script para verificar y corregir la generación de XML
Archivo: debug_xml_generation.py
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

from documentos.models import DocumentoElectronico, Empresa

def check_recent_xml_generation():
    """Verificar XML de documentos recientes"""
    
    print("🔍 VERIFICANDO GENERACIÓN DE XML")
    print("=" * 50)
    
    # Obtener último documento
    try:
        ultimo_doc = DocumentoElectronico.objects.latest('created_at')
        print(f"📄 Último documento: {ultimo_doc.get_numero_completo()}")
        print(f"🆔 ID: {ultimo_doc.id}")
        print(f"🔐 Estado: {ultimo_doc.estado}")
        print(f"📅 Creado: {ultimo_doc.created_at}")
        
        # Verificar XML content
        print(f"\n📋 VERIFICACIÓN XML CONTENT:")
        if ultimo_doc.xml_content:
            print(f"✅ XML Content existe: {len(ultimo_doc.xml_content)} chars")
            print(f"📄 Inicio: {ultimo_doc.xml_content[:200]}...")
        else:
            print(f"❌ XML Content VACÍO!")
        
        # Verificar XML firmado
        print(f"\n🔐 VERIFICACIÓN XML FIRMADO:")
        if ultimo_doc.xml_firmado:
            print(f"✅ XML Firmado existe: {len(ultimo_doc.xml_firmado)} chars")
            print(f"📄 Inicio: {ultimo_doc.xml_firmado[:200]}...")
            
            # Análisis detallado del XML firmado
            analyze_xml_content(ultimo_doc.xml_firmado)
        else:
            print(f"❌ XML Firmado VACÍO!")
        
        return ultimo_doc
        
    except DocumentoElectronico.DoesNotExist:
        print("❌ No hay documentos en la BD")
        return None

def analyze_xml_content(xml_content):
    """Analizar contenido XML detalladamente"""
    
    print(f"\n🔬 ANÁLISIS DETALLADO DEL XML:")
    
    # Verificaciones básicas
    checks = {
        'Longitud mínima': len(xml_content) > 500,
        'Declaración XML': xml_content.strip().startswith('<?xml'),
        'Elemento Invoice': '<Invoice' in xml_content,
        'Namespace UBL': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2' in xml_content,
        'ID documento': '<cbc:ID>' in xml_content,
        'Fecha emisión': '<cbc:IssueDate>' in xml_content,
        'Proveedor': '<cac:AccountingSupplierParty>' in xml_content,
        'Cliente': '<cac:AccountingCustomerParty>' in xml_content,
        'Líneas': '<cac:InvoiceLine>' in xml_content,
        'Totales': '<cac:LegalMonetaryTotal>' in xml_content,
        'Extension': '<ext:UBLExtensions>' in xml_content
    }
    
    all_passed = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
        if not result:
            all_passed = False
    
    if not all_passed:
        print(f"\n⚠️ XML TIENE PROBLEMAS ESTRUCTURALES")
        
        # Guardar XML problemático
        debug_file = f"xml_problematico_{datetime.now().strftime('%H%M%S')}.xml"
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            print(f"💾 XML guardado para análisis: {debug_file}")
        except Exception as e:
            print(f"❌ Error guardando XML: {e}")
    else:
        print(f"\n✅ XML ESTRUCTURA PARECE CORRECTA")

def test_xml_generation_process():
    """Test del proceso completo de generación XML"""
    
    print(f"\n🧪 TEST DEL PROCESO DE GENERACIÓN XML")
    print("=" * 50)
    
    import requests
    
    # 1. Obtener empresa
    try:
        empresas_response = requests.get('http://localhost:8000/api/empresas/', timeout=10)
        if empresas_response.status_code == 200:
            empresas_data = empresas_response.json()
            if empresas_data.get('success') and empresas_data.get('data'):
                empresa_id = empresas_data['data'][0]['id']
                print(f"✅ Empresa ID obtenida: {empresa_id}")
            else:
                print(f"❌ No se encontraron empresas activas")
                return
        else:
            print(f"❌ Error obteniendo empresas: {empresas_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error conectando: {e}")
        return
    
    # 2. Datos mínimos para test
    test_numero = int(datetime.now().strftime('%M%S'))
    documento_data = {
        "tipo_documento": "01",
        "serie": "F001", 
        "numero": test_numero,
        "fecha_emision": datetime.now().strftime('%Y-%m-%d'),
        "moneda": "PEN",
        "empresa_id": empresa_id,
        "receptor": {
            "tipo_doc": "6",
            "numero_doc": "20123456789",
            "razon_social": "CLIENTE TEST XML",
            "direccion": "AV. TEST XML 123"
        },
        "items": [
            {
                "descripcion": "Producto test generación XML",
                "cantidad": 1.0,
                "valor_unitario": 100.0,
                "unidad_medida": "NIU",
                "afectacion_igv": "10",
                "codigo_producto": "TEST-XML-001"
            }
        ]
    }
    
    print(f"📋 Generando documento test: F001-{test_numero:08d}")
    
    # 3. Generar XML
    try:
        response = requests.post(
            'http://localhost:8000/api/generar-xml/',
            json=documento_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📄 Response JSON:")
            
            if result.get('success'):
                print(f"✅ Generación exitosa:")
                print(f"   📄 Documento: {result.get('numero_completo')}")
                print(f"   🆔 ID: {result.get('documento_id')}")
                print(f"   🔐 Estado: {result.get('estado')}")
                print(f"   📊 Totales: {result.get('totales', {})}")
                
                # Verificar XML inmediatamente
                doc_id = result.get('documento_id')
                if doc_id:
                    print(f"\n🔍 Verificando XML recién generado...")
                    verify_generated_xml(doc_id)
                
            else:
                print(f"❌ Error en generación:")
                print(f"   💬 Error: {result.get('error')}")
                
                # Si hay error, mostrar detalles
                if 'xml' in result.get('error', '').lower():
                    print(f"   ⚠️ Error relacionado con XML detectado")
        else:
            print(f"❌ Error HTTP:")
            print(f"   📄 Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error en test: {e}")

def verify_generated_xml(doc_id):
    """Verificar XML recién generado"""
    
    try:
        doc = DocumentoElectronico.objects.get(id=doc_id)
        
        print(f"📋 Documento encontrado: {doc.get_numero_completo()}")
        
        # Verificar XML content
        if doc.xml_content:
            print(f"✅ XML Content: {len(doc.xml_content)} chars")
            if len(doc.xml_content) < 500:
                print(f"⚠️ XML Content sospechosamente corto")
                print(f"📄 Contenido completo:")
                print(doc.xml_content)
        else:
            print(f"❌ XML Content está VACÍO")
        
        # Verificar XML firmado
        if doc.xml_firmado:
            print(f"✅ XML Firmado: {len(doc.xml_firmado)} chars")
            if len(doc.xml_firmado) < 500:
                print(f"⚠️ XML Firmado sospechosamente corto")
                print(f"📄 Contenido completo:")
                print(doc.xml_firmado)
            else:
                print(f"✅ XML Firmado tiene tamaño adecuado")
                analyze_xml_content(doc.xml_firmado)
        else:
            print(f"❌ XML Firmado está VACÍO")
            
    except DocumentoElectronico.DoesNotExist:
        print(f"❌ Documento no encontrado: {doc_id}")
    except Exception as e:
        print(f"❌ Error verificando: {e}")

def check_xml_generation_logs():
    """Verificar logs de generación XML"""
    
    print(f"\n📄 VERIFICANDO LOGS DE GENERACIÓN")
    print("=" * 40)
    
    log_files = [
        'logs/signature.log',
        'logs/certificates.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n📋 {log_file}:")
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Mostrar últimas líneas
                recent_lines = lines[-10:] if len(lines) > 10 else lines
                
                for line in recent_lines:
                    line = line.strip()
                    if line:
                        if 'ERROR' in line:
                            print(f"   ❌ {line}")
                        elif 'WARNING' in line:
                            print(f"   ⚠️ {line}")
                        else:
                            print(f"   ℹ️ {line}")
                            
            except Exception as e:
                print(f"   ❌ Error leyendo log: {e}")
        else:
            print(f"⚠️ Log no encontrado: {log_file}")

def show_recommendations():
    """Mostrar recomendaciones basadas en el análisis"""
    
    print(f"\n💡 RECOMENDACIONES:")
    print("=" * 30)
    
    print(f"1️⃣ VERIFICAR TEMPLATE UBL:")
    print(f"   - Revisar conversion/templates/ubl/factura.xml")
    print(f"   - Asegurar que el template no esté vacío")
    
    print(f"\n2️⃣ VERIFICAR GENERADOR UBL:")
    print(f"   - Revisar conversion/generators/factura_generator.py")
    print(f"   - Verificar que generate_xml() funcione")
    
    print(f"\n3️⃣ VERIFICAR FIRMA DIGITAL:")
    print(f"   - Revisar firma_digital/xml_signer.py")
    print(f"   - Verificar que sign_xml_document() no vacíe el XML")
    
    print(f"\n4️⃣ VERIFICAR CERTIFICADO:")
    print(f"   - Asegurar que C23022479065.pfx esté en certificados/production/")
    print(f"   - Verificar password: Ch14pp32023")
    
    print(f"\n5️⃣ COMANDOS ÚTILES:")
    print(f"   python verify_xml.py  # Verificar XMLs existentes")
    print(f"   python manage.py shell  # Debugging manual")

if __name__ == "__main__":
    print("🔍 DEBUG GENERACIÓN XML")
    print("=" * 30)
    
    # 1. Verificar documentos recientes
    ultimo_doc = check_recent_xml_generation()
    
    # 2. Test de generación
    test_xml_generation_process()
    
    # 3. Verificar logs
    check_xml_generation_logs()
    
    # 4. Mostrar recomendaciones
    show_recommendations()
    
    print(f"\n🎯 CONCLUSIÓN:")
    print(f"El error 0160 indica que el XML está llegando vacío a SUNAT.")
    print(f"Necesitamos verificar que el XML se genere correctamente ANTES del envío.")