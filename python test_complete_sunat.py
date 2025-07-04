#!/usr/bin/env python
"""
Prueba completa del flujo: Generar XML → Firmar → Enviar a SUNAT
Ubicación: test_complete_sunat.py (en la raíz del proyecto)
"""

import os
import sys
import django
from pathlib import Path
import json
import time
from datetime import datetime, date

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

from documentos.models import Empresa, TipoDocumento, DocumentoElectronico
from conversion.generators import generate_ubl_xml
from firma_digital import XMLSigner, certificate_manager
from sunat_integration import sunat_client, cdr_processor

def create_test_data():
    """Crea datos de prueba si no existen"""
    print("📋 Creando datos de prueba...")
    
    # Crear empresa de prueba
    empresa, created = Empresa.objects.get_or_create(
        ruc='20123456789',
        defaults={
            'razon_social': 'EMPRESA TEST SUNAT SAC',
            'nombre_comercial': 'EMPRESA TEST',
            'direccion': 'AV. LARCO 123, MIRAFLORES, LIMA',
            'ubigeo': '150101',
            'activo': True
        }
    )
    
    if created:
        print(f"   ✅ Empresa creada: {empresa.razon_social}")
    else:
        print(f"   ℹ️  Empresa existe: {empresa.razon_social}")
    
    # Crear tipo de documento si no existe
    tipo_doc, created = TipoDocumento.objects.get_or_create(
        codigo='01',
        defaults={
            'descripcion': 'Factura',
            'activo': True
        }
    )
    
    if created:
        print(f"   ✅ Tipo documento creado: {tipo_doc.descripcion}")
    else:
        print(f"   ℹ️  Tipo documento existe: {tipo_doc.descripcion}")
    
    return empresa, tipo_doc

def create_test_document():
    """Crea documento de prueba"""
    print("\n📄 Creando documento de prueba...")
    
    empresa, tipo_doc = create_test_data()
    
    # Datos del documento
    document_data = {
        'tipo_documento': '01',
        'serie': 'F001',
        'numero': 1,
        'fecha_emision': date.today(),
        'moneda': 'PEN',
        'empresa_id': str(empresa.id),
        'receptor': {
            'tipo_doc': '6',
            'numero_doc': '20987654321',
            'razon_social': 'EMPRESA CLIENTE SAC',
            'direccion': 'AV. BRASIL 456, LIMA'
        },
        'items': [
            {
                'descripcion': 'PRODUCTO DE PRUEBA PARA SUNAT',
                'cantidad': 1,
                'valor_unitario': 100.00,
                'afectacion_igv': '10'
            },
            {
                'descripcion': 'SERVICIO DE PRUEBA ADICIONAL',
                'cantidad': 2,
                'valor_unitario': 50.00,
                'afectacion_igv': '10'
            }
        ]
    }
    
    # Crear documento usando la API interna
    from api_rest.views import GenerarXMLView
    from rest_framework.test import APIRequestFactory
    from rest_framework.request import Request
    
    factory = APIRequestFactory()
    request = factory.post('/api/generar-xml/', document_data, format='json')
    
    view = GenerarXMLView()
    response = view.post(Request(request))
    
    if response.status_code == 200:
        documento_id = response.data['documento_id']
        documento = DocumentoElectronico.objects.get(id=documento_id)
        
        print(f"   ✅ Documento creado: {documento.get_numero_completo()}")
        print(f"   - ID: {documento_id}")
        print(f"   - Total: S/ {documento.total}")
        print(f"   - Estado: {documento.estado}")
        
        return documento
    else:
        print(f"   ❌ Error creando documento: {response.data}")
        return None

def test_xml_generation(documento):
    """Prueba generación de XML"""
    print(f"\n📝 Probando generación XML para {documento.get_numero_completo()}...")
    
    try:
        # El XML ya debería estar generado
        if documento.xml_content:
            print(f"   ✅ XML generado: {len(documento.xml_content)} caracteres")
            return True
        else:
            print("   ❌ XML no encontrado")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_digital_signature(documento):
    """Prueba firma digital"""
    print(f"\n🔐 Probando firma digital...")
    
    try:
        # Cargar certificado de prueba
        cert_path = 'certificados/test/test_cert_empresa1.pfx'
        password = 'test123'
        
        cert_info = certificate_manager.get_certificate(cert_path, password)
        
        # Firmar XML
        signer = XMLSigner()
        xml_firmado = signer.sign_xml_document(
            documento.xml_content,
            cert_info,
            documento.get_numero_completo()
        )
        
        # Actualizar documento
        documento.xml_firmado = xml_firmado
        documento.estado = 'FIRMADO'
        documento.save()
        
        print(f"   ✅ Documento firmado: {len(xml_firmado)} caracteres")
        print(f"   - Estado actualizado: {documento.estado}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error firmando: {e}")
        return False

def test_sunat_connection():
    """Prueba conexión con SUNAT"""
    print(f"\n🌐 Probando conexión SUNAT...")
    
    try:
        result = sunat_client.test_connection()
        
        if result['success']:
            print("   ✅ Conexión SUNAT exitosa")
            print(f"   - Ambiente: {sunat_client.environment}")
            print(f"   - WSDL: {result['service_info']['wsdl_url']}")
            return True
        else:
            print(f"   ❌ Error conexión: {result['error']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_send_to_sunat(documento):
    """Prueba envío a SUNAT"""
    print(f"\n🚀 Enviando documento a SUNAT Beta...")
    
    try:
        print(f"   - Documento: {documento.get_numero_completo()}")
        print(f"   - Estado actual: {documento.estado}")
        
        # Enviar a SUNAT
        response = sunat_client.send_bill(documento, documento.xml_firmado)
        
        print(f"   ✅ Enviado a SUNAT en {response['duration_ms']:.0f}ms")
        print(f"   - Método: {response['method']}")
        print(f"   - Archivo ZIP: {response['zip_filename']}")
        print(f"   - Correlación: {response['correlation_id']}")
        
        # Procesar CDR
        if 'cdr_content' in response:
            print("\n📋 Procesando CDR...")
            
            cdr_data = cdr_processor.process_cdr_zip(response['cdr_content'])
            
            print(f"   - CDR ID: {cdr_data['cdr_id']}")
            print(f"   - Estado: {cdr_data['status_summary']}")
            print(f"   - Código respuesta: {cdr_data['response_code']}")
            print(f"   - Descripción: {cdr_data['response_description']}")
            
            if cdr_data['notes']:
                print(f"   - Observaciones: {len(cdr_data['notes'])}")
                for note in cdr_data['notes']:
                    print(f"     * {note['full_text']}")
            
            # Actualizar estado del documento
            if cdr_data['is_accepted']:
                documento.estado = 'ACEPTADO'
                documento.save()
                print(f"   ✅ Documento ACEPTADO por SUNAT")
                return True
            else:
                documento.estado = 'RECHAZADO'
                documento.save()
                print(f"   ⚠️  Documento RECHAZADO por SUNAT")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error enviando a SUNAT: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_flow():
    """Prueba flujo completo"""
    print("🚀 PRUEBA COMPLETA: XML → FIRMA → SUNAT")
    print("=" * 60)
    
    # Paso 1: Crear documento
    documento = create_test_document()
    if not documento:
        print("❌ No se pudo crear documento de prueba")
        return False
    
    # Paso 2: Verificar XML
    if not test_xml_generation(documento):
        print("❌ Error en generación XML")
        return False
    
    # Paso 3: Firmar documento
    if not test_digital_signature(documento):
        print("❌ Error en firma digital")
        return False
    
    # Paso 4: Probar conexión SUNAT
    if not test_sunat_connection():
        print("❌ Error en conexión SUNAT")
        return False
    
    # Paso 5: Enviar a SUNAT
    if not test_send_to_sunat(documento):
        print("❌ Error enviando a SUNAT")
        return False
    
    return True

def main():
    """Función principal"""
    try:
        success = test_complete_flow()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 ¡FLUJO COMPLETO EXITOSO!")
            print("✅ XML generado correctamente")
            print("✅ Documento firmado digitalmente")
            print("✅ Enviado y procesado por SUNAT")
            print("\n🚀 ¡Sistema listo para producción!")
            print("\n📝 Próximos pasos:")
            print("1. Configurar certificados de producción")
            print("2. Cambiar ambiente a 'production' en .env")
            print("3. Configurar credenciales reales de SUNAT")
            return 0
        else:
            print("❌ FLUJO CON ERRORES")
            print("🔧 Revisar logs para más detalles")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Prueba interrumpida por el usuario")
        return 1
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())