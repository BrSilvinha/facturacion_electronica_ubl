"""
Excepciones específicas para integración con SUNAT
Ubicación: sunat_integration/exceptions.py
"""

class SUNATError(Exception):
    """Excepción base para errores de SUNAT"""
    def __init__(self, message: str, error_code: str = None, response_data: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.response_data = response_data or {}

class SUNATConnectionError(SUNATError):
    """Error de conexión con servicios SUNAT"""
    pass

class SUNATAuthenticationError(SUNATError):
    """Error de autenticación con SUNAT"""
    pass

class SUNATValidationError(SUNATError):
    """Error de validación de documentos por SUNAT"""
    pass

class SUNATZipError(SUNATError):
    """Error en la generación/procesamiento de archivos ZIP"""
    pass

class SUNATCDRError(SUNATError):
    """Error procesando Constancia de Recepción"""
    pass

class SUNATConfigurationError(SUNATError):
    """Error de configuración de SUNAT"""
    pass

class SUNATTimeoutError(SUNATError):
    """Timeout en operaciones con SUNAT"""
    pass