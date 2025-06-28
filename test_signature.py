#!/usr/bin/env python
"""
Script de prueba para el sistema de firma digital
Ubicación: test_signature.py (en la raíz del proyecto)
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

from firma_digital import XMLSigner, certificate_manager
from firma_digital.exceptions import CertificateError, SignatureError

def test_certificate_loading():
    """Prueba de carga de certificados"""
    print("🔐 Probando carga de certificados...")
    
    try:
        # Usar certificado de prueba
        cert_path = 'certificados/test/test_cert_empresa1.pfx'
        password = 'test123'
        
        # Cargar certificado
        cert_info = certificate_manager.get_certificate(cert_path, password)
        
        print("✅ Certificado cargado exitosamente:")
        print(f"   - Sujeto: {cert_info['metadata']['subject_cn']}")
        print(f"   - RUC: {cert_info['metadata']['subject_serial']}")
        print(f"   - Válido hasta: {cert_info['metadata']['not_after']}")
        print(f"   - Algoritmo: {cert_info['metadata']['signature_algorithm']}")
        
        return cert_info
        
    except CertificateError as e:
        print(f"❌ Error cargando certificado: {e}")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def test_xml_signing():
    """Prueba de firma XML"""
    print("\n📝 Probando firma de XML...")
    
    # XML de prueba simple
    test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">
    
    <ext:UBLExtensions>
        <ext:UBLExtension>
            <ext:ExtensionContent>
                <!-- Aquí irá la firma digital -->
            </ext:ExtensionContent>
        </ext:UBLExtension>
    </ext:UBLExtensions>
    
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>2.0</cbc:CustomizationID>
    <cbc:ID>01-F001-00000001</cbc:ID>
    <cbc:IssueDate>2025-06-28</cbc:IssueDate>
    <cbc:InvoiceTypeCode>01</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>PEN</cbc:DocumentCurrencyCode>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID>20123456789</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>Empresa Test 1 SAC</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:LegalMonetaryTotal>
        <cbc:PayableAmount currencyID="PEN">100.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
</Invoice>'''
    
    try:
        # Cargar certificado
        cert_info = test_certificate_loading()
        if not cert_info:
            return False
        
        # Crear firmador
        signer = XMLSigner()
        
        # Firmar XML
        print("🔏 Firmando documento XML...")
        signed_xml = signer.sign_xml_document(
            test_xml, 
            cert_info, 
            document_id="test-document-001"
        )
        
        print("✅ XML firmado exitosamente!")
        print(f"   - Longitud: {len(signed_xml)} caracteres")
        print(f"   - Contiene firma: {'<Signature' in signed_xml}")
        
        # Guardar para inspección
        output_path = Path('logs/test_signed_document.xml')
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(signed_xml)
        
        print(f"   - Guardado en: {output_path}")
        
        # Verificar firma
        print("\n🔍 Verificando firma...")
        verification_result = signer.verify_signature(signed_xml)
        
        if verification_result['valid']:
            print("✅ Firma verificada exitosamente!")
            print(f"   - Mensaje: {verification_result['message']}")
        else:
            print(f"❌ Error verificando firma: {verification_result['error']}")
            return False
        
        return True
        
    except SignatureError as e:
        print(f"❌ Error firmando XML: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal de prueba"""
    print("🚀 TEST DE FIRMA DIGITAL - NIVEL 2")
    print("=" * 50)
    
    success = True
    
    # Prueba 1: Carga de certificados
    cert_info = test_certificate_loading()
    if not cert_info:
        success = False
    
    # Prueba 2: Firma XML
    if cert_info and not test_xml_signing():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("🔥 Sistema de firma digital funcionando correctamente")
        print("📋 Próximo paso: Integrar con API REST")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisar logs para más detalles")
    
    return 0 if success else 1

if __name__ == '__main__':
    exit(main())