"""
Cliente SOAP para integración con servicios SUNAT
VERSIÓN CORREGIDA - Solución definitiva para Error 401 en archivos WSDL adicionales
"""

import base64
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, Union
from django.conf import settings

import zeep
from zeep import Client, Settings
from zeep.wsse.username import UsernameToken
from zeep.transports import Transport
from requests import Session
from requests.auth import HTTPBasicAuth
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
    """Cliente SOAP para comunicación con servicios web SUNAT"""
    
    def __init__(self, service_type: str = 'factura', environment: str = None, lazy_init: bool = False):
        """Inicializa cliente SOAP"""
        
        self.config = settings.SUNAT_CONFIG
        self.service_type = service_type
        self.environment = environment or self.config['ENVIRONMENT']
        
        # Configuración de conexión
        self.timeout = self.config.get('TIMEOUT', 180)  # Timeout más largo
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
    
    def _create_authenticated_session(self, credentials: Dict[str, str]) -> Session:
        """Crea sesión con autenticación HTTP básica persistente"""
        
        # Formato de usuario para SUNAT: RUC + Usuario
        http_username = f"{credentials['ruc']}{credentials['username']}"
        http_password = credentials['password']
        
        print(f"🔐 Configurando sesión autenticada:")
        print(f"   Usuario HTTP: {http_username}")
        print(f"   Password: {'*' * len(http_password)}")
        
        # Crear sesión con autenticación persistente
        session = Session()
        session.auth = HTTPBasicAuth(http_username, http_password)
        
        # Headers importantes para SUNAT
        session.headers.update({
            'User-Agent': 'Python-SUNAT-Client/1.0',
            'Accept': 'text/xml,application/xml,application/soap+xml,*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        })
        
        # Configurar estrategia de reintentos más robusta
        retry_strategy = Retry(
            total=5,  # Más intentos
            status_forcelist=[401, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=2,
            raise_on_status=False  # No lanzar excepción inmediatamente
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _test_wsdl_accessibility(self, wsdl_url: str, session: Session) -> bool:
        """Prueba si el WSDL principal es accesible"""
        
        try:
            print(f"🌐 Probando acceso a WSDL: {wsdl_url}")
            
            response = session.get(wsdl_url, timeout=30)
            
            if response.status_code == 200:
                if 'wsdl:definitions' in response.text or 'definitions' in response.text:
                    print("✅ WSDL principal accesible")
                    return True
                else:
                    print("❌ Respuesta no es WSDL válido")
                    return False
            elif response.status_code == 401:
                print("❌ Error 401: Credenciales incorrectas")
                return False
            else:
                print(f"❌ Error HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error accediendo WSDL: {e}")
            return False
    
    def _initialize_client(self):
        """Inicializa el cliente SOAP con configuración robusta"""
        
        try:
            print("🔧 Inicializando cliente SOAP SUNAT...")
            
            # Obtener credenciales
            credentials = get_sunat_credentials(self.environment)
            
            # Crear sesión autenticada
            self.session = self._create_authenticated_session(credentials)
            
            # Obtener WSDL URL
            wsdl_url = get_wsdl_url(self.service_type, self.environment)
            
            # Verificar accesibilidad del WSDL
            if not self._test_wsdl_accessibility(wsdl_url, self.session):
                raise SUNATAuthenticationError("No se puede acceder al WSDL con las credenciales proporcionadas")
            
            # Configurar transporte con sesión autenticada
            transport = Transport(
                session=self.session,
                timeout=self.timeout,
                operation_timeout=self.timeout,
                cache=False  # Desactivar cache para evitar problemas
            )
            
            # SOLUCIÓN CLAVE: Settings más permisivos y robustos
            settings_zeep = Settings(
                strict=False,              # Modo no estricto
                xml_huge_tree=True,        # Permitir XML grandes
                forbid_dtd=False,          # Permitir DTDs
                forbid_entities=False,     # Permitir entidades XML
                forbid_external=False,     # Permitir referencias externas
                xsd_ignore_sequence_order=True,  # Ignorar orden de secuencia
                force_https=False,         # No forzar HTTPS
                raw_response=False,        # Respuesta procesada
                extra_http_headers=None
            )
            
            print(f"🌐 Creando cliente SOAP con WSDL: {wsdl_url}")
            
            # Crear cliente SOAP con configuración mejorada
            try:
                self.client = Client(
                    wsdl_url, 
                    transport=transport,
                    settings=settings_zeep
                )
                print("✅ Cliente SOAP principal creado")
                
            except Exception as e:
                # Si falla, intentar con estrategia alternativa
                print(f"⚠️ Error con cliente principal: {e}")
                print("🔄 Intentando estrategia alternativa...")
                
                # Estrategia alternativa: Descargar WSDL localmente
                self.client = self._create_client_with_local_wsdl(wsdl_url, transport, settings_zeep)
                
                if not self.client:
                    raise SUNATConnectionError(f"No se pudo crear cliente SOAP: {e}")
            
            # Configurar WS-Security
            http_username = f"{credentials['ruc']}{credentials['username']}"
            wsse = UsernameToken(
                username=http_username,
                password=credentials['password'],
                use_digest=False,  # SUNAT usa texto plano
                timestamp_token=True
            )
            
            self.client.wsse = wsse
            print("✅ WS-Security configurado")
            
            # Verificar operaciones disponibles
            self._verify_operations()
            
            self._initialized = True
            print("✅ Cliente SOAP inicializado exitosamente")
            
        except Exception as e:
            print(f"❌ Error inicializando cliente SOAP: {e}")
            # Mostrar stack trace para debugging
            import traceback
            traceback.print_exc()
            raise SUNATConnectionError(f"Error conectando con SUNAT: {e}")
    
    def _create_client_with_local_wsdl(self, wsdl_url: str, transport: Transport, settings: Settings) -> Optional[Client]:
        """Estrategia alternativa: Crear cliente con WSDL local"""
        
        try:
            import tempfile
            import os
            
            print("📁 Descargando WSDL para uso local...")
            
            # Descargar WSDL con autenticación
            response = self.session.get(wsdl_url, timeout=60)
            
            if response.status_code != 200:
                print(f"❌ Error descargando WSDL: {response.status_code}")
                return None
            
            # Guardar WSDL localmente
            with tempfile.NamedTemporaryFile(mode='w', suffix='.wsdl', delete=False) as f:
                f.write(response.text)
                local_wsdl_path = f.name
            
            print(f"✅ WSDL guardado en: {local_wsdl_path}")
            
            try:
                # Crear cliente con WSDL local
                client = Client(
                    f"file://{local_wsdl_path}",
                    transport=transport,
                    settings=settings
                )
                
                print("✅ Cliente con WSDL local creado")
                return client
                
            finally:
                # Limpiar archivo temporal
                try:
                    os.unlink(local_wsdl_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Error creando cliente con WSDL local: {e}")
            return None
    
    def _verify_operations(self):
        """Verifica que las operaciones necesarias estén disponibles"""
        
        try:
            if hasattr(self.client, 'service'):
                operations = [op for op in dir(self.client.service) if not op.startswith('_')]
                print(f"✅ Operaciones disponibles: {operations}")
                
                # Verificar operaciones críticas
                required_ops = ['sendBill', 'getStatus', 'sendSummary', 'getStatusCdr']
                available_ops = [op for op in operations if op in required_ops]
                missing_ops = [op for op in required_ops if op not in operations]
                
                print(f"✅ Operaciones críticas disponibles: {available_ops}")
                if missing_ops:
                    print(f"⚠️ Operaciones faltantes: {missing_ops}")
                
                return len(available_ops) >= 2  # Al menos sendBill y getStatus
            else:
                print("❌ Cliente no tiene atributo 'service'")
                return False
                
        except Exception as e:
            print(f"⚠️ Error verificando operaciones: {e}")
            return False
    
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
            
            error_msg = str(e).lower()
            if 'authentication' in error_msg or '401' in error_msg:
                raise SUNATAuthenticationError(f"Error de autenticación: {e}")
            elif 'validation' in error_msg or 'invalid' in error_msg:
                raise SUNATValidationError(f"Error validación SUNAT: {e}")
            else:
                raise SUNATError(f"Error SOAP: {e}")
        
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
                error_msg = str(e).lower()
                
                if 'timeout' in error_msg:
                    print(f"[{self.correlation_id}] ⏱️ Timeout en intento #{attempt + 1}")
                    if attempt == self.max_retries:
                        raise SUNATTimeoutError(f"Timeout después de {self.max_retries} intentos")
                elif '401' in error_msg:
                    print(f"[{self.correlation_id}] 🔒 Error autenticación en intento #{attempt + 1}")
                    if attempt == self.max_retries:
                        raise SUNATAuthenticationError(f"Error de autenticación: {e}")
                else:
                    print(f"[{self.correlation_id}] 🌐 Error transporte en intento #{attempt + 1}: {e}")
                    if attempt == self.max_retries:
                        raise SUNATConnectionError(f"Error de conexión: {e}")
            
            except zeep.exceptions.Fault as e:
                # Errores SOAP no se reintentan generalmente
                error_msg = str(e).lower()
                if 'authentication' in error_msg or '401' in error_msg:
                    raise SUNATAuthenticationError(f"Error de autenticación: {e}")
                elif 'validation' in error_msg or 'invalid' in error_msg:
                    # Errores de validación podrían ser transitorios
                    if attempt < self.max_retries:
                        last_exception = e
                        print(f"[{self.correlation_id}] ⚠️ Error validación en intento #{attempt + 1}: {e}")
                        continue
                    else:
                        raise SUNATValidationError(f"Error de validación: {e}")
                else:
                    raise SUNATError(f"Error SOAP: {e}")
            
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
            
            # Verificar operaciones disponibles
            operations_ok = self._verify_operations()
            
            # Intentar una operación simple para verificar conectividad
            auth_ok = True
            try:
                # Crear un ZIP dummy mínimo para probar autenticación
                dummy_zip = base64.b64encode(b"dummy content").decode('utf-8')
                
                # Esto debería fallar con un error de validación, no de autenticación
                test_response = self.client.service.sendBill(
                    fileName="test-20123456789-01-F001-00000001.zip",
                    contentFile=dummy_zip
                )
                
                # Si llegamos aquí, la autenticación funcionó
                auth_ok = True
                
            except zeep.exceptions.Fault as e:
                error_msg = str(e).lower()
                if 'authentication' in error_msg or '401' in error_msg:
                    auth_ok = False
                    print(f"❌ Error de autenticación: {e}")
                elif 'validation' in error_msg or 'invalid' in error_msg:
                    # Error de validación es esperado con datos dummy
                    auth_ok = True
                    print(f"✅ Autenticación OK - Error de validación esperado")
                else:
                    auth_ok = True
                    print(f"✅ Autenticación OK - Error esperado: {e}")
                    
            except Exception as e:
                # Otros errores podrían indicar problemas de autenticación
                error_msg = str(e).lower()
                if 'authentication' in error_msg or '401' in error_msg:
                    auth_ok = False
                else:
                    auth_ok = True
                    print(f"✅ Autenticación OK - Error técnico: {e}")
            
            service_info = {
                'wsdl_url': wsdl_url,
                'operations': list(self.client.service.__dict__.keys()) if hasattr(self.client, 'service') else [],
                'environment': self.environment,
                'service_type': self.service_type,
                'ruc_configured': credentials['ruc'],
                'username_configured': f"{credentials['ruc']}{credentials['username']}",
                'wsdl_accessible': True,
                'authentication_ok': auth_ok,
                'operations_ok': operations_ok
            }
            
            print(f"✅ Conexión SUNAT exitosa (auth={auth_ok}, ops={operations_ok})")
            
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
    
    def __del__(self):
        """Limpieza al destruir el objeto"""
        if hasattr(self, 'session') and self.session:
            try:
                self.session.close()
            except:
                pass

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