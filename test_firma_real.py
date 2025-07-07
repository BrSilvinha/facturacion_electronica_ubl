import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

from firma_digital import XMLSigner

# Test XML simple
xml_test = '''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
    <cbc:ID xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">TEST-001</cbc:ID>
</Invoice>'''

# Probar firma
signer = XMLSigner()
cert_info = {
    'path': 'certificados/test/test_cert_empresa1.pfx',
    'password': 'test123'
}

try:
    # Cargar certificado
    cert = signer.load_certificate_from_pfx(cert_info['path'], cert_info['password'])
    print("✅ Certificado cargado")
    
    # Firmar XML
    xml_firmado = signer.sign_xml_document(xml_test, cert, 'test-001')
    
    if '<ds:Signature' in xml_firmado:
        print("🎉 ¡FIRMA DIGITAL REAL FUNCIONANDO!")
    else:
        print("⚠️ Firma simulada activada")
        
except Exception as e:
    print(f"❌ Error: {e}")