#!/usr/bin/env python
"""
ANALIZADOR DE CONTENIDO PARA ERROR 0160
Archivo: content_analyzer.py

Analiza el contenido XML y ZIP para encontrar la causa raíz del error 0160
"""

import os
import sys
import base64
import zipfile
from io import BytesIO
from pathlib import Path
import re

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

import django
django.setup()

from documentos.models import DocumentoElectronico

def analyze_content():
    """Analiza el contenido para encontrar problemas específicos"""
    
    print("🔬 ANALIZADOR DE CONTENIDO - ERROR 0160")
    print("=" * 60)
    
    # Obtener documento
    documento = DocumentoElectronico.objects.filter(
        serie='F001',
        numero=1,
        empresa__ruc='20103129061'
    ).first()
    
    if not documento:
        print("❌ No se encontró documento")
        return
    
    print(f"📄 Analizando: {documento.get_numero_completo()}")
    
    # 1. Analizar XML
    print("\n🔍 ANÁLISIS DEL XML:")
    xml_issues = analyze_xml_content(documento.xml_firmado)
    
    # 2. Analizar ZIP
    print("\n🔍 ANÁLISIS DEL ZIP:")
    zip_issues = analyze_zip_content(documento)
    
    # 3. Analizar Base64
    print("\n🔍 ANÁLISIS BASE64:")
    b64_issues = analyze_base64_content(documento)
    
    # 4. Comparar con documentos exitosos
    print("\n🔍 COMPARACIÓN CON EJEMPLOS EXITOSOS:")
    compare_with_examples()
    
    # 5. Reporte final
    print("\n📋 REPORTE FINAL:")
    total_issues = len(xml_issues) + len(zip_issues) + len(b64_issues)
    
    if total_issues == 0:
        print("✅ No se encontraron problemas en el contenido")
        print("❓ El problema puede estar en:")
        print("   - Configuración de red")
        print("   - Headers HTTP")
        print("   - Timing de envío")
        print("   - Configuración de SUNAT Beta")
    else:
        print(f"⚠️ Se encontraron {total_issues} problemas potenciales:")
        for issue in xml_issues + zip_issues + b64_issues:
            print(f"   - {issue}")

def analyze_xml_content(xml_content):
    """Analiza problemas específicos en el XML"""
    
    issues = []
    
    if not xml_content:
        issues.append("XML está vacío")
        return issues
    
    # Verificaciones básicas
    print(f"   📏 Longitud: {len(xml_content)} chars")
    print(f"   📋 Inicia con: {xml_content[:50]}...")
    
    # Problemas comunes
    if len(xml_content) < 1000:
        issues.append(f"XML muy corto: {len(xml_content)} chars")
    
    if not xml_content.startswith('<?xml'):
        issues.append("XML sin declaración válida")
    
    if 'encoding="UTF-8"' not in xml_content:
        issues.append("XML sin encoding UTF-8 explícito")
    
    # Verificar elementos requeridos por SUNAT
    required_elements = [
        ('<Invoice', 'Elemento Invoice'),
        ('urn:oasis:names:specification:ubl:schema:xsd:Invoice-2', 'Namespace UBL'),
        ('<cbc:ID>', 'ID del documento'),
        ('<cbc:IssueDate>', 'Fecha de emisión'),
        ('20103129061', 'RUC del emisor'),
        ('<cac:AccountingSupplierParty>', 'Datos del emisor'),
        ('<cac:AccountingCustomerParty>', 'Datos del cliente'),
        ('<cac:InvoiceLine>', 'Líneas de la factura'),
        ('<cac:LegalMonetaryTotal>', 'Totales monetarios')
    ]
    
    for element, description in required_elements:
        if element not in xml_content:
            issues.append(f"Falta elemento: {description}")
    
    # Verificar caracteres problemáticos
    if '\ufeff' in xml_content:
        issues.append("XML contiene BOM")
    
    # Verificar encoding real
    try:
        xml_content.encode('utf-8')
    except UnicodeEncodeError:
        issues.append("XML contiene caracteres no UTF-8")
    
    # Verificar estructura XML
    try:
        from lxml import etree
        etree.fromstring(xml_content.encode('utf-8'))
        print("   ✅ XML bien formado")
    except Exception as e:
        issues.append(f"XML mal formado: {str(e)[:100]}")
    
    return issues

def analyze_zip_content(documento):
    """Analiza problemas en la generación del ZIP"""
    
    issues = []
    
    try:
        # Recrear ZIP como en el envío
        xml_content = documento.xml_firmado.strip()
        if xml_content.startswith('\ufeff'):
            xml_content = xml_content[1:]
        
        zip_buffer = BytesIO()
        xml_filename = f"20103129061-01-{documento.serie}-{documento.numero:08d}.xml"
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('dummy/', '')
            zip_file.writestr(xml_filename, xml_content.encode('utf-8'))
        
        zip_content = zip_buffer.getvalue()
        
        print(f"   📦 Tamaño ZIP: {len(zip_content)} bytes")
        
        # Verificaciones
        if len(zip_content) < 1000:
            issues.append(f"ZIP muy pequeño: {len(zip_content)} bytes")
        
        if len(zip_content) > 5 * 1024 * 1024:
            issues.append(f"ZIP muy grande: {len(zip_content)} bytes")
        
        # Verificar contenido del ZIP
        with zipfile.ZipFile(BytesIO(zip_content), 'r') as verify_zip:
            files = verify_zip.namelist()
            print(f"   📋 Archivos: {files}")
            
            if len(files) != 2:
                issues.append(f"ZIP debe tener 2 archivos, tiene {len(files)}")
            
            if 'dummy/' not in files:
                issues.append("ZIP sin carpeta dummy/")
            
            xml_files = [f for f in files if f.endswith('.xml')]
            if len(xml_files) != 1:
                issues.append(f"ZIP debe tener 1 XML, tiene {len(xml_files)}")
            
            if xml_files:
                xml_in_zip = verify_zip.read(xml_files[0]).decode('utf-8')
                print(f"   📄 XML en ZIP: {len(xml_in_zip)} chars")
                
                if len(xml_in_zip) != len(xml_content.strip()):
                    issues.append("Tamaño XML en ZIP no coincide con original")
                
                if xml_in_zip != xml_content:
                    issues.append("Contenido XML en ZIP modificado")
        
        # Guardar ZIP para análisis manual
        debug_dir = Path('temp') / 'content_analysis'
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        zip_path = debug_dir / f"{xml_filename.replace('.xml', '')}_ANALYSIS.zip"
        with open(zip_path, 'wb') as f:
            f.write(zip_content)
        
        print(f"   💾 ZIP guardado: {zip_path}")
        
    except Exception as e:
        issues.append(f"Error creando ZIP: {e}")
    
    return issues

def analyze_base64_content(documento):
    """Analiza la codificación Base64"""
    
    issues = []
    
    try:
        # Recrear proceso completo
        xml_content = documento.xml_firmado.strip()
        if xml_content.startswith('\ufeff'):
            xml_content = xml_content[1:]
        
        # Crear ZIP
        zip_buffer = BytesIO()
        xml_filename = f"20103129061-01-{documento.serie}-{documento.numero:08d}.xml"
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('dummy/', '')
            zip_file.writestr(xml_filename, xml_content.encode('utf-8'))
        
        zip_content = zip_buffer.getvalue()
        
        # Codificar Base64
        content_base64 = base64.b64encode(zip_content).decode('utf-8')
        
        print(f"   🔐 Base64 longitud: {len(content_base64)} chars")
        print(f"   📋 Base64 preview: {content_base64[:100]}...")
        
        # Verificaciones
        if len(content_base64) < 1000:
            issues.append(f"Base64 muy corto: {len(content_base64)} chars")
        
        # Verificar round-trip
        try:
            decoded_zip = base64.b64decode(content_base64)
            if len(decoded_zip) != len(zip_content):
                issues.append("Base64 round-trip falló")
            else:
                print("   ✅ Base64 round-trip exitoso")
        except Exception as e:
            issues.append(f"Error decodificando Base64: {e}")
        
        # Verificar caracteres válidos
        import string
        valid_b64_chars = set(string.ascii_letters + string.digits + '+/=')
        invalid_chars = set(content_base64) - valid_b64_chars
        
        if invalid_chars:
            issues.append(f"Base64 contiene caracteres inválidos: {invalid_chars}")
        
        # Guardar Base64 para análisis
        debug_dir = Path('temp') / 'content_analysis'
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        b64_path = debug_dir / f"{xml_filename.replace('.xml', '')}_ANALYSIS.b64"
        with open(b64_path, 'w') as f:
            f.write(content_base64)
        
        print(f"   💾 Base64 guardado: {b64_path}")
        
    except Exception as e:
        issues.append(f"Error en análisis Base64: {e}")
    
    return issues

def compare_with_examples():
    """Compara con ejemplos de documentos exitosos conocidos"""
    
    # Ejemplo de XML mínimo que SUNAT acepta
    minimal_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>2.0</cbc:CustomizationID>
    <cbc:ID>F001-00000001</cbc:ID>
    <cbc:IssueDate>2025-07-10</cbc:IssueDate>
    <cbc:InvoiceTypeCode>01</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>PEN</cbc:DocumentCurrencyCode>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">20103129061</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>COMERCIAL LAVAGNA SAC</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">20987654321</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>CLIENTE PRUEBA SAC</cbc:RegistrationName>
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
        <cbc:InvoicedQuantity unitCode="NIU">1.00</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="PEN">100.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Description>PRODUCTO PRUEBA</cbc:Description>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="PEN">100.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
</Invoice>'''
    
    print(f"   📏 XML mínimo: {len(minimal_xml)} chars")
    
    # Crear ZIP del ejemplo
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('dummy/', '')
        zip_file.writestr('20103129061-01-F001-00000001.xml', minimal_xml.encode('utf-8'))
    
    example_zip = zip_buffer.getvalue()
    example_b64 = base64.b64encode(example_zip).decode('utf-8')
    
    print(f"   📦 ZIP ejemplo: {len(example_zip)} bytes")
    print(f"   🔐 Base64 ejemplo: {len(example_b64)} chars")
    
    # Guardar ejemplo para comparación
    debug_dir = Path('temp') / 'content_analysis'
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    with open(debug_dir / 'EJEMPLO_MINIMO.xml', 'w', encoding='utf-8') as f:
        f.write(minimal_xml)
    
    with open(debug_dir / 'EJEMPLO_MINIMO.zip', 'wb') as f:
        f.write(example_zip)
    
    with open(debug_dir / 'EJEMPLO_MINIMO.b64', 'w') as f:
        f.write(example_b64)
    
    print("   💾 Ejemplo mínimo guardado para comparación")

def create_minimal_test():
    """Crea un test con XML mínimo"""
    
    print("\n🧪 CREANDO TEST CON XML MÍNIMO:")
    
    minimal_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>2.0</cbc:CustomizationID>
    <cbc:ID>F001-00000002</cbc:ID>
    <cbc:IssueDate>2025-07-10</cbc:IssueDate>
    <cbc:InvoiceTypeCode>01</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>PEN</cbc:DocumentCurrencyCode>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">20103129061</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>COMERCIAL LAVAGNA SAC</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">20987654321</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>CLIENTE PRUEBA SAC</cbc:RegistrationName>
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
        <cbc:InvoicedQuantity unitCode="NIU">1.00</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="PEN">100.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Description>PRODUCTO MINIMO PRUEBA</cbc:Description>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="PEN">100.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
</Invoice>'''
    
    # Probar envío directo con XML mínimo
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        
        # Crear ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('dummy/', '')
            zip_file.writestr('20103129061-01-F001-00000002.xml', minimal_xml.encode('utf-8'))
        
        zip_content = zip_buffer.getvalue()
        content_base64 = base64.b64encode(zip_content).decode('utf-8')
        
        print(f"   📦 ZIP mínimo: {len(zip_content)} bytes")
        print(f"   🔐 Base64 mínimo: {len(content_base64)} chars")
        
        # Envelope SOAP
        envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:ser="http://service.sunat.gob.pe"
               xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
    <soap:Header>
        <wsse:Security>
            <wsse:UsernameToken>
                <wsse:Username>20103129061MODDATOS</wsse:Username>
                <wsse:Password>MODDATOS</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soap:Header>
    <soap:Body>
        <ser:sendBill>
            <fileName>20103129061-01-F001-00000002.zip</fileName>
            <contentFile>{content_base64}</contentFile>
        </ser:sendBill>
    </soap:Body>
</soap:Envelope>'''
        
        # Enviar
        service_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService"
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'urn:sendBill'
        }
        
        auth = HTTPBasicAuth('20103129061MODDATOS', 'MODDATOS')
        
        print("   🌐 Enviando XML mínimo a SUNAT...")
        
        response = requests.post(
            service_url,
            data=envelope.encode('utf-8'),
            headers=headers,
            auth=auth,
            timeout=60
        )
        
        print(f"   📊 Status: {response.status_code}")
        
        if 'Client.0160' in response.text:
            print("   ❌ Error 0160 PERSISTE con XML mínimo")
            print("   🔍 El problema NO está en el contenido XML")
        else:
            print("   ✅ XML mínimo FUNCIONA!")
            print("   🔍 El problema está en el XML complejo generado")
        
        # Guardar respuesta
        debug_dir = Path('temp') / 'content_analysis'
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        with open(debug_dir / 'RESPUESTA_XML_MINIMO.xml', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print("   💾 Respuesta guardada para análisis")
        
    except Exception as e:
        print(f"   ❌ Error enviando XML mínimo: {e}")

def main():
    print("🔬 ANALIZADOR AVANZADO DE CONTENIDO")
    print("Encuentra la causa exacta del error 0160")
    print()
    
    try:
        analyze_content()
        
        print("\n🧪 EJECUTANDO TEST CON XML MÍNIMO:")
        create_minimal_test()
        
        print("\n📋 ARCHIVOS DE ANÁLISIS CREADOS:")
        debug_dir = Path('temp') / 'content_analysis'
        if debug_dir.exists():
            for file in debug_dir.iterdir():
                print(f"   📄 {file.name}")
        
        print("\n💡 PRÓXIMOS PASOS:")
        print("1. Revisar archivos en temp/content_analysis/")
        print("2. Comparar tu XML con el ejemplo mínimo")
        print("3. Si XML mínimo funciona, simplificar tu XML")
        print("4. Si XML mínimo falla, problema está en red/config")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())