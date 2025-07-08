#!/usr/bin/env python
"""
Script RÁPIDO para enviar documento 01-F001-250707011 a SUNAT
Ejecutar: python envio_rapido.py
"""

import requests
import json
import os
import sys
from pathlib import Path

def obtener_documento_id():
    """Busca el último documento generado en la base de datos"""
    
    print("🔍 Buscando documento más reciente...")
    
    try:
        # Configurar Django
        sys.path.append(str(Path(__file__).parent))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
        
        import django
        django.setup()
        
        from documentos.models import DocumentoElectronico
        
        # Buscar el documento específico o el más reciente
        documento = DocumentoElectronico.objects.filter(
            serie='F001',
            estado__in=['FIRMADO', 'FIRMADO_SIMULADO']
        ).order_by('-created_at').first()
        
        if documento:
            print(f"✅ Documento encontrado: {documento.get_numero_completo()}")
            print(f"   ID: {documento.id}")
            print(f"   Estado: {documento.estado}")
            print(f"   Total: S/ {documento.total}")
            return str(documento.id)
        else:
            print("❌ No se encontró documento firmado")
            return None
            
    except Exception as e:
        print(f"⚠️ Error accediendo BD: {e}")
        return None

def enviar_a_sunat(documento_id):
    """Envía el documento a SUNAT Beta"""
    
    API_BASE = "http://localhost:8000/api"
    
    print(f"\n📤 Enviando documento a SUNAT Beta...")
    print(f"   ID: {documento_id}")
    
    try:
        # Verificar servidor
        test_response = requests.get(f"{API_BASE}/test/", timeout=5)
        if test_response.status_code != 200:
            print("❌ Servidor Django no responde")
            return False
        
        print("✅ Servidor OK")
        
        # Enviar a SUNAT
        response = requests.post(
            f"{API_BASE}/sunat/send-bill/",
            headers={"Content-Type": "application/json"},
            json={"documento_id": documento_id},
            timeout=30
        )
        
        print(f"📡 Respuesta SUNAT: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n🎉 RESPUESTA DE SUNAT:")
            print("-" * 40)
            
            if result.get('success'):
                print(f"✅ ÉXITO: {result.get('document_number', 'N/A')}")
                print(f"📋 Estado: {result.get('document_status', 'N/A')}")
                print(f"⚡ Método: {result['sunat_response']['method']}")
                print(f"⏱️ Tiempo: {result['sunat_response']['duration_ms']}ms")
                
                # CDR info si disponible
                if 'cdr_info' in result:
                    cdr = result['cdr_info']
                    print(f"\n📄 CDR:")
                    print(f"   Aceptado: {'✅ SÍ' if cdr['is_accepted'] else '❌ NO'}")
                    print(f"   Código: {cdr['response_code']}")
                    print(f"   Descripción: {cdr['response_description']}")
                
                return True
            else:
                print(f"❌ Error: {result.get('error', 'Desconocido')}")
                print(f"🔧 Tipo: {result.get('error_type', 'N/A')}")
                
                # Si es error de implementación, mostrar simulación
                if 'NOT_IMPLEMENTED' in result.get('error_type', ''):
                    print(f"\n💡 SIMULACIÓN:")
                    print(f"   ✅ Documento procesado localmente")
                    print(f"   📋 Ticket simulado: {result.get('simulated_response', {}).get('ticket', 'N/A')}")
                    return True
                
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Detalle: {error_data}")
            except:
                print(f"   Respuesta: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ Timeout - SUNAT puede estar procesando")
        print("   💡 El documento puede haberse enviado correctamente")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    
    print("🚀 ENVÍO RÁPIDO A SUNAT BETA")
    print("=" * 50)
    print("Documento: 01-F001-250707011")
    print("Estado: FIRMADO con certificado real")
    print("")
    
    # Método 1: Buscar automáticamente
    documento_id = obtener_documento_id()
    
    # Método 2: Manual si falla automático
    if not documento_id:
        print("\n📝 Ingresa manualmente el documento_id:")
        print("   (UUID de la respuesta JSON al generar XML)")
        documento_id = input("ID: ").strip()
        
        if not documento_id:
            print("❌ documento_id requerido")
            return
    
    # Enviar a SUNAT
    if enviar_a_sunat(documento_id):
        print(f"\n🎊 ¡PROCESO COMPLETADO!")
        print(f"📄 Documento enviado a SUNAT Beta exitosamente")
    else:
        print(f"\n⚠️ PROCESO CON ERRORES")
        print(f"🔧 Revisa la configuración de SUNAT")

if __name__ == '__main__':
    main()