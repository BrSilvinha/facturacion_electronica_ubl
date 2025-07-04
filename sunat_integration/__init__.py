"""
Módulo de Integración SUNAT para Facturación Electrónica UBL 2.1
Implementa comunicación completa con servicios web SUNAT según manual RS 097-2012/SUNAT
"""

from .soap_client import SUNATSoapClient, sunat_client
from .zip_generator import SUNATZipGenerator, zip_generator
from .cdr_processor import CDRProcessor, cdr_processor
from .utils import (
    get_sunat_filename, get_sunat_credentials, get_wsdl_url,
    validate_ruc_format, generate_correlation_id, is_production_environment
)
from .exceptions import (
    SUNATError, SUNATConnectionError, SUNATAuthenticationError,
    SUNATValidationError, SUNATZipError, SUNATCDRError,
    SUNATConfigurationError, SUNATTimeoutError
)

__version__ = '1.0.0'
__author__ = 'Sistema Facturación Electrónica'

# Exportar clases principales
__all__ = [
    # Clases principales
    'SUNATSoapClient',
    'SUNATZipGenerator', 
    'CDRProcessor',
    
    # Instancias globales
    'sunat_client',
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