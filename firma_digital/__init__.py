"""
Módulo de Firma Digital para Facturación Electrónica UBL 2.1
Implementa firma XML-DSig según estándares W3C y especificaciones SUNAT
"""

from .xml_signer import XMLSigner, CertificateManager, certificate_manager
from .exceptions import (
    DigitalSignatureError, 
    CertificateError, 
    SignatureError, 
    ValidationError, 
    ConfigurationError
)

__version__ = '2.0.0'
__author__ = 'Sistema Facturación Electrónica'

# Exportar clases principales
__all__ = [
    'XMLSigner',
    'CertificateManager', 
    'certificate_manager',
    'DigitalSignatureError',
    'CertificateError',
    'SignatureError', 
    'ValidationError',
    'ConfigurationError'
]