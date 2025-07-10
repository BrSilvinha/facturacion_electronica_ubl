#!/usr/bin/env python
"""
Verificar estado del RUC 20103129061 y probar diferentes configuraciones
"""

import os
import sys
import django
import base64
import zipfile
import requests
from io import BytesIO
from pathlib import Path
from requests.auth import HTTPBasicAuth

# Configurar Django
project_path = Path(__file__).parent
sys.path.append(str(project_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

def test_multiple_configurations():
    """Test con múltiples configuraciones para diagnosticar el problema"""
    
    print("🔍 DIAGNÓSTICO COMPLETO RUC REAL 20103129061")
    print("=" * 70)
    
    ruc_real = "20103129061"
    
    # Configuraciones a probar
    configuraciones = [
        {
            'name': 'Configuración Original',
            'ruc': ruc_real,
            'user': 'MODDATOS',
            'password': 'MODDATOS',
            'url': 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService'
        },
        {
            'name': 'Sin Puerto en URL',
            'ruc': ruc_real,
            'user': 'MODDATOS', 
            'password': 'MODDATOS',
            'url': 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService'
        },
        {
            'name': 'Credenciales Beta Alternativas',
            'ruc': ruc_real,
            'user': 'TESTDATOS',
            'password': 'TESTDATOS',
            'url': 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService'
        }
    ]
    
    # XML super mínimo - solo elementos esenciales
    xml_ultra_minimo = f'''<?xml version="1.0" encoding="UTF-8"?>
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
                <cbc:ID schemeID="6">{ruc_real}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>COMERCIAL LAVAGNA S.A.C.</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="1">12345678</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>CLIENTE PRUEBA</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="PEN">0.00</cbc:TaxAmount>
    </cac:TaxTotal>
    
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="PEN">100.00</cbc:LineExtensionAmount>
        <cbc:TaxInclusiveAmount currencyID="PEN">100.00</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="PEN">100.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="NIU">1</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="PEN">100.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Description>TEST</cbc:Description>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="PEN">100.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
</Invoice>'''
    
    print(f"📄 XML Ultra Mínimo: {len(xml_ultra_minimo)} caracteres")
    
    for i, config in enumerate(configuraciones, 1):
        print(f"\n🧪 TEST {i}: {config['name']}")
        print("-" * 50)
        
        usuario_completo = f"{config['ruc']}{config['user']}"
        print(f"👤 Usuario: {usuario_completo}")
        print(f"🔑 Password: {config['password']}")
        print(f"🌐 URL: {config['url']}")
        
        # Crear ZIP específico para esta configuración
        xml_filename = f"{config['ruc']}-01-F001-{str(i).zfill(8)}.xml"
        filename_zip = f"{config['ruc']}-01-F001-{str(i).zfill(8)}.zip"
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
            zip_file.writestr('dummy/', '')
            zip_file.writestr(xml_filename, xml_ultra_minimo.encode('utf-8'))
        
        zip_content = zip_buffer.getvalue()
        content_base64 = base64.b64encode(zip_content).decode('utf-8')
        
        print(f"📦 ZIP: {len(zip_content)} bytes")
        print(f"📄 Base64: {len(content_base64)} chars")
        
        # SOAP envelope
        soap_envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.sunat.gob.pe" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
    <soap:Header>
        <wsse:Security>
            <wsse:UsernameToken>
                <wsse:Username>{usuario_completo}</wsse:Username>
                <wsse:Password>{config['password']}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soap:Header>
    <soap:Body>
        <ser:sendBill>
            <fileName>{filename_zip}</fileName>
            <contentFile>{content_base64}</contentFile>
        </ser:sendBill>
    </soap:Body>
</soap:Envelope>'''
        
        # Enviar
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'urn:sendBill',
            'User-Agent': f'Python-SUNAT-Test-{i}/1.0'
        }
        
        try:
            response = requests.post(
                config['url'],
                data=soap_envelope.encode('utf-8'),
                headers=headers,
                auth=HTTPBasicAuth(usuario_completo, config['password']),
                timeout=60,
                verify=True
            )
            
            print(f"📨 HTTP: {response.status_code}")
            
            if response.status_code == 200:
                response_text = response.text
                
                if 'Client.0160' in response_text:
                    print("❌ Error 0160 persiste")
                elif 'Client.0154' in response_text:
                    print("⚠️ Error 0154: RUC no autorizado o sin perfil")
                elif 'Client.0111' in response_text:
                    print("⚠️ Error 0111: Sin perfil de emisor")
                elif 'Client.0102' in response_text:
                    print("⚠️ Error 0102: Credenciales incorrectas")
                elif 'applicationResponse' in response_text:
                    print("✅ ¡SUCCESS! CDR recibido")
                    print("🎉 ¡CONFIGURACIÓN FUNCIONA!")
                    break
                elif 'Fault' not in response_text:
                    print("✅ Respuesta sin error aparente")
                else:
                    print("❓ Respuesta no clasificada")
                
                # Mostrar parte de la respuesta
                if len(response_text) < 1000:
                    print(f"📋 Respuesta: {response_text[:200]}...")
                    
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 RECOMENDACIONES FINALES")
    print("=" * 70)
    print("1. Verificar con tu ingeniero:")
    print("   - ¿El RUC 20103129061 está dado de alta en SUNAT Beta?")
    print("   - ¿Qué credenciales exactas usar?")
    print("   - ¿Necesita un usuario secundario?")
    print()
    print("2. Si ninguna configuración funciona:")
    print("   - El RUC puede no estar autorizado para Beta")
    print("   - Puede necesitar configuración especial")
    print("   - Puede requerir certificado específico")
    print()
    print("3. Preguntar al ingeniero:")
    print("   - ¿Has enviado documentos exitosamente con este RUC?")
    print("   - ¿Qué herramienta/sistema usa él?")
    print("   - ¿Puede compartir un XML que SÍ funcione?")

if __name__ == '__main__':
    test_multiple_configurations()