"""
Cliente SOAP para integración con servicios SUNAT
Basado en Manual del Programador RS 097-2012/SUNAT
Ubicación: sunat_integration/soap_client.py
VERSIÓN CORREGIDA - Compatible con urllib3 moderno
"""

import base64
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union
from django.conf import settings

import zeep
from zeep import Client
from zeep.wsse.username import UsernameToken
from zeep.transports import Transport
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .utils import (
    get_sunat_credentials, get_wsdl_url, generate_correlation_id,
    parse_sunat_error_response
)
from .exceptions import (
    SUNATConnectionError, SUNATAuthenticationError, 
    SUNATValidationError, SUNATTimeoutError, SUNATError
)
from .zip_generator import zip_generator

logger = logging.getLogger('sunat')

class SUNATSoapClient:
    """
    Cliente SOAP para comunicación con servicios web SUNAT
    
    Implementa todos los métodos definidos en el manual:
    - sendBill: Envío síncrono (facturas, notas)
    - sendSummary: Envío asíncrono (resúmenes, bajas)  
    - sendPack: Envío de lotes
    - getStatus: Consulta de estado por ticket
    - getStatusCdr: Consulta de CDR por datos del comprobante
    """
    
    def __init__(self, service_type: str = 'factura', environment: str = None, lazy_init: bool = False):
        """
        Inicializa cliente SOAP
        
        Args:
            service_type: 'factura', 'guia', 'retencion'
            environment: 'beta' o 'production'
            lazy_init: Si True, no inicializa conexión hasta que se necesite
        """
        
        self.config = settings.SUNAT_CONFIG
        self.service_type = service_type
        self.environment = environment or self.config['ENVIRONMENT']
        
        # Configuración de conexión
        self.timeout = self.config.get('TIMEOUT', 120)
        self.max_retries = self.config.get('MAX_RETRIES', 3)
        self.retry_delay = self.config.get('RETRY_DELAY', 2)
        
        # Cliente SOAP
        self.client = None
        self.session = None
        self.correlation_id = None
        self._initialized = False
        
        # Inicializar cliente solo si no es lazy
        if not lazy_init:
            self._initialize_client()
        
        logger.info(f"SUNATSoapClient creado: {service_type} - {self.environment} (lazy={lazy_init})")
    
    def _ensure_initialized(self):
        """Asegura que el cliente esté inicializado"""
        if not self._initialized:
            self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente SOAP con configuración robusta"""
        
        try:
            # Configurar sesión HTTP con reintentos
            self.session = Session()
            
            # Configurar estrategia de reintentos (CORREGIDO para urllib3 moderno)
            retry_strategy = Retry(
                total=self.max_retries,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],  # CORREGIDO: era method_whitelist
                backoff_factor=1
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
            
            # Configurar transporte
            transport = Transport(
                session=self.session,
                timeout=self.timeout,
                operation_timeout=self.timeout
            )
            
            # Obtener WSDL URL
            wsdl_url = get_wsdl_url(self.service_type, self.environment)
            logger.info(f"Conectando a WSDL: {wsdl_url}")
            
            # Crear cliente SOAP
            self.client = Client(wsdl_url, transport=transport)
            
            # Configurar autenticación WS-Security
            credentials = get_sunat_credentials(self.environment)
            username_token = UsernameToken(
                username=credentials['username'],
                password=credentials['password']
            )
            
            self.client.wsse = username_token
            self._initialized = True
            
            logger.info("Cliente SOAP configurado exitosamente")
            
        except Exception as e:
            logger.error(f"Error inicializando cliente SOAP: {e}")
            raise SUNATConnectionError(f"Error conectando con SUNAT: {e}")
    
    def send_bill(self, documento, xml_firmado: str) -> Dict[str, Any]:
        """
        Envío síncrono de documentos individuales (facturas, notas)
        
        Args:
            documento: Instancia de DocumentoElectronico
            xml_firmado: XML firmado digitalmente
        
        Returns:
            Dict con respuesta de SUNAT
        """
        
        self._ensure_initialized()
        self.correlation_id = generate_correlation_id()
        
        try:
            logger.info(f"[{self.correlation_id}] Enviando documento: {documento.get_numero_completo()}")
            
            # Crear archivo ZIP
            zip_content = zip_generator.create_document_zip(documento, xml_firmado)
            zip_filename = f"{documento.empresa.ruc}-{documento.tipo_documento.codigo}-{documento.serie}-{documento.numero:08d}.zip"
            
            # Codificar en base64
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')
            
            # Preparar parámetros
            start_time = time.time()
            
            # Realizar llamada SOAP
            response = self._execute_with_retry(
                self.client.service.sendBill,
                fileName=zip_filename,
                contentFile=zip_base64
            )
            
            duration = (time.time() - start_time) * 1000
            
            # Procesar respuesta
            if hasattr(response, 'applicationResponse'):
                # Respuesta exitosa con CDR
                cdr_content = base64.b64decode(response.applicationResponse)
                
                result = {
                    'success': True,
                    'method': 'sendBill',
                    'document_id': documento.get_numero_completo(),
                    'zip_filename': zip_filename,
                    'cdr_content': cdr_content,
                    'response_data': response,
                    'duration_ms': duration,
                    'correlation_id': self.correlation_id,
                    'timestamp': datetime.now()
                }
                
                logger.info(f"[{self.correlation_id}] Documento enviado exitosamente en {duration:.0f}ms")
                return result
            
            else:
                # Respuesta inesperada
                raise SUNATError(f"Respuesta inesperada de SUNAT: {response}")
                
        except zeep.exceptions.Fault as e:
            # Error SOAP
            error_info = parse_sunat_error_response(str(e))
            logger.error(f"[{self.correlation_id}] Error SOAP: {e}")
            
            if 'authentication' in str(e).lower():
                raise SUNATAuthenticationError(f"Error de autenticación: {e}")
            else:
                raise SUNATValidationError(f"Error validación SUNAT: {e}", 
                                         error_code=error_info.get('error_code'))
        
        except Exception as e:
            logger.error(f"[{self.correlation_id}] Error enviando documento: {e}")
            raise SUNATError(f"Error enviando documento: {e}")
    
    def send_summary(self, archivo_resumen: str, xml_content: str) -> Dict[str, Any]:
        """
        Envío asíncrono de resúmenes diarios y comunicaciones de baja
        
        Args:
            archivo_resumen: Nombre del archivo (ej: 20123456789-RC-20250628-1)
            xml_content: Contenido XML del resumen
        
        Returns:
            Dict con ticket de SUNAT
        """
        
        self._ensure_initialized()
        self.correlation_id = generate_correlation_id()
        
        try:
            logger.info(f"[{self.correlation_id}] Enviando resumen: {archivo_resumen}")
            
            # Crear archivo ZIP
            zip_content = zip_generator.create_summary_zip(archivo_resumen, xml_content)
            zip_filename = f"{archivo_resumen}.zip"
            
            # Codificar en base64
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')
            
            start_time = time.time()
            
            # Realizar llamada SOAP
            response = self._execute_with_retry(
                self.client.service.sendSummary,
                fileName=zip_filename,
                contentFile=zip_base64
            )
            
            duration = (time.time() - start_time) * 1000
            
            # Procesar respuesta
            if hasattr(response, 'ticket'):
                result = {
                    'success': True,
                    'method': 'sendSummary',
                    'filename': archivo_resumen,
                    'zip_filename': zip_filename,
                    'ticket': response.ticket,
                    'response_data': response,
                    'duration_ms': duration,
                    'correlation_id': self.correlation_id,
                    'timestamp': datetime.now()
                }
                
                logger.info(f"[{self.correlation_id}] Resumen enviado, ticket: {response.ticket}")
                return result
            
            else:
                raise SUNATError(f"Respuesta sin ticket: {response}")
                
        except Exception as e:
            logger.error(f"[{self.correlation_id}] Error enviando resumen: {e}")
            raise SUNATError(f"Error enviando resumen: {e}")
    
    def get_status(self, ticket: str) -> Dict[str, Any]:
        """
        Consulta estado de procesamiento por ticket
        
        Args:
            ticket: Ticket devuelto por sendSummary o sendPack
        
        Returns:
            Dict con estado y CDR si está listo
        """
        
        self._ensure_initialized()
        self.correlation_id = generate_correlation_id()
        
        try:
            logger.info(f"[{self.correlation_id}] Consultando ticket: {ticket}")
            
            start_time = time.time()
            
            # Realizar llamada SOAP
            response = self._execute_with_retry(
                self.client.service.getStatus,
                ticket=ticket
            )
            
            duration = (time.time() - start_time) * 1000
            
            # Procesar respuesta
            if hasattr(response, 'status'):
                status_code = response.status.statusCode
                
                result = {
                    'success': True,
                    'method': 'getStatus',
                    'ticket': ticket,
                    'status_code': status_code,
                    'status_message': getattr(response.status, 'statusMessage', ''),
                    'response_data': response,
                    'duration_ms': duration,
                    'correlation_id': self.correlation_id,
                    'timestamp': datetime.now()
                }
                
                # Estados posibles:
                # 0 = Procesado correctamente
                # 98 = En proceso
                # 99 = Proceso con errores
                
                if status_code == '0':
                    # Procesado correctamente - CDR disponible
                    if hasattr(response.status, 'content'):
                        result['cdr_content'] = base64.b64decode(response.status.content)
                        result['processed'] = True
                        logger.info(f"[{self.correlation_id}] Ticket procesado exitosamente")
                    else:
                        result['processed'] = True
                        result['cdr_content'] = None
                
                elif status_code == '98':
                    # En proceso
                    result['processed'] = False
                    result['in_progress'] = True
                    logger.info(f"[{self.correlation_id}] Ticket en proceso")
                
                elif status_code == '99':
                    # Error en procesamiento
                    result['processed'] = True
                    result['has_errors'] = True
                    if hasattr(response.status, 'content'):
                        result['cdr_content'] = base64.b64decode(response.status.content)
                    logger.warning(f"[{self.correlation_id}] Ticket con errores")
                
                return result
            
            else:
                raise SUNATError(f"Respuesta inesperada: {response}")
                
        except Exception as e:
            logger.error(f"[{self.correlation_id}] Error consultando ticket: {e}")
            raise SUNATError(f"Error consultando ticket: {e}")
    
    def get_status_cdr(self, ruc: str, tipo_documento: str, serie: str, numero: int) -> Dict[str, Any]:
        """
        Consulta CDR por datos del comprobante
        
        Args:
            ruc: RUC del emisor
            tipo_documento: Código de tipo documento (01, 07, 08)
            serie: Serie del documento
            numero: Número del documento
        
        Returns:
            Dict con CDR si está disponible
        """
        
        self._ensure_initialized()
        self.correlation_id = generate_correlation_id()
        
        try:
            logger.info(f"[{self.correlation_id}] Consultando CDR: {ruc}-{tipo_documento}-{serie}-{numero:08d}")
            
            start_time = time.time()
            
            # Realizar llamada SOAP
            response = self._execute_with_retry(
                self.client.service.getStatusCdr,
                rucComprobante=ruc,
                tipoComprobante=tipo_documento,
                serieComprobante=serie,
                numeroComprobante=str(numero)
            )
            
            duration = (time.time() - start_time) * 1000
            
            # Procesar respuesta
            if hasattr(response, 'statusCdr'):
                status_code = response.statusCdr.statusCode
                
                result = {
                    'success': True,
                    'method': 'getStatusCdr',
                    'document_id': f"{tipo_documento}-{serie}-{numero:08d}",
                    'status_code': status_code,
                    'status_message': getattr(response.statusCdr, 'statusMessage', ''),
                    'response_data': response,
                    'duration_ms': duration,
                    'correlation_id': self.correlation_id,
                    'timestamp': datetime.now()
                }
                
                # CDR disponible
                if hasattr(response.statusCdr, 'content') and response.statusCdr.content:
                    result['cdr_content'] = base64.b64decode(response.statusCdr.content)
                    result['cdr_available'] = True
                    logger.info(f"[{self.correlation_id}] CDR encontrado")
                else:
                    result['cdr_available'] = False
                    logger.info(f"[{self.correlation_id}] CDR no disponible")
                
                return result
            
            else:
                raise SUNATError(f"Respuesta inesperada: {response}")
                
        except Exception as e:
            logger.error(f"[{self.correlation_id}] Error consultando CDR: {e}")
            raise SUNATError(f"Error consultando CDR: {e}")
    
    def _execute_with_retry(self, operation, **kwargs):
        """
        Ejecuta operación SOAP con reintentos automáticos
        
        Args:
            operation: Método del servicio SOAP
            **kwargs: Parámetros para el método
        
        Returns:
            Respuesta del servicio
        """
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Backoff exponencial
                    logger.info(f"[{self.correlation_id}] Reintento #{attempt} en {delay}s")
                    time.sleep(delay)
                
                response = operation(**kwargs)
                return response
                
            except zeep.exceptions.TransportError as e:
                last_exception = e
                if 'timeout' in str(e).lower():
                    logger.warning(f"[{self.correlation_id}] Timeout en intento #{attempt + 1}")
                    if attempt == self.max_retries:
                        raise SUNATTimeoutError(f"Timeout después de {self.max_retries} intentos")
                else:
                    logger.warning(f"[{self.correlation_id}] Error transporte en intento #{attempt + 1}: {e}")
                    if attempt == self.max_retries:
                        raise SUNATConnectionError(f"Error de conexión: {e}")
            
            except zeep.exceptions.Fault:
                # Errores SOAP no se reintentan
                raise
            
            except Exception as e:
                last_exception = e
                logger.warning(f"[{self.correlation_id}] Error en intento #{attempt + 1}: {e}")
                if attempt == self.max_retries:
                    raise SUNATError(f"Error después de {self.max_retries} intentos: {e}")
        
        # Si llegamos aquí, falló todos los intentos
        raise SUNATError(f"Operación falló después de {self.max_retries} intentos: {last_exception}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión con SUNAT
        
        Returns:
            Dict con resultado de la prueba
        """
        
        try:
            logger.info("Probando conexión con SUNAT...")
            
            # Inicializar si no está inicializado
            self._ensure_initialized()
            
            # Verificar que el cliente esté inicializado
            if not self.client:
                raise SUNATConnectionError("Cliente SOAP no inicializado")
            
            # Intentar obtener información del servicio
            service_info = {
                'wsdl_url': self.client.wsdl.location,
                'operations': list(self.client.service.__dict__.keys()),
                'environment': self.environment,
                'service_type': self.service_type
            }
            
            logger.info("Conexión SUNAT exitosa")
            
            return {
                'success': True,
                'message': 'Conexión exitosa con SUNAT',
                'service_info': service_info,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error probando conexión: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }

# Función factory para crear clientes
def create_sunat_client(service_type: str = 'factura', environment: str = None) -> SUNATSoapClient:
    """
    Factory function para crear clientes SUNAT
    
    Args:
        service_type: 'factura', 'guia', 'retencion'
        environment: 'beta' o 'production'
    
    Returns:
        Instancia de SUNATSoapClient
    """
    return SUNATSoapClient(service_type, environment, lazy_init=False)

# Variable global para lazy loading
_global_client = None

def get_sunat_client(service_type: str = 'factura', environment: str = None) -> SUNATSoapClient:
    """
    Obtiene cliente SUNAT global con lazy loading
    
    Args:
        service_type: 'factura', 'guia', 'retencion'
        environment: 'beta' o 'production'
    
    Returns:
        Instancia de SUNATSoapClient
    """
    global _global_client
    
    if _global_client is None:
        _global_client = SUNATSoapClient(service_type, environment, lazy_init=True)
    
    return _global_client