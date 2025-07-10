#!/usr/bin/env python
"""
Script de debugging para verificar el contenido XML que se envía a SUNAT
Ejecutar desde el directorio raíz del proyecto Django
"""

import os
import sys
import django
from pathlib import Path
import base64
import zipfile
from io import BytesIO

# Configurar Django
project_path = Path(__file__).parent
sys.path.append(str(project_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

django.setup()

from documentos.models import DocumentoElectronico

def debug_ultimo_documento():
    """Debug del último documento generado"""
    
    print("🔍 DEBUGGING ÚLTIMO DOCUMENTO XML")
    print("=" * 60)
    
    # Buscar último documento
    try:
        documento = DocumentoElectronico.objects.filter(
            xml_firmado__isnull=False
        ).order_by('-created_at').first()
        
        if not documento:
            print("❌ No se encontró ningún documento firmado")
            return
        
        print(f"📄 Documento: {documento.get_numero_completo()}")
        print(f"📅 Creado: {documento.created_at}")
        print(f"📊 Estado: {documento.estado}")
        print()
        
        # Verificar XML firmado
        xml_content = documento.xml_firmado
        if not xml_content:
            print("❌ XML firmado está vacío")
            return
        
        print(f"✅ XML firmado disponible: {len(xml_content)} caracteres")
        
        # Verificar inicio del XML
        print("\n📋 INICIO DEL XML (primeros 500 chars):")
        print("-" * 50)
        print(xml_content[:500])
        print("-" * 50)
        
        # Verificar elementos críticos
        print("\n🔍 VERIFICACIÓN DE ELEMENTOS CRÍTICOS:")
        elementos_criticos = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<Invoice',
            '<cbc:ID>',
            '<cbc:IssueDate>',
            '<cac:AccountingSupplierParty>',
            '<cac:AccountingCustomerParty>',
            '<cac:InvoiceLine>',
            '<cac:LegalMonetaryTotal>'
        ]
        
        for elemento in elementos_criticos:
            presente = elemento in xml_content
            status = "✅" if presente else "❌"
            print(f"  {status} {elemento}")
        
        # Simular creación de ZIP como lo hace SUNAT
        print("\n📦 SIMULANDO CREACIÓN DE ZIP:")
        try:
            ruc = "20103129061"
            xml_filename = f"{ruc}-01-{documento.serie}-{documento.numero:08d}.xml"
            
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
                # Carpeta dummy
                zip_file.writestr('dummy/', '')
                
                # XML
                xml_bytes = xml_content.encode('utf-8')
                zip_file.writestr(xml_filename, xml_bytes, compresslevel=6)
                
                print(f"  ✅ ZIP creado con {len(zip_file.namelist())} archivos")
                print(f"  📄 Archivos: {zip_file.namelist()}")
                print(f"  📊 XML bytes: {len(xml_bytes)}")
            
            zip_content = zip_buffer.getvalue()
            print(f"  📦 ZIP final: {len(zip_content)} bytes")
            
            # Verificar ZIP
            with zipfile.ZipFile(BytesIO(zip_content), 'r') as verify_zip:
                files = verify_zip.namelist()
                print(f"  🔍 Verificación ZIP: {len(files)} archivos")
                
                if xml_filename in files:
                    xml_read = verify_zip.read(xml_filename).decode('utf-8')
                    print(f"  ✅ XML leído del ZIP: {len(xml_read)} chars")
                    print(f"  🔍 Inicia con: {xml_read[:100]}...")
                    
                    # Verificar que el contenido sea el mismo
                    if xml_read == xml_content:
                        print("  ✅ XML en ZIP coincide con original")
                    else:
                        print("  ❌ XML en ZIP NO coincide con original")
                        print("  📊 Diferencias en longitud:", len(xml_read), "vs", len(xml_content))
                else:
                    print(f"  ❌ Archivo XML {xml_filename} no encontrado en ZIP")
            
            # Codificar Base64
            content_base64 = base64.b64encode(zip_content).decode('utf-8')
            print(f"  📄 Base64: {len(content_base64)} caracteres")
            print(f"  🔍 Base64 inicia: {content_base64[:50]}...")
            
        except Exception as e:
            print(f"  ❌ Error simulando ZIP: {e}")
        
        # Buscar el archivo de respuesta guardado
        print("\n📁 VERIFICANDO RESPUESTA SUNAT GUARDADA:")
        temp_dir = Path('temp') / 'sunat_responses'
        if temp_dir.exists():
            response_files = list(temp_dir.glob('response_*.xml'))
            if response_files:
                latest_response = max(response_files, key=lambda x: x.stat().st_mtime)
                print(f"  📄 Última respuesta: {latest_response.name}")
                
                with open(latest_response, 'r', encoding='utf-8') as f:
                    response_content = f.read()
                
                print(f"  📊 Tamaño respuesta: {len(response_content)} chars")
                print("  📋 Contenido respuesta:")
                print("  " + "-" * 50)
                print("  " + response_content[:300].replace('\n', '\n  '))
                print("  " + "-" * 50)
                
                # Buscar código de error específico
                if 'Client.0160' in response_content:
                    print("  ❌ Confirmado: Error 0160 presente en respuesta")
                    if 'File size error' in response_content:
                        print("  🔍 Detalle: Error de tamaño de archivo")
                    if 'XML esta vacio' in response_content:
                        print("  🔍 Detalle: SUNAT considera el XML vacío")
            else:
                print("  📁 No se encontraron archivos de respuesta")
        else:
            print("  📁 Directorio de respuestas no existe")
        
        # Recomendaciones
        print("\n💡 RECOMENDACIONES:")
        print("1. Verificar que el XML contiene todos los elementos requeridos")
        print("2. Revisar codificación UTF-8 del XML")
        print("3. Verificar que no hay caracteres especiales problemáticos")
        print("4. Probar con un XML mínimo para descartar problemas de contenido")
        
    except Exception as e:
        print(f"❌ Error en debugging: {e}")
        import traceback
        traceback.print_exc()

def generar_xml_minimo():
    """Genera un XML mínimo para testing"""
    
    print("\n🧪 GENERANDO XML MÍNIMO PARA TESTING:")
    print("-" * 50)
    
    xml_minimo = '''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>2.0</cbc:CustomizationID>
    <cbc:ID>F001-00000001</cbc:ID>
    <cbc:IssueDate>2025-07-10</cbc:IssueDate>
    <cbc:InvoiceTypeCode listAgencyName="PE:SUNAT">01</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>PEN</cbc:DocumentCurrencyCode>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">20103129061</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>COMERCIAL LAVAGNA S.A.C.</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">20987654321</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>CLIENTE TEST</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="PEN">18.00</cbc:TaxAmount>
    </cac:TaxTotal>
    
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="PEN">100.00</cbc:LineExtensionAmount>
        <cbc:TaxInclusiveAmount currencyID="PEN">118.00</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="PEN">118.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="NIU">1</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="PEN">100.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Description>Producto Test</cbc:Description>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="PEN">100.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
</Invoice>'''
    
    print(f"📄 XML Mínimo generado: {len(xml_minimo)} caracteres")
    print("💾 Guardado en: temp/xml_minimo_test.xml")
    
    # Guardar archivo
    temp_dir = Path('temp')
    temp_dir.mkdir(exist_ok=True)
    
    with open(temp_dir / 'xml_minimo_test.xml', 'w', encoding='utf-8') as f:
        f.write(xml_minimo)
    
    return xml_minimo

def main():
    """Función principal"""
    try:
        debug_ultimo_documento()
        generar_xml_minimo()
        
        print("\n" + "=" * 60)
        print("🎯 SIGUIENTE PASO:")
        print("1. Revisar los elementos críticos que faltan")
        print("2. Comparar con el XML mínimo generado")
        print("3. Probar con un documento más simple")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()