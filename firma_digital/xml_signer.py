"""
XMLSigner - Implementación de firma digital XML-DSig para documentos UBL 2.1
Ubicación: firma_digital/xml_signer.py
Versión corregida usando solo cryptography (sin pyOpenSSL)
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from lxml import etree
from signxml import XMLSigner as SignXMLSigner, XMLVerifier
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.serialization import pkcs12
from django.conf import settings

logger = logging.getLogger('signature')

class DigitalSignatureError(Exception):
    """Excepción base para errores de firma digital"""
    pass

class CertificateError(DigitalSignatureError):
    """Errores relacionados con certificados"""
    pass

class SignatureError(DigitalSignatureError):
    """Errores relacionados con el proceso de firma"""
    pass

class XMLSigner:
    """
    Implementa firma digital XML-DSig para documentos UBL 2.1
    Compatible con especificaciones SUNAT y estándares W3C
    Usa únicamente cryptography (sin pyOpenSSL)
    """
    
    def __init__(self):
        self.config = getattr(settings, 'DIGITAL_SIGNATURE_CONFIG', {})
        self.logger = logger
        
        # Configuración de algoritmos
        self.signature_algorithm = self.config.get('SIGNATURE_ALGORITHM', 'RSA-SHA256')
        self.digest_algorithm = self.config.get('DIGEST_ALGORITHM', 'SHA256')
        self.canonicalization_method = self.config.get(
            'CANONICALIZATION_METHOD', 
            'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
        )
        
        self.logger.info(f"XMLSigner inicializado con algoritmo: {self.signature_algorithm}")
    
    def load_certificate_from_pfx(self, pfx_path: str, password: str) -> Dict[str, Any]:
        """
        Carga certificado y clave privada desde archivo PFX usando cryptography
        
        Args:
            pfx_path: Ruta al archivo PFX
            password: Password del archivo PFX
            
        Returns:
            Dict con certificado, clave privada y metadatos
            
        Raises:
            CertificateError: Si hay error cargando el certificado
        """
        
        try:
            self.logger.info(f"Cargando certificado desde: {pfx_path}")
            
            # Leer archivo PFX
            pfx_path = Path(pfx_path)
            if not pfx_path.exists():
                raise CertificateError(f"Archivo PFX no encontrado: {pfx_path}")
            
            with open(pfx_path, 'rb') as f:
                pfx_data = f.read()
            
            # Cargar usando cryptography
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data, 
                password.encode() if isinstance(password, str) else password
            )
            
            if private_key is None or certificate is None:
                raise CertificateError("No se pudo extraer la clave privada o certificado del archivo PFX")
            
            # Convertir a formato PEM para signxml
            cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()
            
            # Extraer metadatos del certificado
            subject_attrs = {}
            for attribute in certificate.subject:
                subject_attrs[attribute.oid._name] = attribute.value
            
            issuer_attrs = {}
            for attribute in certificate.issuer:
                issuer_attrs[attribute.oid._name] = attribute.value
            
            cert_info = {
                'certificate_pem': cert_pem,
                'private_key_pem': key_pem,
                'certificate_obj': certificate,
                'private_key_obj': private_key,
                'additional_certificates': additional_certificates or [],
                'metadata': {
                    'subject_cn': subject_attrs.get('commonName', 'N/A'),
                    'subject_o': subject_attrs.get('organizationName', 'N/A'),
                    'subject_serial': subject_attrs.get('serialNumber', 'N/A'),
                    'issuer_cn': issuer_attrs.get('commonName', 'N/A'),
                    'issuer_o': issuer_attrs.get('organizationName', 'N/A'),
                    'serial_number': str(certificate.serial_number),
                    'not_before': certificate.not_valid_before,
                    'not_after': certificate.not_valid_after,
                    'version': certificate.version.name,
                    'signature_algorithm': certificate.signature_algorithm_oid._name,
                    'key_size': private_key.key_size if hasattr(private_key, 'key_size') else 'N/A'
                }
            }
            
            self.logger.info(f"Certificado cargado exitosamente:")
            self.logger.info(f"  - Sujeto: {cert_info['metadata']['subject_cn']}")
            self.logger.info(f"  - RUC/Serial: {cert_info['metadata']['subject_serial']}")
            self.logger.info(f"  - Válido hasta: {cert_info['metadata']['not_after']}")
            self.logger.info(f"  - Tamaño clave: {cert_info['metadata']['key_size']} bits")
            
            return cert_info
            
        except Exception as e:
            if isinstance(e, CertificateError):
                raise
            raise CertificateError(f"Error cargando certificado: {e}")
    
    def validate_certificate(self, cert_info: Dict[str, Any]) -> bool:
        """
        Valida que el certificado sea válido para firma digital
        
        Args:
            cert_info: Información del certificado
            
        Returns:
            True si es válido
            
        Raises:
            CertificateError: Si el certificado no es válido
        """
        
        metadata = cert_info['metadata']
        now = datetime.now()
        
        # Verificar vigencia - normalizar fechas para comparación
        not_before = metadata['not_before']
        not_after = metadata['not_after']
        
        # Remover timezone info para comparación simple
        if not_before.tzinfo is not None:
            not_before = not_before.replace(tzinfo=None)
        if not_after.tzinfo is not None:
            not_after = not_after.replace(tzinfo=None)
        
        # Debug de fechas
        self.logger.info(f"Validando fechas:")
        self.logger.info(f"  - Ahora: {now}")
        self.logger.info(f"  - Válido desde: {not_before}")
        self.logger.info(f"  - Válido hasta: {not_after}")
        
        if now < not_before:
            raise CertificateError(f"Certificado aún no es válido. Válido desde: {not_before}")
        
        if now > not_after:
            raise CertificateError(f"Certificado expirado. Expiró: {not_after}")
        
        # Verificar tamaño de clave
        allowed_key_sizes = self.config.get('ALLOWED_KEY_SIZES', [2048, 3072, 4096])
        key_size = metadata.get('key_size')
        if key_size != 'N/A' and key_size not in allowed_key_sizes:
            raise CertificateError(f"Tamaño de clave no permitido: {key_size} bits")
        
        # Verificar que tenga RUC/Serial
        if not metadata['subject_serial'] or metadata['subject_serial'] == 'N/A':
            self.logger.warning("Certificado sin número de serie/RUC en el sujeto")
        
        self.logger.info("Certificado validado exitosamente")
        return True
    
    def sign_xml_document(self, xml_content: str, cert_info: Dict[str, Any], 
                         document_id: Optional[str] = None) -> str:
        """
        Firma un documento XML con XML-DSig
        
        Args:
            xml_content: Contenido XML a firmar
            cert_info: Información del certificado
            document_id: ID del documento (opcional)
            
        Returns:
            XML firmado como string
            
        Raises:
            SignatureError: Si hay error en el proceso de firma
        """
        
        try:
            start_time = datetime.now()
            signature_id = document_id or str(uuid.uuid4())
            
            self.logger.info(f"Iniciando firma digital del documento: {signature_id}")
            
            # Validar certificado
            self.validate_certificate(cert_info)
            
            # Parsear XML
            try:
                root = etree.fromstring(xml_content.encode('utf-8'))
            except etree.XMLSyntaxError as e:
                raise SignatureError(f"XML inválido: {e}")
            
            # Verificar que es un documento UBL válido
            if not self._is_valid_ubl_document(root):
                raise SignatureError("El documento no es un XML UBL 2.1 válido")
            
            # Preparar para firma
            self._prepare_xml_for_signature(root, signature_id)
            
            # Configurar firmador
            signer = SignXMLSigner(
                method=self._get_signature_method(),
                digest_algorithm=self.digest_algorithm.lower(),
                c14n_algorithm=self.canonicalization_method
            )
            
            # Firmar documento
            signed_root = signer.sign(
                root,
                key=cert_info['private_key_pem'],
                cert=cert_info['certificate_pem']
            )
            
            # Convertir a string con formato bonito
            signed_xml = etree.tostring(
                signed_root, 
                pretty_print=True, 
                xml_declaration=True, 
                encoding='UTF-8'
            ).decode('utf-8')
            
            # Agregar metadatos de firma
            signed_xml = self._add_signature_metadata(signed_xml, cert_info, signature_id)
            
            # Log de éxito
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.info(f"Documento firmado exitosamente en {duration:.0f}ms")
            self.logger.info(f"  - ID Firma: {signature_id}")
            self.logger.info(f"  - Certificado: {cert_info['metadata']['subject_cn']}")
            self.logger.info(f"  - Algoritmo: {self.signature_algorithm}")
            
            return signed_xml
            
        except (CertificateError, SignatureError):
            raise
        except Exception as e:
            self.logger.error(f"Error inesperado durante la firma: {e}")
            raise SignatureError(f"Error inesperado durante la firma: {e}")
    
    def verify_signature(self, signed_xml: str) -> Dict[str, Any]:
        """
        Verifica la firma digital de un documento XML
        
        Args:
            signed_xml: XML firmado
            
        Returns:
            Dict con resultado de la verificación
            
        Raises:
            SignatureError: Si hay error en la verificación
        """
        
        try:
            self.logger.info("Iniciando verificación de firma digital")
            
            # Parsear XML firmado
            root = etree.fromstring(signed_xml.encode('utf-8'))
            
            # Configurar verificador
            verifier = XMLVerifier()
            
            # Verificar firma
            verified_data = verifier.verify(root)
            
            # Extraer información del certificado
            cert_info = self._extract_certificate_info_from_signature(root)
            
            result = {
                'valid': True,
                'verified_data': verified_data,
                'certificate_info': cert_info,
                'verification_time': datetime.now(),
                'message': 'Firma válida'
            }
            
            self.logger.info("Firma verificada exitosamente")
            return result
            
        except Exception as e:
            self.logger.error(f"Error verificando firma: {e}")
            return {
                'valid': False,
                'error': str(e),
                'verification_time': datetime.now(),
                'message': f'Error en verificación: {e}'
            }
    
    def _get_signature_method(self) -> str:
        """Obtiene el método de firma según la configuración"""
        algorithm_map = {
            'RSA-SHA1': 'rsa-sha1',
            'RSA-SHA256': 'rsa-sha256',
            'RSA-SHA512': 'rsa-sha512'
        }
        return algorithm_map.get(self.signature_algorithm, 'rsa-sha256')
    
    def _is_valid_ubl_document(self, root: etree.Element) -> bool:
        """Verifica si es un documento UBL válido"""
        
        # Verificar namespace UBL
        ubl_namespaces = [
            'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2',
            'urn:oasis:names:specification:ubl:schema:xsd:DebitNote-2'
        ]
        
        return any(ns in root.nsmap.values() for ns in ubl_namespaces if root.nsmap)
    
    def _prepare_xml_for_signature(self, root: etree.Element, signature_id: str):
        """Prepara el XML para firma agregando IDs necesarios"""
        
        # Agregar ID al elemento raíz si no existe
        if 'Id' not in root.attrib:
            root.set('Id', f"doc-{signature_id}")
        
        # Buscar ExtensionContent para firma
        ext_namespaces = {
            'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2'
        }
        
        ext_content = root.find('.//ext:ExtensionContent', ext_namespaces)
        if ext_content is not None:
            ext_content.set('Id', f"ext-{signature_id}")
    
    def _add_signature_metadata(self, signed_xml: str, cert_info: Dict[str, Any], 
                               signature_id: str) -> str:
        """Agrega metadatos de firma como comentarios XML"""
        
        metadata_comment = f"""
<!-- FIRMA DIGITAL XML-DSig -->
<!-- Generado: {datetime.now().isoformat()} -->
<!-- ID Firma: {signature_id} -->
<!-- Certificado: {cert_info['metadata']['subject_cn']} -->
<!-- RUC: {cert_info['metadata']['subject_serial']} -->
<!-- Algoritmo: {self.signature_algorithm} -->
<!-- Sistema: Facturación Electrónica UBL 2.1 Nivel 2 -->
"""
        
        # Insertar después de la declaración XML
        lines = signed_xml.split('\n')
        if lines[0].startswith('<?xml'):
            lines.insert(1, metadata_comment)
        else:
            lines.insert(0, metadata_comment)
        
        return '\n'.join(lines)
    
    def _extract_certificate_info_from_signature(self, root: etree.Element) -> Dict[str, Any]:
        """Extrae información del certificado desde la firma XML"""
        
        # Buscar el certificado en la firma
        ds_namespaces = {'ds': 'http://www.w3.org/2000/09/xmldsig#'}
        
        cert_element = root.find('.//ds:X509Certificate', ds_namespaces)
        if cert_element is not None:
            try:
                import base64
                cert_data = cert_element.text.strip()
                cert_der = base64.b64decode(cert_data)
                
                # Decodificar certificado
                certificate = x509.load_der_x509_certificate(cert_der)
                
                return {
                    'subject': certificate.subject.rfc4514_string(),
                    'issuer': certificate.issuer.rfc4514_string(),
                    'serial_number': str(certificate.serial_number),
                    'not_before': certificate.not_valid_before,
                    'not_after': certificate.not_valid_after
                }
            except Exception as e:
                self.logger.warning(f"No se pudo extraer info del certificado: {e}")
        
        return {}

class CertificateManager:
    """Gestor de certificados con cache y validación"""
    
    def __init__(self):
        self.config = getattr(settings, 'DIGITAL_SIGNATURE_CONFIG', {})
        self.cache_timeout = self.config.get('CERT_CACHE_TIMEOUT', 3600)
        self.logger = logger
        self._certificate_cache = {}
    
    def get_certificate(self, cert_path: str, password: str, 
                       use_cache: bool = True) -> Dict[str, Any]:
        """
        Obtiene certificado con cache opcional
        
        Args:
            cert_path: Ruta al certificado
            password: Password del certificado
            use_cache: Si usar cache o no
            
        Returns:
            Información del certificado
        """
        
        cache_key = f"{cert_path}:{hash(password)}"
        
        # Verificar cache
        if use_cache and cache_key in self._certificate_cache:
            cached_cert = self._certificate_cache[cache_key]
            cache_time = cached_cert.get('cached_at', datetime.min)
            
            if (datetime.now() - cache_time).seconds < self.cache_timeout:
                self.logger.debug(f"Certificado obtenido desde cache: {cert_path}")
                return cached_cert['cert_info']
        
        # Cargar certificado
        signer = XMLSigner()
        cert_info = signer.load_certificate_from_pfx(cert_path, password)
        
        # Guardar en cache
        if use_cache:
            self._certificate_cache[cache_key] = {
                'cert_info': cert_info,
                'cached_at': datetime.now()
            }
        
        return cert_info
    
    def clear_cache(self):
        """Limpia el cache de certificados"""
        self._certificate_cache.clear()
        self.logger.info("Cache de certificados limpiado")

# Instancia global para uso en el sistema
certificate_manager = CertificateManager()