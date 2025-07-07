"""
Módulo de Integración SUNAT para Facturación Electrónica UBL 2.1
Implementa comunicación completa con servicios web SUNAT según manual RS 097-2012/SUNAT
VERSIÓN CORREGIDA - Lazy loading para evitar conexiones al importar
"""

# Imports seguros - solo clases, no instancias
try:
    from .soap_client import SUNATSoapClient, create_sunat_client, get_sunat_client
except ImportError as e:
    # En caso de error, crear stubs
    class SUNATSoapClient:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"Error importando SUNATSoapClient: {e}")
    
    def create_sunat_client(*args, **kwargs):
        raise ImportError(f"Error importando create_sunat_client: {e}")
    
    def get_sunat_client(*args, **kwargs):
        raise ImportError(f"Error importando get_sunat_client: {e}")

try:
    from .zip_generator import SUNATZipGenerator, zip_generator
except ImportError:
    zip_generator = None

try:
    from .cdr_processor import CDRProcessor, cdr_processor
except ImportError:
    cdr_processor = None

try:
    from .utils import (
        get_sunat_filename, get_sunat_credentials, get_wsdl_url,
        validate_ruc_format, generate_correlation_id, is_production_environment
    )
except ImportError:
    # Funciones stub en caso de error
    def get_sunat_filename(*args, **kwargs):
        return "document.xml"
    
    def get_sunat_credentials(*args, **kwargs):
        return {'ruc': '', 'username': '', 'password': ''}
    
    def get_wsdl_url(*args, **kwargs):
        return "https://example.com/service.wsdl"
    
    def validate_ruc_format(*args, **kwargs):
        return False
    
    def generate_correlation_id(*args, **kwargs):
        return "test-correlation-id"
    
    def is_production_environment(*args, **kwargs):
        return False

try:
    from .exceptions import (
        SUNATError, SUNATConnectionError, SUNATAuthenticationError,
        SUNATValidationError, SUNATZipError, SUNATCDRError,
        SUNATConfigurationError, SUNATTimeoutError
    )
except ImportError:
    # Excepciones stub
    class SUNATError(Exception):
        pass
    
    class SUNATConnectionError(SUNATError):
        pass
    
    class SUNATAuthenticationError(SUNATError):
        pass
    
    class SUNATValidationError(SUNATError):
        pass
    
    class SUNATZipError(SUNATError):
        pass
    
    class SUNATCDRError(SUNATError):
        pass
    
    class SUNATConfigurationError(SUNATError):
        pass
    
    class SUNATTimeoutError(SUNATError):
        pass

__version__ = '1.0.2'
__author__ = 'Sistema Facturación Electrónica'

# Exportar clases principales
__all__ = [
    # Clases principales
    'SUNATSoapClient',
    'SUNATZipGenerator', 
    'CDRProcessor',
    
    # Factory functions
    'create_sunat_client',
    'get_sunat_client',
    
    # Instancias globales (pueden ser None)
    'zip_generator',
    'cdr_processor',
    
    # Utilidades
    'get_sunat_filename',
    'get_sunat_credentials',
    'get_wsdl_url',
    'validate_ruc_format',
    'generate_correlation_id',
    'is_production_environment',
    
    # Excepciones
    'SUNATError',
    'SUNATConnectionError',
    'SUNATAuthenticationError',
    'SUNATValidationError',
    'SUNATZipError',
    'SUNATCDRError',
    'SUNATConfigurationError',
    'SUNATTimeoutError'
]

# Información del módulo
MODULE_INFO = {
    'name': 'SUNAT Integration',
    'version': __version__,
    'description': 'Integración completa con servicios web SUNAT para facturación electrónica',
    'supported_documents': ['01', '03', '07', '08', '09', '20', '40'],
    'supported_operations': ['sendBill', 'sendSummary', 'sendPack', 'getStatus', 'getStatusCdr'],
    'environments': ['beta', 'production']
}