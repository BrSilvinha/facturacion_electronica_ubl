"""
Script para forzar obtención de CDR real
Archivo: force_cdr.py
"""

import requests
import base64
import zipfile
from io import BytesIO
from requests.auth import HTTPBasicAuth

def force_get_cdr_with_better_soap():
    """Intenta obtener CDR con SOAP mejorado"""
    
    print("🚀 FORZANDO OBTENCIÓN DE CDR REAL")
    print("=" * 50)
    
    # CREDENCIALES CORRECTAS
    ruc = "20103129061"
    usuario_completo = f"{ruc}MODDATOS"
    password = "MODDATOS"
    
    print(f"🔐 Usuario: {usuario_completo}")
    print(f"🔐 Password: {password}")
    
    # XML MÍNIMO pero válido para SUNAT
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">
         
    <ext:UBLExtensions>
        <ext:UBLExtension>
            <ext:ExtensionContent>
                <!-- Placeholder para firma digital -->
            </ext:ExtensionContent>
        </ext:UBLExtension>
    </ext:UBLExtensions>
    
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>2.0</cbc:CustomizationID>
    <cbc:ID>F001-00000001</cbc:ID>
    <cbc:IssueDate>2025-07-09</cbc:IssueDate>
    <cbc:InvoiceTypeCode listAgencyName="PE:SUNAT" 
                        listName="SUNAT:Identificador de Tipo de Documento">01</cbc:InvoiceTypeCode>
    <cbc:Note languageLocaleID="1000">118.00</cbc:Note>
    <cbc:DocumentCurrencyCode listID="ISO 4217 Alpha">PEN</cbc:DocumentCurrencyCode>
    
    <!-- Emisor -->
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">{ruc}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name>COMERCIAL LAVAGNA SAC</cbc:Name>
            </cac:PartyName>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>COMERCIAL LAVAGNA S.A.C.</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <!-- Cliente -->
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">20123456789</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>EMPRESA CLIENTE TEST SAC</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <!-- Totales -->
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="PEN">18.00</cbc:TaxAmount>
    </cac:TaxTotal>
    
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="PEN">100.00</cbc:LineExtensionAmount>
        <cbc:TaxInclusiveAmount currencyID="PEN">118.00</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="PEN">118.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    <!-- Item -->
    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="NIU">1.00</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="PEN">100.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Description>Producto para CDR real</cbc:Description>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="PEN">100.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
</Invoice>"""
    
    # Crear ZIP exacto según SUNAT
    zip_buffer = BytesIO()
    filename_base = f"{ruc}-01-F001-00000001"
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Carpeta dummy OBLIGATORIA
        zip_file.writestr('dummy/', '')
        # XML
        zip_file.writestr(f"{filename_base}.xml", xml_content.encode('utf-8'))
    
    zip_content = zip_buffer.getvalue()
    content_base64 = base64.b64encode(zip_content).decode('utf-8')
    
    print(f"📦 ZIP creado: {len(zip_content)} bytes")
    print(f"📄 Base64: {len(content_base64)} caracteres")
    
    # SOAP Envelope PERFECTO para SUNAT
    soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
    <soap:Header>
        <wsse:Security>
            <wsse:UsernameToken>
                <wsse:Username>{usuario_completo}</wsse:Username>
                <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soap:Header>
    <soap:Body>
        <sendBill xmlns="http://service.sunat.gob.pe">
            <fileName>{filename_base}.zip</fileName>
            <contentFile>{content_base64}</contentFile>
        </sendBill>
    </soap:Body>
</soap:Envelope>"""
    
    # Headers perfectos
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'urn:sendBill',
        'User-Agent': 'Python-SUNAT-CDR-Force/1.0',
        'Accept': 'text/xml, multipart/related',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Content-Length': str(len(soap_envelope.encode('utf-8')))
    }
    
    # URL de servicio
    url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService"
    
    print(f"📡 Enviando a: {url}")
    print(f"📋 Headers: {list(headers.keys())}")
    
    try:
        # Triple autenticación: Headers + Basic Auth + WSSE
        auth = HTTPBasicAuth(usuario_completo, password)
        
        print(f"⏱️ Enviando request...")
        
        response = requests.post(
            url,
            data=soap_envelope.encode('utf-8'),
            headers=headers,
            auth=auth,
            timeout=60,
            verify=True,
            stream=False
        )
        
        print(f"📊 Status: {response.status_code} {response.reason}")
        print(f"📊 Response headers: {dict(response.headers)}")
        print(f"📊 Response size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            response_text = response.text
            print(f"📄 Response preview: {response_text[:300]}...")
            
            # Buscar CDR en diferentes formatos
            cdr_patterns = [
                'applicationResponse',
                'return',
                'ns2:sendBillResponse', 
                'sendBillResponse',
                'ticket'
            ]
            
            found_cdr = False
            
            for pattern in cdr_patterns:
                if pattern in response_text:
                    print(f"🎉 Encontrado patrón '{pattern}' en respuesta!")
                    
                    if pattern == 'applicationResponse':
                        # Extraer CDR
                        start_tag = f'<{pattern}>'
                        end_tag = f'</{pattern}>'
                        
                        start_idx = response_text.find(start_tag)
                        end_idx = response_text.find(end_tag)
                        
                        if start_idx != -1 and end_idx != -1:
                            start_idx += len(start_tag)
                            cdr_base64 = response_text[start_idx:end_idx].strip()
                            
                            if cdr_base64:
                                print(f"🏆 ¡CDR BASE64 EXTRAÍDO!")
                                print(f"📄 CDR Base64 length: {len(cdr_base64)}")
                                
                                # Decodificar y analizar CDR
                                try:
                                    cdr_zip = base64.b64decode(cdr_base64)
                                    print(f"📦 CDR ZIP: {len(cdr_zip)} bytes")
                                    
                                    # Extraer XML del CDR
                                    with zipfile.ZipFile(BytesIO(cdr_zip), 'r') as zf:
                                        files = zf.namelist()
                                        print(f"📁 Archivos en CDR: {files}")
                                        
                                        for file in files:
                                            if file.endswith('.xml'):
                                                cdr_xml = zf.read(file).decode('utf-8')
                                                print(f"📄 CDR XML: {len(cdr_xml)} caracteres")
                                                
                                                # Analizar ResponseCode
                                                if '<cbc:ResponseCode>' in cdr_xml:
                                                    start_code = cdr_xml.find('<cbc:ResponseCode>') + len('<cbc:ResponseCode>')
                                                    end_code = cdr_xml.find('</cbc:ResponseCode>')
                                                    if end_code > start_code:
                                                        resp_code = cdr_xml[start_code:end_code]
                                                        print(f"🔍 Response Code: {resp_code}")
                                                        
                                                        if resp_code == '0':
                                                            print(f"✅ ¡DOCUMENTO ACEPTADO POR SUNAT!")
                                                        else:
                                                            print(f"⚠️ Código de respuesta: {resp_code}")
                                                
                                                # Guardar CDR
                                                cdr_filename = f"cdr_force_{filename_base}.xml"
                                                with open(cdr_filename, 'w', encoding='utf-8') as f:
                                                    f.write(cdr_xml)
                                                print(f"💾 CDR guardado en: {cdr_filename}")
                                                
                                                found_cdr = True
                                                break
                                                
                                except Exception as e:
                                    print(f"❌ Error procesando CDR: {e}")
                    
                    elif pattern == 'ticket':
                        # Buscar ticket para consulta posterior
                        start_idx = response_text.find('<ticket>') + len('<ticket>')
                        end_idx = response_text.find('</ticket>')
                        if start_idx > 7 and end_idx > start_idx:
                            ticket = response_text[start_idx:end_idx]
                            print(f"🎫 Ticket para consulta: {ticket}")
            
            if found_cdr:
                print(f"\n🎉 ¡CDR REAL OBTENIDO EXITOSAMENTE!")
                return True
            else:
                print(f"\n📋 Documento enviado exitosamente pero sin CDR inmediato")
                print(f"💡 Esto puede ser normal en SUNAT Beta")
                return True
        else:
            print(f"❌ ERROR {response.status_code}")
            print(f"📄 Error response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {e}")
        return False

if __name__ == "__main__":
    success = force_get_cdr_with_better_soap()
    
    if success:
        print(f"\n✅ Envío exitoso a SUNAT")
        print(f"🔍 Si no apareció CDR, verificar con: python check_cdr.py")
    else:
        print(f"\n❌ Error en envío")