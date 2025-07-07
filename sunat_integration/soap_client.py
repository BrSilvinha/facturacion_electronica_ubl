"""
Cliente SOAP para integración con SUNAT - VERSIÓN CORREGIDA
Ubicación: sunat_integration/soap_client.py
Implementa comunicación completa con servicios web SUNAT
"""

import os
import logging
import zipfile
import base64
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Imports de Django
from django.conf import settings

# Imports de requests y zeep
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from zeep import Client, Settings
    from zeep.transports import Transport
    from zeep.wsse.username import UsernameToken
    ZEEP_AVAILABLE = True
except ImportError:
    ZEEP_AVAILABLE = False

# Imports locales
from .utils import (
    get_sunat_credentials, get_wsdl_url, generate_correlation_id,
    sanitize_xml_content, parse_sunat_error_response
)
from .exceptions import (
    SUNATError, SUNATConnectionError, SUNATAuthenticationError,
    SUNATValidationError, SUNATTimeoutError, SUNATConfigurationError
)

logger = logging.getLogger('sunat')

class SUNATSoapClient:
    """
    Cliente SOAP para comunicación con servicios web SUNAT
    Soporta sendBill, sendSummary, getStatus y getStatusCdr
    """
    
    def __init__(self, service_type: str = 'factura', environment: str = None, lazy_init: bool = True):
        """
        Inicializa cliente SOAP para SUNAT
        
        Args:
            service_type: Tipo de servicio ('factura', 'guia', 'retencion')
            environment: Ambiente ('beta', 'production')
            lazy_init: Si True, inicializa el cliente solo cuando se necesita
        """
        self.service_type = service_type
        self.environment = environment or settings.SUNAT_CONFIG['ENVIRONMENT']
        self.config = settings.SUNAT_CONFIG
        self.lazy_init = lazy_init
        
        # Cliente zeep
        self.zeep_client = None
        self.session = None
        self.transport = None
        
        # URLs y credenciales
        self.wsdl_url = get_wsdl_url(service_type, self.environment)
        self.credentials = get_sunat_credentials(self.environment)
        
        # Usuario completo para autenticación
        self.full_username = f"{self.credentials['ruc']}{self.credentials['username']}"
        
        logger.info(f"SUNATSoapClient inicializado:")
        logger.info(f"  - Servicio: {service_type}")
        logger.info(f"  - Ambiente: {self.environment}")
        logger.info(f"  - WSDL: {self.wsdl_url}")
        logger.info(f"  - Usuario: {self.full_username}")
        
        # Inicializar inmediatamente si no es lazy
        if not lazy_init:
            self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente SOAP zeep"""
        if self.zeep_client is not None:
            return  # Ya inicializado
        
        if not ZEEP_AVAILABLE:
            raise SUNATConfigurationError("zeep no está disponible. Instalar con: pip install zeep")
        
        try:
            logger.info("🔧 Inicializando cliente SOAP SUNAT...")
            
            # Configurar sesión HTTP
            self._setup_session()
            
            # Configurar transporte
            self._setup_transport()
            
            # Crear cliente zeep
            self._create_zeep_client()
            
            # Configurar autenticación WS-Security
            self._setup_wsse()
            
            logger.info("✅ Cliente SOAP SUNAT inicializado exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando cliente SOAP: {e}")
            raise SUNATConnectionError(f"Error conectando con SUNAT: {e}")
    
    def _setup_session(self):
        """Configura sesión HTTP con autenticación y reintentos"""
        logger.debug("🔐 Configurando autenticación:")
        logger.debug(f"   Usuario: {self.full_username}")
        logger.debug(f"   Password: {'*' * len(self.credentials['password'])}")
        logger.debug(f"   RUC: {self.credentials['ruc']}")
        logger.debug(f"   Ambiente: {self.environment}")
        
        self.session = requests.Session()
        
        # Autenticación HTTP Basic
        self.session.auth = HTTPBasicAuth(
            self.full_username,
            self.credentials['password']
        )
        
        # Headers estándar
        self.session.headers.update({
            'User-Agent': 'Python-SUNAT-Client/2.0',
            'Accept': 'text/xml,application/xml,application/soap+xml,*/*',
            'Content-Type': 'text/xml; charset=utf-8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
        
        # Configurar reintentos
        retry_strategy = Retry(
            total=self.config.get('MAX_RETRIES', 3),
            backoff_factor=self.config.get('RETRY_DELAY', 2),
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Verificar SSL pero ser permisivo
        self.session.verify = True
    
    def _setup_transport(self):
        """Configura transporte zeep"""
        timeout = self.config.get('TIMEOUT', 120)
        
        self.transport = Transport(
            session=self.session,
            timeout=timeout,
            operation_timeout=timeout,
            cache=False  # Deshabilitar cache para evitar problemas
        )
    
    def _create_zeep_client(self):
        """Crea cliente zeep"""
        logger.debug(f"🌐 Conectando a WSDL: {self.wsdl_url}")
        
        # Configuración zeep permisiva
        settings_zeep = Settings(
            strict=False,
            xml_huge_tree=True,
            forbid_entities=False,
            forbid_external=False,
            forbid_dtd=False,
            raw_response=False,
            xsd_ignore_sequence_order=True
        )
        
        try:
            self.zeep_client = Client(
                wsdl=self.wsdl_url,
                transport=self.transport,
                settings=settings_zeep
            )
            
        except Exception as e:
            # Si falla, intentar con WSDL local
            logger.warning(f"Error con WSDL remoto: {e}")
            logger.info("Intentando con WSDL local...")
            self._create_zeep_client_with_local_wsdl()
    
    def _create_zeep_client_with_local_wsdl(self):
        """Crea cliente zeep descargando WSDL localmente"""
        try:
            # Descargar WSDL
            response = self.session.get(self.wsdl_url, timeout=30)
            response.raise_for_status()
            
            # Guardar temporalmente
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.wsdl', delete=False) as f:
                f.write(response.text)
                local_wsdl_path = f.name
            
            # Crear cliente con archivo local
            settings_zeep = Settings(strict=False, xml_huge_tree=True)
            
            self.zeep_client = Client(
                wsdl=f"file://{local_wsdl_path}",
                transport=self.transport,
                settings=settings_zeep
            )
            
            # Limpiar archivo temporal
            try:
                os.unlink(local_wsdl_path)
            except:
                pass
            
            logger.info("✅ Cliente creado con WSDL local")
            
        except Exception as e:
            raise SUNATConnectionError(f"Error creando cliente con WSDL local: {e}")
    
    def _setup_wsse(self):
        """Configura WS-Security para autenticación SOAP"""
        if self.zeep_client:
            wsse = UsernameToken(
                username=self.full_username,
                password=self.credentials['password'],
                use_digest=False  # SUNAT usa texto plano
            )
            self.zeep_client.wsse = wsse
            logger.debug("✅ WS-Security configurado")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión con SUNAT
        
        Returns:
            Dict con resultado de la prueba
        """
        start_time = datetime.now()
        correlation_id = generate_correlation_id()
        
        try:
            logger.info(f"[{correlation_id}] Probando conexión SUNAT...")
            
            # Inicializar cliente si es necesario
            if self.zeep_client is None:
                self._initialize_client()
            
            # Verificar operaciones disponibles
            operations = []
            if hasattr(self.zeep_client, 'service'):
                operations = [op for op in dir(self.zeep_client.service) if not op.startswith('_')]
            
            # Verificar operaciones críticas
            required_operations = ['sendBill', 'getStatus']
            available_operations = [op for op in operations if op in required_operations]
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result = {
                'success': True,
                'service_info': {
                    'service_type': self.service_type,
                    'environment': self.environment,
                    'wsdl_url': self.wsdl_url,
                    'username': self.full_username,
                    'operations': operations,
                    'critical_operations': available_operations,
                    'authentication_ok': len(available_operations) > 0
                },
                'timestamp': datetime.now(),
                'duration_ms': duration_ms,
                'correlation_id': correlation_id
            }
            
            logger.info(f"[{correlation_id}] Conexión exitosa en {duration_ms}ms")
            logger.info(f"[{correlation_id}] Operaciones disponibles: {len(operations)}")
            
            return result
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.error(f"[{correlation_id}] Error en test de conexión: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(),
                'duration_ms': duration_ms,
                'correlation_id': correlation_id
            }
    
    def send_bill(self, documento, xml_firmado: str) -> Dict[str, Any]:
        """
        Envía documento individual a SUNAT (sendBill)
        
        Args:
            documento: Instancia de DocumentoElectronico
            xml_firmado: XML firmado digitalmente
            
        Returns:
            Dict con respuesta de SUNAT
        """
        start_time = datetime.now()
        correlation_id = generate_correlation_id()
        
        try:
            logger.info(f"[{correlation_id}] Enviando documento: {documento.get_numero_completo()}")
            
            # Inicializar cliente si es necesario
            if self.zeep_client is None:
                self._initialize_client()
            
            # Generar archivo ZIP
            from .zip_generator import zip_generator
            zip_content = zip_generator.create_document_zip(documento, xml_firmado)
            
            # Codificar en base64
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')
            
            # Generar nombre de archivo
            from .utils import get_sunat_filename
            filename = get_sunat_filename(documento, 'zip')
            
            logger.debug(f"[{correlation_id}] Archivo: {filename}")
            logger.debug(f"[{correlation_id}] ZIP: {len(zip_content)} bytes")
            
            # Llamar servicio sendBill
            response = self.zeep_client.service.sendBill(
                fileName=filename,
                contentFile=zip_base64
            )
            
            # Procesar respuesta
            cdr_content = None
            if hasattr(response, 'applicationResponse'):
                cdr_content = base64.b64decode(response.applicationResponse)
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result = {
                'success': True,
                'method': 'sendBill',
                'filename': filename,
                'cdr_content': cdr_content,
                'raw_response': response,
                'duration_ms': duration_ms,
                'correlation_id': correlation_id,
                'timestamp': datetime.now()
            }
            
            logger.info(f"[{correlation_id}] Documento enviado exitosamente en {duration_ms}ms")
            
            return result
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.error(f"[{correlation_id}] Error enviando documento: {e}")
            
            # Clasificar error
            if '401' in str(e) or 'authentication' in str(e).lower():
                raise SUNATAuthenticationError(f"Error de autenticación: {e}")
            elif 'validation' in str(e).lower() or 'invalid' in str(e).lower():
                raise SUNATValidationError(f"Error de validación: {e}")
            elif 'timeout' in str(e).lower():
                raise SUNATTimeoutError(f"Timeout en operación: {e}")
            else:
                raise SUNATError(f"Error enviando documento: {e}")
    
    def send_summary(self, filename: str, xml_content: str) -> Dict[str, Any]:
        """
        Envía resumen diario a SUNAT (sendSummary)
        
        Args:
            filename: Nombre del archivo resumen
            xml_content: Contenido XML del resumen
            
        Returns:
            Dict con respuesta de SUNAT (incluye ticket)
        """
        start_time = datetime.now()
        correlation_id = generate_correlation_id()
        
        try:
            logger.info(f"[{correlation_id}] Enviando resumen: {filename}")
            
            # Inicializar cliente si es necesario
            if self.zeep_client is None:
                self._initialize_client()
            
            # Generar archivo ZIP
            from .zip_generator import zip_generator
            zip_content = zip_generator.create_summary_zip(filename, xml_content)
            
            # Codificar en base64
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')
            zip_filename = f"{filename}.zip"
            
            logger.debug(f"[{correlation_id}] Archivo: {zip_filename}")
            logger.debug(f"[{correlation_id}] ZIP: {len(zip_content)} bytes")
            
            # Llamar servicio sendSummary
            response = self.zeep_client.service.sendSummary(
                fileName=zip_filename,
                contentFile=zip_base64
            )
            
            # Extraer ticket
            ticket = None
            if hasattr(response, 'ticket'):
                ticket = response.ticket
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result = {
                'success': True,
                'method': 'sendSummary',
                'filename': zip_filename,
                'ticket': ticket,
                'raw_response': response,
                'duration_ms': duration_ms,
                'correlation_id': correlation_id,
                'timestamp': datetime.now()
            }
            
            logger.info(f"[{correlation_id}] Resumen enviado exitosamente en {duration_ms}ms")
            logger.info(f"[{correlation_id}] Ticket recibido: {ticket}")
            
            return result
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.error(f"[{correlation_id}] Error enviando resumen: {e}")
            
            # Clasificar error
            if '401' in str(e) or 'authentication' in str(e).lower():
                raise SUNATAuthenticationError(f"Error de autenticación: {e}")
            elif 'validation' in str(e).lower() or 'invalid' in str(e).lower():
                raise SUNATValidationError(f"Error de validación: {e}")
            elif 'timeout' in str(e).lower():
                raise SUNATTimeoutError(f"Timeout en operación: {e}")
            else:
                raise SUNATError(f"Error enviando resumen: {e}")
    
    def get_status(self, ticket: str) -> Dict[str, Any]:
        """
        Consulta estado de procesamiento por ticket (getStatus)
        
        Args:
            ticket: Ticket devuelto por sendSummary
            
        Returns:
            Dict con estado del procesamiento
        """
        start_time = datetime.now()
        correlation_id = generate_correlation_id()
        
        try:
            logger.info(f"[{correlation_id}] Consultando ticket: {ticket}")
            
            # Inicializar cliente si es necesario
            if self.zeep_client is None:
                self._initialize_client()
            
            # Llamar servicio getStatus
            response = self.zeep_client.service.getStatus(ticket=ticket)
            
            # Procesar respuesta
            status_code = getattr(response, 'statusCode', None)
            content = getattr(response, 'content', None)
            
            # Decodificar contenido CDR si existe
            cdr_content = None
            if content:
                try:
                    cdr_content = base64.b64decode(content)
                except:
                    pass
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Interpretar estado
            processed = status_code in ['0', '99']  # 0=Procesado, 99=En proceso
            in_progress = status_code == '99'
            has_errors = status_code not in ['0', '99']
            
            result = {
                'success': True,
                'method': 'getStatus',
                'ticket': ticket,
                'status_code': status_code,
                'status_message': self._get_status_message(status_code),
                'processed': processed,
                'in_progress': in_progress,
                'has_errors': has_errors,
                'cdr_content': cdr_content,
                'raw_response': response,
                'duration_ms': duration_ms,
                'correlation_id': correlation_id,
                'timestamp': datetime.now()
            }
            
            logger.info(f"[{correlation_id}] Consulta exitosa en {duration_ms}ms")
            logger.info(f"[{correlation_id}] Estado: {status_code} - {result['status_message']}")
            
            return result
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.error(f"[{correlation_id}] Error consultando ticket: {e}")
            
            # Clasificar error
            if '401' in str(e) or 'authentication' in str(e).lower():
                raise SUNATAuthenticationError(f"Error de autenticación: {e}")
            elif 'timeout' in str(e).lower():
                raise SUNATTimeoutError(f"Timeout en operación: {e}")
            else:
                raise SUNATError(f"Error consultando ticket: {e}")
    
    def get_status_cdr(self, ruc: str, document_type: str, series: str, number: int) -> Dict[str, Any]:
        """
        Consulta CDR por datos del comprobante (getStatusCdr)
        
        Args:
            ruc: RUC del emisor
            document_type: Tipo de documento (01, 03, etc.)
            series: Serie del documento
            number: Número del documento
            
        Returns:
            Dict con CDR del documento
        """
        start_time = datetime.now()
        correlation_id = generate_correlation_id()
        
        try:
            document_id = f"{ruc}-{document_type}-{series}-{number:08d}"
            logger.info(f"[{correlation_id}] Consultando CDR: {document_id}")
            
            # Inicializar cliente si es necesario
            if self.zeep_client is None:
                self._initialize_client()
            
            # Llamar servicio getStatusCdr
            response = self.zeep_client.service.getStatusCdr(
                rucComprobante=ruc,
                tipoComprobante=document_type,
                serieComprobante=series,
                numeroComprobante=str(number)
            )
            
            # Procesar respuesta
            status_code = getattr(response, 'statusCode', None)
            content = getattr(response, 'content', None)
            
            # Decodificar contenido CDR
            cdr_content = None
            cdr_available = False
            if content:
                try:
                    cdr_content = base64.b64decode(content)
                    cdr_available = True
                except:
                    pass
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result = {
                'success': True,
                'method': 'getStatusCdr',
                'document_id': document_id,
                'status_code': status_code,
                'status_message': self._get_status_message(status_code),
                'cdr_available': cdr_available,
                'cdr_content': cdr_content,
                'raw_response': response,
                'duration_ms': duration_ms,
                'correlation_id': correlation_id,
                'timestamp': datetime.now()
            }
            
            logger.info(f"[{correlation_id}] Consulta CDR exitosa en {duration_ms}ms")
            logger.info(f"[{correlation_id}] CDR disponible: {cdr_available}")
            
            return result
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.error(f"[{correlation_id}] Error consultando CDR: {e}")
            
            # Clasificar error
            if '401' in str(e) or 'authentication' in str(e).lower():
                raise SUNATAuthenticationError(f"Error de autenticación: {e}")
            elif 'timeout' in str(e).lower():
                raise SUNATTimeoutError(f"Timeout en operación: {e}")
            else:
                raise SUNATError(f"Error consultando CDR: {e}")
    
    def _get_status_message(self, status_code: str) -> str:
        """Obtiene mensaje descriptivo del código de estado"""
        status_messages = {
            '0': 'Procesado correctamente',
            '99': 'En proceso',
            '98': 'Error en procesamiento',
            '97': 'Archivo no válido',
            '96': 'Archivo duplicado',
            '95': 'Error interno del sistema'
        }
        
        return status_messages.get(status_code, f'Estado desconocido: {status_code}')

# Factory functions para crear clientes

def create_sunat_client(service_type: str = 'factura', environment: str = None, **kwargs) -> SUNATSoapClient:
    """
    Factory function para crear cliente SUNAT
    
    Args:
        service_type: Tipo de servicio
        environment: Ambiente
        **kwargs: Argumentos adicionales
        
    Returns:
        Instancia de SUNATSoapClient
    """
    return SUNATSoapClient(
        service_type=service_type,
        environment=environment,
        **kwargs
    )

# Cache de clientes para evitar reconexiones
_client_cache = {}

def get_sunat_client(service_type: str = 'factura', environment: str = None) -> SUNATSoapClient:
    """
    Obtiene cliente SUNAT con cache (lazy loading)
    
    Args:
        service_type: Tipo de servicio
        environment: Ambiente
        
    Returns:
        Instancia de SUNATSoapClient (cacheada)
    """
    env = environment or settings.SUNAT_CONFIG['ENVIRONMENT']
    cache_key = f"{service_type}_{env}"
    
    if cache_key not in _client_cache:
        _client_cache[cache_key] = SUNATSoapClient(
            service_type=service_type,
            environment=env,
            lazy_init=True  # Inicialización perezosa
        )
    
    return _client_cache[cache_key]

def clear_client_cache():
    """Limpia el cache de clientes"""
    global _client_cache
    _client_cache.clear()
    logger.info("Cache de clientes SUNAT limpiado")