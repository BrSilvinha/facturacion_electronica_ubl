"""
Cliente SOAP para integración con servicios SUNAT
VERSIÓN CORREGIDA - Autenticación HTTP en el transporte
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
from requests.auth import HTTPBasicAuth
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
    """Cliente SOAP para comunicación con servicios web SUNAT"""
    
    def __init__(self, service_type: str = 'factura', environment: str = None, lazy_init: bool = False):
        """Inicializa cliente SOAP"""
        
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
        
        print(f"SUNATSoapClient creado: {service_type} - {self.environment} (lazy={lazy_init})")
    
    def _ensure_initialized(self):
        """Asegura que el cliente esté inicializado"""
        if not self._initialized:
            self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente SOAP con configuración robusta"""
        
        try:
            print("🔧 Inicializando cliente SOAP SUNAT...")
            
            # Obtener credenciales
            credentials = get_sunat_credentials(self.environment)
            username = f"{credentials['ruc']}{credentials['username']}"
            password = credentials['password']
            
            print(f"🔐 Configurando autenticación:")
            print(f"   Usuario: {username}")
            print(f"   Password: {'*' * len(password)}")
            print(f"   RUC: {credentials['ruc']}")
            print(f"   Ambiente: {self.environment}")
            
            # Configurar sesión HTTP con autenticación básica
            self.session = Session()
            self.session.auth = HTTPBasicAuth(username, password)
            
            # Configurar headers
            self.session.headers.update({
                'User-Agent': 'FacturacionElectronica/2.0',
                'Accept': 'text/xml,application/xml,application/soap+xml',
                'Content-Type': 'text/xml; charset=utf-8'
            })
            
            # Configurar estrategia de reintentos
            retry_strategy = Retry(
                total=self.max_retries,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
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
            print(f"🌐 Conectando a WSDL: {wsdl_url}")
            
            # Crear cliente SOAP
            self.client = Client(wsdl_url, transport=transport)
            print("✅ Cliente SOAP creado exitosamente")
            
            # Configurar autenticación WS-Security adicional
            username_token = UsernameToken(
                username=username,
                password=password
            )
            
            self.client.wsse = username_token
            self._initialized = True
            
            print("✅ Cliente SOAP configurado exitosamente")
            
        except Exception as e:
            print(f"❌ Error inicializando cliente SOAP: {e}")
            raise SUNATConnectionError(f"Error conectando con SUNAT: {e}")
    
    def send_bill(self, documento, xml_firmado: str) -> Dict[str, Any]:
        """Envío síncrono de documentos individuales"""
        
        self._ensure_initialized()
        self.correlation_id = generate_correlation_id()
        
        try:
            print(f"[{self.correlation_id}] 📤 Enviando documento: {documento.get_numero_completo()}")
            
            # Crear archivo ZIP
            zip_content = zip_generator.create_document_zip(documento, xml_firmado)
            zip_filename = f"{documento.empresa.ruc}-{documento.tipo_documento.codigo}-{documento.serie}-{documento.numero:08d}.zip"
            
            # Codificar en base64
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')
            
            print(f"[{self.correlation_id}] 📦 ZIP creado: {zip_filename} ({len(zip_base64)} chars base64)")
            
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
                
                print(f"[{self.correlation_id}] ✅ Documento enviado exitosamente en {duration:.0f}ms")
                return result
            
            else:
                raise SUNATError(f"Respuesta inesperada de SUNAT: {response}")
                
        except zeep.exceptions.Fault as e:
            print(f"[{self.correlation_id}] ❌ Error SOAP: {e}")
            
            if 'authentication' in str(e).lower() or '401' in str(e):
                raise SUNATAuthenticationError(f"Error de autenticación: {e}")
            else:
                raise SUNATValidationError(f"Error validación SUNAT: {e}")
        
        except Exception as e:
            print(f"[{self.correlation_id}] ❌ Error enviando documento: {e}")
            raise SUNATError(f"Error enviando documento: {e}")
    
    def send_summary(self, archivo_resumen: str, xml_content: str) -> Dict[str, Any]:
        """Envío asíncrono de resúmenes diarios"""
        
        self._ensure_initialized()
        self.correlation_id = generate_correlation_id()
        
        try:
            print(f"[{self.correlation_id}] 📤 Enviando resumen: {archivo_resumen}")
            
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
                
                print(f"[{self.correlation_id}] ✅ Resumen enviado, ticket: {response.ticket}")
                return result
            
            else:
                raise SUNATError(f"Respuesta sin ticket: {response}")
                
        except Exception as e:
            print(f"[{self.correlation_id}] ❌ Error enviando resumen: {e}")
            raise SUNATError(f"Error enviando resumen: {e}")
    
    def get_status(self, ticket: str) -> Dict[str, Any]:
        """Consulta estado de procesamiento por ticket"""
        
        self._ensure_initialized()
        self.correlation_id = generate_correlation_id()
        
        try:
            print(f"[{self.correlation_id}] 🔍 Consultando ticket: {ticket}")
            
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
                
                # Estados posibles
                if status_code == '0':
                    if hasattr(response.status, 'content'):
                        result['cdr_content'] = base64.b64decode(response.status.content)
                        result['processed'] = True
                        print(f"[{self.correlation_id}] ✅ Ticket procesado exitosamente")
                    else:
                        result['processed'] = True
                        result['cdr_content'] = None
                
                elif status_code == '98':
                    result['processed'] = False
                    result['in_progress'] = True
                    print(f"[{self.correlation_id}] ⏳ Ticket en proceso")
                
                elif status_code == '99':
                    result['processed'] = True
                    result['has_errors'] = True
                    if hasattr(response.status, 'content'):
                        result['cdr_content'] = base64.b64decode(response.status.content)
                    print(f"[{self.correlation_id}] ⚠️ Ticket con errores")
                
                return result
            
            else:
                raise SUNATError(f"Respuesta inesperada: {response}")
                
        except Exception as e:
            print(f"[{self.correlation_id}] ❌ Error consultando ticket: {e}")
            raise SUNATError(f"Error consultando ticket: {e}")
    
    def get_status_cdr(self, ruc: str, tipo_documento: str, serie: str, numero: int) -> Dict[str, Any]:
        """Consulta CDR por datos del comprobante"""
        
        self._ensure_initialized()
        self.correlation_id = generate_correlation_id()
        
        try:
            print(f"[{self.correlation_id}] 🔍 Consultando CDR: {ruc}-{tipo_documento}-{serie}-{numero:08d}")
            
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
                    print(f"[{self.correlation_id}] ✅ CDR encontrado")
                else:
                    result['cdr_available'] = False
                    print(f"[{self.correlation_id}] ℹ️ CDR no disponible")
                
                return result
            
            else:
                raise SUNATError(f"Respuesta inesperada: {response}")
                
        except Exception as e:
            print(f"[{self.correlation_id}] ❌ Error consultando CDR: {e}")
            raise SUNATError(f"Error consultando CDR: {e}")
    
    def _execute_with_retry(self, operation, **kwargs):
        """Ejecuta operación SOAP con reintentos automáticos"""
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    print(f"[{self.correlation_id}] 🔄 Reintento #{attempt} en {delay}s")
                    time.sleep(delay)
                
                response = operation(**kwargs)
                return response
                
            except zeep.exceptions.TransportError as e:
                last_exception = e
                if 'timeout' in str(e).lower():
                    print(f"[{self.correlation_id}] ⏱️ Timeout en intento #{attempt + 1}")
                    if attempt == self.max_retries:
                        raise SUNATTimeoutError(f"Timeout después de {self.max_retries} intentos")
                else:
                    print(f"[{self.correlation_id}] 🌐 Error transporte en intento #{attempt + 1}: {e}")
                    if attempt == self.max_retries:
                        raise SUNATConnectionError(f"Error de conexión: {e}")
            
            except zeep.exceptions.Fault:
                # Errores SOAP no se reintentan
                raise
            
            except Exception as e:
                last_exception = e
                print(f"[{self.correlation_id}] ⚠️ Error en intento #{attempt + 1}: {e}")
                if attempt == self.max_retries:
                    raise SUNATError(f"Error después de {self.max_retries} intentos: {e}")
        
        raise SUNATError(f"Operación falló después de {self.max_retries} intentos: {last_exception}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Prueba la conexión con SUNAT"""
        
        try:
            print("🧪 Probando conexión con SUNAT...")
            
            # Inicializar si no está inicializado
            self._ensure_initialized()
            
            # Verificar que el cliente esté inicializado
            if not self.client:
                raise SUNATConnectionError("Cliente SOAP no inicializado")
            
            # Obtener información del servicio
            wsdl_url = get_wsdl_url(self.service_type, self.environment)
            credentials = get_sunat_credentials(self.environment)
            
            service_info = {
                'wsdl_url': wsdl_url,
                'operations': list(self.client.service.__dict__.keys()) if hasattr(self.client, 'service') else [],
                'environment': self.environment,
                'service_type': self.service_type,
                'ruc_configured': credentials['ruc'],
                'username_configured': f"{credentials['ruc']}{credentials['username']}",
                'wsdl_accessible': True
            }
            
            print("✅ Conexión SUNAT exitosa")
            
            return {
                'success': True,
                'message': 'Conexión exitosa con SUNAT',
                'service_info': service_info,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error probando conexión: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.now()
            }

# Función factory para crear clientes
def create_sunat_client(service_type: str = 'factura', environment: str = None) -> SUNATSoapClient:
    """Factory function para crear clientes SUNAT"""
    return SUNATSoapClient(service_type, environment, lazy_init=False)

# Variable global para lazy loading
_global_client = None

def get_sunat_client(service_type: str = 'factura', environment: str = None) -> SUNATSoapClient:
    """Obtiene cliente SUNAT global con lazy loading"""
    global _global_client
    
    if _global_client is None:
        _global_client = SUNATSoapClient(service_type, environment, lazy_init=True)
    
    return _global_client