#!/usr/bin/env python
"""
Generador de certificados de prueba para desarrollo
Ubicación: certificados/generate_test_certs.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import OpenSSL

# Agregar el directorio raíz al path para importar configuraciones Django
sys.path.append(str(Path(__file__).parent.parent))

class TestCertificateGenerator:
    """Generador de certificados de prueba para desarrollo"""
    
    def __init__(self, config_file=None):
        self.base_dir = Path(__file__).parent
        self.test_dir = self.base_dir / 'test'
        self.config_file = config_file or self.test_dir / 'config.ini'
        
        # Asegurar que el directorio existe
        self.test_dir.mkdir(exist_ok=True)
    
    def generate_self_signed_certificate(self, 
                                       common_name: str,
                                       ruc: str,
                                       validity_days: int = 365,
                                       key_size: int = 2048,
                                       country: str = "PE",
                                       state: str = "Lima",
                                       locality: str = "Lima",
                                       organization: str = "Empresa Test",
                                       organizational_unit: str = "IT Department",
                                       email: str = "test@empresa.com") -> tuple:
        """
        Genera un certificado auto-firmado para testing
        
        Returns:
            tuple: (private_key, certificate)
        """
        
        print(f"🔑 Generando certificado para: {common_name} (RUC: {ruc})")
        
        # Generar clave privada
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        
        # Crear el sujeto del certificado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, email),
            # Agregar RUC como parte del distinguished name
            x509.NameAttribute(x509.oid.NameOID.SERIAL_NUMBER, ruc),
        ])
        
        # Configurar fechas de validez
        now = datetime.utcnow()
        
        # Crear el certificado
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            now
        ).not_valid_after(
            now + timedelta(days=validity_days)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(f"{ruc}.test.sunat.gob.pe"),
                x509.DNSName("localhost"),
                x509.RFC822Name(email),
            ]),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=True,  # Para firmas digitales
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                x509.oid.ExtendedKeyUsageOID.EMAIL_PROTECTION,
                # OID específico para firma digital de documentos
                x509.ObjectIdentifier("1.3.6.1.4.1.311.10.3.12"),  # Document Signing
            ]),
            critical=True,
        ).sign(private_key, hashes.SHA256())
        
        return private_key, cert
    
    def create_pfx_file(self, private_key, certificate, password: str, filename: str):
        """Crea archivo PFX con certificado y clave privada"""
        
        print(f"📦 Creando archivo PFX: {filename}")
        
        # Usar pyOpenSSL para crear PFX
        p12 = OpenSSL.crypto.PKCS12()
        
        # Convertir certificado de cryptography a pyOpenSSL
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        openssl_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_pem)
        
        # Convertir clave privada de cryptography a pyOpenSSL
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        openssl_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, key_pem)
        
        # Configurar el P12
        p12.set_certificate(openssl_cert)
        p12.set_privatekey(openssl_key)
        p12.set_friendlyname(f"Certificado Test - {certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value}".encode())
        
        # Generar archivo PFX
        pfx_data = p12.export(password.encode())
        
        # Guardar archivo
        pfx_path = self.test_dir / filename
        with open(pfx_path, 'wb') as f:
            f.write(pfx_data)
        
        return pfx_path
    
    def save_certificate_info(self, certificate, filename_base: str):
        """Guarda información del certificado en archivos separados"""
        
        # Guardar certificado en formato PEM
        cert_pem_path = self.test_dir / f"{filename_base}.pem"
        with open(cert_pem_path, 'wb') as f:
            f.write(certificate.public_bytes(serialization.Encoding.PEM))
        
        # Guardar información del certificado
        info_path = self.test_dir / f"{filename_base}_info.txt"
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(f"# Información del Certificado de Prueba\n")
            f.write(f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Sujeto: {certificate.subject.rfc4514_string()}\n")
            f.write(f"Emisor: {certificate.issuer.rfc4514_string()}\n")
            f.write(f"Válido desde: {certificate.not_valid_before}\n")
            f.write(f"Válido hasta: {certificate.not_valid_after}\n")
            f.write(f"Número de serie: {certificate.serial_number}\n")
            f.write(f"Algoritmo de firma: {certificate.signature_algorithm_oid._name}\n")
            f.write(f"Tamaño de clave: {certificate.public_key().key_size} bits\n")
            
            # Extensiones
            f.write(f"\nExtensiones:\n")
            for extension in certificate.extensions:
                f.write(f"  - {extension.oid._name}: {extension.critical}\n")
        
        return cert_pem_path, info_path
    
    def generate_default_certificates(self):
        """Genera certificados por defecto para testing"""
        
        certificates = [
            {
                'common_name': 'Certificado Test Empresa 1',
                'ruc': '20123456789',
                'filename': 'test_cert_empresa1',
                'password': 'test123',
                'validity_days': 365,
                'organization': 'Empresa Test 1 SAC',
                'email': 'test1@empresa1.com'
            },
            {
                'common_name': 'Certificado Test Empresa 2',
                'ruc': '20987654321',
                'filename': 'test_cert_empresa2',
                'password': 'test456',
                'validity_days': 730,
                'organization': 'Empresa Test 2 EIRL',
                'email': 'test2@empresa2.com'
            }
        ]
        
        generated_certs = []
        
        for cert_config in certificates:
            print(f"\n📋 Configuración: {cert_config['common_name']}")
            
            # Generar certificado
            private_key, certificate = self.generate_self_signed_certificate(
                common_name=cert_config['common_name'],
                ruc=cert_config['ruc'],
                validity_days=cert_config['validity_days'],
                organization=cert_config['organization'],
                email=cert_config['email']
            )
            
            # Crear archivo PFX
            pfx_path = self.create_pfx_file(
                private_key, 
                certificate, 
                cert_config['password'],
                f"{cert_config['filename']}.pfx"
            )
            
            # Guardar información del certificado
            pem_path, info_path = self.save_certificate_info(
                certificate, 
                cert_config['filename']
            )
            
            cert_info = {
                'config': cert_config,
                'pfx_path': pfx_path,
                'pem_path': pem_path,
                'info_path': info_path,
                'certificate': certificate,
                'private_key': private_key
            }
            
            generated_certs.append(cert_info)
            
            print(f"✅ Certificado generado exitosamente:")
            print(f"   📄 PFX: {pfx_path}")
            print(f"   📄 PEM: {pem_path}")
            print(f"   📄 Info: {info_path}")
            print(f"   🔑 Password: {cert_config['password']}")
        
        return generated_certs
    
    def create_summary_file(self, generated_certs):
        """Crea archivo resumen con todos los certificados generados"""
        
        summary_path = self.test_dir / 'certificates_summary.md'
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# 🔐 Resumen de Certificados de Prueba\n\n")
            f.write(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## ⚠️ SOLO PARA DESARROLLO\n\n")
            f.write("Estos certificados son auto-firmados y **NO deben usarse en producción**.\n\n")
            
            f.write("## 📋 Certificados Disponibles\n\n")
            
            for i, cert_info in enumerate(generated_certs, 1):
                config = cert_info['config']
                f.write(f"### {i}. {config['common_name']}\n\n")
                f.write(f"- **RUC:** {config['ruc']}\n")
                f.write(f"- **Organización:** {config['organization']}\n")
                f.write(f"- **Email:** {config['email']}\n")
                f.write(f"- **Archivo PFX:** `{cert_info['pfx_path'].name}`\n")
                f.write(f"- **Password:** `{config['password']}`\n")
                f.write(f"- **Validez:** {config['validity_days']} días\n")
                f.write(f"- **Válido hasta:** {cert_info['certificate'].not_valid_after.strftime('%Y-%m-%d')}\n\n")
            
            f.write("## 🔧 Uso en Desarrollo\n\n")
            f.write("```python\n")
            f.write("# Cargar certificado en tu código\n")
            f.write("cert_path = 'certificados/test/test_cert_empresa1.pfx'\n")
            f.write("password = 'test123'\n")
            f.write("```\n\n")
            f.write("## 🚀 Siguiente Paso\n\n")
            f.write("Estos certificados están listos para usar en el **Nivel 2: Firma Digital Real**.\n")
        
        print(f"\n📋 Resumen creado: {summary_path}")
        return summary_path

def main():
    """Función principal"""
    print("🚀 Generador de Certificados de Prueba - Nivel 2")
    print("=" * 60)
    
    try:
        generator = TestCertificateGenerator()
        
        # Generar certificados por defecto
        generated_certs = generator.generate_default_certificates()
        
        # Crear archivo resumen
        summary_path = generator.create_summary_file(generated_certs)
        
        print("\n" + "=" * 60)
        print("🎉 ¡Certificados de prueba generados exitosamente!")
        print(f"📁 Ubicación: {generator.test_dir}")
        print(f"📋 Resumen: {summary_path}")
        print("\n🔥 ¡Listo para implementar firma digital real!")
        
    except Exception as e:
        print(f"❌ Error generando certificados: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())