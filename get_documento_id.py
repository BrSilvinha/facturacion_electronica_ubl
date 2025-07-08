#!/usr/bin/env python
"""
Script para obtener documento_id desde la base de datos
Ejecutar: python get_documento_id.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

# Inicializar Django
django.setup()

from documentos.models import DocumentoElectronico

def find_document():
    """Buscar documento reciente por número"""
    
    print("🔍 Buscando documento 01-F001-250707007...")
    
    # Buscar por número específico
    doc = DocumentoElectronico.objects.filter(
        tipo_documento__codigo='01',
        serie='F001', 
        numero=250707007
    ).first()
    
    if doc:
        print(f"✅ Documento encontrado:")
        print(f"   📄 ID: {doc.id}")
        print(f"   📋 Número: {doc.get_numero_completo()}")
        print(f"   📊 Estado: {doc.estado}")
        print(f"   💰 Total: {doc.moneda} {doc.total}")
        print(f"   🏢 Empresa: {doc.empresa.razon_social}")
        print(f"   📅 Creado: {doc.created_at}")
        print(f"   🔑 Hash: {doc.hash_digest}")
        
        # Verificar que tenga XML firmado
        if doc.xml_firmado:
            print(f"   ✅ XML firmado: SÍ ({len(doc.xml_firmado)} caracteres)")
        else:
            print(f"   ❌ XML firmado: NO")
        
        print(f"\n🚀 Para enviar a SUNAT, usa este comando:")
        print(f"curl -X POST http://localhost:8000/api/sunat/send-bill/ \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d '{{\"documento_id\": \"{doc.id}\"}}'")
        
        return str(doc.id)
    
    else:
        print("❌ Documento no encontrado")
        
        # Buscar documentos recientes
        print("\n🔍 Documentos recientes:")
        recent_docs = DocumentoElectronico.objects.order_by('-created_at')[:5]
        
        for i, doc in enumerate(recent_docs, 1):
            print(f"   {i}. {doc.get_numero_completo()} - {doc.estado} - {doc.created_at}")
            if i == 1:  # Mostrar comando para el más reciente
                print(f"      🚀 ID: {doc.id}")
                print(f"      💡 Comando: curl -X POST http://localhost:8000/api/sunat/send-bill/ -H 'Content-Type: application/json' -d '{{\"documento_id\": \"{doc.id}\"}}'")
        
        return None

def find_all_signed_documents():
    """Buscar todos los documentos firmados"""
    
    print("\n📋 Todos los documentos firmados:")
    
    docs = DocumentoElectronico.objects.filter(
        estado__in=['FIRMADO', 'FIRMADO_SIMULADO']
    ).order_by('-created_at')
    
    for i, doc in enumerate(docs[:10], 1):  # Solo mostrar los primeros 10
        print(f"   {i}. {doc.get_numero_completo()}")
        print(f"      📄 ID: {doc.id}")
        print(f"      📊 Estado: {doc.estado}")
        print(f"      💰 Total: {doc.moneda} {doc.total}")
        print(f"      📅 Fecha: {doc.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

if __name__ == '__main__':
    print("🚀 BUSCADOR DE DOCUMENTO_ID")
    print("=" * 50)
    
    # Buscar documento específico
    doc_id = find_document()
    
    # Si no lo encuentra, mostrar todos los firmados
    if not doc_id:
        find_all_signed_documents()
    
    print("\n✅ Búsqueda completada")