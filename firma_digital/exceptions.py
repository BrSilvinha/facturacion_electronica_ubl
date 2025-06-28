"""
Excepciones específicas para el sistema de firma digital
Ubicación: firma_digital/exceptions.py
"""

class DigitalSignatureError(Exception):
    """Excepción base para errores de firma digital"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

class CertificateError(DigitalSignatureError):
    """Errores relacionados con certificados digitales"""
    pass

class SignatureError(DigitalSignatureError):
    """Errores relacionados con el proceso de firma"""
    pass

class ValidationError(DigitalSignatureError):
    """Errores de validación de documentos o certificados"""
    pass

class ConfigurationError(DigitalSignatureError):
    """Errores de configuración del sistema de firma"""
    pass