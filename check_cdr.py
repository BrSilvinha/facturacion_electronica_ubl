"""
Script para verificar CDR en base de datos
Archivo: check_cdr.py
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

from documentos.models import DocumentoElectronico

def check_recent_documents():
    """Verificar documentos recientes y sus CDR"""
    
    print("🔍 VERIFICANDO CDR EN BASE DE DATOS")
    print("=" * 50)
    
    # Obtener documentos recientes (últimas 24 horas)
    recent_docs = DocumentoElectronico.objects.filter(
        created_at__gte=datetime.now().replace(hour=0, minute=0, second=0)
    ).order_by('-created_at')[:10]
    
    print(f"📄 Documentos recientes encontrados: {recent_docs.count()}")
    print()
    
    for doc in recent_docs:
        print(f"📋 DOCUMENTO: {doc.get_numero_completo()}")
        print(f"   🆔 ID: {str(doc.id)[:8]}...")
        print(f"   📅 Creado: {doc.created_at.strftime('%H:%M:%S')}")
        print(f"   🔐 Estado: {doc.estado}")
        print(f"   📤 Tiene XML firmado: {'✅' if doc.xml_firmado else '❌'}")
        
        # Verificar CDR
        if doc.cdr_xml:
            print(f"   🎉 TIENE CDR:")
            print(f"      📋 Estado CDR: {doc.cdr_estado}")
            print(f"      🔍 Código: {doc.cdr_codigo_respuesta}")
            print(f"      💬 Descripción: {doc.cdr_descripcion}")
            print(f"      📅 Fecha CDR: {doc.cdr_fecha_recepcion}")
            print(f"      📄 XML CDR: {len(doc.cdr_xml)} caracteres")
            
            # Analizar contenido del CDR
            if '<cbc:ResponseCode>0</cbc:ResponseCode>' in doc.cdr_xml:
                print(f"      ✅ ESTADO: ACEPTADO POR SUNAT")
            elif '<cbc:ResponseCode>' in doc.cdr_xml:
                # Extraer código
                start = doc.cdr_xml.find('<cbc:ResponseCode>') + len('<cbc:ResponseCode>')
                end = doc.cdr_xml.find('</cbc:ResponseCode>')
                code = doc.cdr_xml[start:end] if end > start else 'Unknown'
                print(f"      ⚠️ CÓDIGO: {code}")
            else:
                print(f"      ❓ Sin código de respuesta en CDR")
        else:
            print(f"   ❌ SIN CDR")
            
            # Verificar ticket SUNAT
            if doc.ticket_sunat:
                print(f"      🎫 Ticket SUNAT: {doc.ticket_sunat}")
                print(f"      💡 Puede requerir consulta posterior")
        
        print(f"   " + "-" * 40)
        print()
    
    return recent_docs

def check_specific_document(document_number):
    """Verificar documento específico"""
    
    try:
        # Extraer serie y número
        parts = document_number.split('-')
        if len(parts) == 3:
            tipo, serie, numero = parts
            numero = int(numero)
            
            doc = DocumentoElectronico.objects.get(
                tipo_documento__codigo=tipo,
                serie=serie,
                numero=numero
            )
            
            print(f"🔍 DOCUMENTO ESPECÍFICO: {doc.get_numero_completo()}")
            print(f"   🆔 ID: {doc.id}")
            print(f"   🔐 Estado: {doc.estado}")
            
            if doc.cdr_xml:
                print(f"   🎉 CDR ENCONTRADO:")
                print(f"      📋 Estado: {doc.cdr_estado}")
                print(f"      🔍 Código: {doc.cdr_codigo_respuesta}")
                print(f"      📄 CDR XML (primeros 200 chars):")
                print(f"      {doc.cdr_xml[:200]}...")
                
                # Guardar CDR en archivo
                filename = f"cdr_{doc.get_numero_completo().replace('-', '_')}.xml"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(doc.cdr_xml)
                print(f"      💾 CDR guardado en: {filename}")
            else:
                print(f"   ❌ SIN CDR en base de datos")
            
            return doc
            
    except DocumentoElectronico.DoesNotExist:
        print(f"❌ Documento {document_number} no encontrado")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def show_latest_document():
    """Mostrar el último documento generado"""
    
    try:
        latest = DocumentoElectronico.objects.latest('created_at')
        print(f"📄 ÚLTIMO DOCUMENTO GENERADO:")
        print(f"   📋 Número: {latest.get_numero_completo()}")
        print(f"   🆔 ID: {latest.id}")
        print(f"   📅 Creado: {latest.created_at}")
        print(f"   🔐 Estado: {latest.estado}")
        
        if latest.cdr_xml:
            print(f"   🎉 TIENE CDR - Verificar arriba para detalles")
        else:
            print(f"   ❌ SIN CDR")
            
        return latest
        
    except DocumentoElectronico.DoesNotExist:
        print("❌ No hay documentos en la base de datos")
        return None

if __name__ == "__main__":
    print("🔍 VERIFICADOR DE CDR")
    print("=" * 30)
    
    # Mostrar último documento
    latest = show_latest_document()
    print()
    
    # Verificar documentos recientes
    recent = check_recent_documents()
    
    # Si hay argumentos, verificar documento específico
    if len(sys.argv) > 1:
        document_number = sys.argv[1]
        print(f"🔍 Verificando documento específico: {document_number}")
        check_specific_document(document_number)
    
    print("✅ Verificación completada")
    print()
    print("💡 COMANDOS ÚTILES:")
    print("   python check_cdr.py                    # Verificar todos")
    print("   python check_cdr.py 01-F001-00194352   # Verificar específico")