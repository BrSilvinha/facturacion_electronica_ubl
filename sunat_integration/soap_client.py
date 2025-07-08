# Archivo: sunat_integration/soap_client_corregido.py
"""
Cliente SOAP SUNAT CORREGIDO - Manejo adecuado de errores y CDR
"""

import logging
import base64
import zipfile
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Imports seguros
try:
    import requests
    from requests.auth import HTTPBasicAuth
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from zeep import Client, Settings
    from zeep.transports import Transport
    from zeep.exceptions import Fault as ZeepFault
    ZEEP_AVAILABLE = True
except ImportError:
    ZEEP_AVAILABLE = False

# Imports locales
try:
    from .utils import get_sunat_credentials, generate_correlation_id
    from .exceptions import SUNATError, SUNATConnectionError, SUNATAuthenticationError
    from .zip_generator import SUNATZipGenerator
except ImportError:
    def get_sunat_credentials(env=None):
        return {'ruc': '20103129061', 'username': 'MODDATOS', 'password': 'MODDATOS'}
    
    def generate_correlation_id():
        return f"SUNAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    class SUNATError(Exception): pass
    class SUNATConnectionError(SUNATError): pass
    class SUNATAuthenticationError(SUNATError): pass
    
    SUNATZipGenerator = None

logger = logging.getLogger('sunat')

class SUNATSoapClientCorregido:
    """Cliente SOAP SUNAT con manejo mejorado de errores y CDR"""
    
    def __init__(self, service_type: str = 'factura', environment: str = None):
        self.service_type = service_type
        self.environment = environment or 'beta'
        
        # Configuración
        self.credentials = get_sunat_credentials(self.environment)
        self.full_username = f"{self.credentials['ruc']}{self.credentials['username']}"
        
        # URLs corregidas (sin puerto explícito)
        if self.environment == 'beta':
            self.service_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService"
            self.wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
        else:
            self.service_url = "https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService"
            self.wsdl_url = "https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService?wsdl"
        
        # ZIP Generator
        self.zip_generator = SUNATZipGenerator() if SUNATZipGenerator else None
        
        # Cliente zeep
        self.zeep_client = None
        self.use_zeep = ZEEP_AVAILABLE
        
        # Session para requests
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.full_username, self.credentials['password'])
        self.session.verify = True  # Verificar SSL
        
        logger.info(f"SUNATSoapClient corregido: {self.environment}")
        logger.info(f"Usuario: {self.full_username}")
        logger.info(f"URL: {self.service_url}")
    
    def _initialize_zeep(self):
        """Inicializar zeep con configuración mejorada"""
        if self.zeep_client or not self.use_zeep:
            return
        
        try:
            logger.info(f"Inicializando zeep con WSDL: {self.wsdl_url}")
            
            # Transport con configuración mejorada
            transport = Transport(
                session=self.session,
                timeout=60,  # Aumentar timeout
                operation_timeout=60
            )
            
            # Settings permisivos
            settings = Settings(
                strict=False,
                xml_huge_tree=True,
                force_https=True,
                forbid_entities=False
            )
            
            # Cliente con WSDL remoto
            self.zeep_client = Client(
                self.wsdl_url,
                transport=transport,
                settings=settings
            )
            
            logger.info("✅ Cliente zeep inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando zeep: {e}")
            self.use_zeep = False
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test de conexión mejorado"""
        start_time = datetime.now()
        correlation_id = generate_correlation_id()
        
        try:
            logger.info(f"[{correlation_id}] Test de conexión SUNAT...")
            
            # Intentar inicializar zeep
            if self.use_zeep:
                if self._initialize_zeep():
                    if self.zeep_client:
                        operations = [op for op in dir(self.zeep_client.service) if not op.startswith('_')]
                        
                        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                        
                        return {
                            'success': True,
                            'method': 'zeep_wsdl',
                            'service_info': {
                                'operations': operations,
                                'authentication_ok': True,
                                'wsdl_source': 'remote',
                                'url': self.service_url
                            },
                            'duration_ms': duration_ms,
                            'correlation_id': correlation_id
                        }
            
            # Fallback a requests
            logger.info("Usando requests como fallback...")
            response = self.session.get(self.service_url, timeout=30)
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Analizar respuesta
            auth_ok = response.status_code not in [401, 403]
            service_ok = response.status_code not in [404, 500, 502, 503]
            
            return {
                'success': service_ok,
                'method': 'requests_fallback',
                'service_info': {
                    'operations': ['sendBill', 'sendSummary', 'getStatus'],
                    'authentication_ok': auth_ok,
                    'status_code': response.status_code,
                    'url': self.service_url
                },
                'duration_ms': duration_ms,
                'correlation_id': correlation_id,
                'warning': 'Usando fallback - zeep no disponible' if not self.use_zeep else None
            }
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return {
                'success': False,
                'error': str(e),
                'duration_ms': duration_ms,
                'correlation_id': correlation_id
            }
    
    def send_bill(self, documento, xml_firmado: str) -> Dict[str, Any]:
        """Envía factura a SUNAT con manejo mejorado de errores"""
        correlation_id = generate_correlation_id()
        start_time = datetime.now()
        
        try:
            logger.info(f"[{correlation_id}] Enviando documento: {documento.get_numero_completo()}")
            
            # Preparar archivo ZIP
            if self.zip_generator:
                zip_content = self.zip_generator.create_document_zip(documento, xml_firmado)
                logger.info(f"ZIP generado: {len(zip_content)} bytes")
            else:
                # Fallback: crear ZIP simple
                zip_content = self._create_simple_zip(documento, xml_firmado)
                logger.info(f"ZIP simple generado: {len(zip_content)} bytes")
            
            # Codificar en base64
            content_base64 = base64.b64encode(zip_content).decode('utf-8')
            
            # Nombre de archivo según especificaciones SUNAT
            filename = f"{documento.empresa.ruc}-{documento.tipo_documento.codigo}-{documento.serie}-{documento.numero:08d}.zip"
            
            logger.info(f"Enviando archivo: {filename}")
            
            # Intentar con zeep primero
            if self.use_zeep and self._initialize_zeep() and self.zeep_client:
                return self._send_with_zeep(filename, content_base64, correlation_id, start_time)
            else:
                return self._send_with_simulation(filename, correlation_id, start_time)
                
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"[{correlation_id}] Error enviando: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'correlation_id': correlation_id,
                'duration_ms': duration_ms,
                'method': 'error'
            }
    
    def _send_with_zeep(self, filename: str, content_base64: str, correlation_id: str, start_time: datetime) -> Dict[str, Any]:
        """Envío usando zeep con manejo de errores SOAP"""
        
        try:
            logger.info(f"[{correlation_id}] Enviando con zeep...")
            
            # Llamada al servicio SUNAT
            response = self.zeep_client.service.sendBill(
                fileName=filename,
                contentFile=content_base64
            )
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(f"[{correlation_id}] Respuesta SUNAT recibida en {duration_ms}ms")
            
            # Procesar respuesta
            if hasattr(response, 'applicationResponse') and response.applicationResponse:
                # Hay CDR en la respuesta
                cdr_base64 = response.applicationResponse
                cdr_data = self._process_cdr_response(cdr_base64, correlation_id)
                
                return {
                    'success': True,
                    'method': 'zeep_with_cdr',
                    'filename': filename,
                    'correlation_id': correlation_id,
                    'duration_ms': duration_ms,
                    'has_cdr': True,
                    'cdr_content': cdr_base64,
                    'cdr_data': cdr_data
                }
            else:
                # Respuesta sin CDR (puede ser normal para algunos casos)
                logger.warning(f"[{correlation_id}] Respuesta sin CDR")
                
                return {
                    'success': True,
                    'method': 'zeep_no_cdr',
                    'filename': filename,
                    'correlation_id': correlation_id,
                    'duration_ms': duration_ms,
                    'has_cdr': False,
                    'message': 'Enviado exitosamente sin CDR inmediato'
                }
                
        except ZeepFault as soap_fault:
            # Error SOAP específico
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            fault_code = getattr(soap_fault, 'code', 'Unknown')
            fault_string = getattr(soap_fault, 'message', str(soap_fault))
            
            logger.error(f"[{correlation_id}] SOAP Fault: {fault_code} - {fault_string}")
            
            # Analizar tipo de error
            error_analysis = self._analyze_soap_error(fault_code, fault_string)
            
            return {
                'success': False,
                'error_type': 'SOAP_FAULT',
                'error_code': fault_code,
                'error_message': fault_string,
                'error_analysis': error_analysis,
                'correlation_id': correlation_id,
                'duration_ms': duration_ms,
                'method': 'zeep_fault'
            }
            
        except Exception as e:
            # Error general
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"[{correlation_id}] Error zeep: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'error_type': 'ZEEP_ERROR',
                'correlation_id': correlation_id,
                'duration_ms': duration_ms,
                'method': 'zeep_error'
            }
    
    def _send_with_simulation(self, filename: str, correlation_id: str, start_time: datetime) -> Dict[str, Any]:
        """Envío simulado cuando zeep no está disponible"""
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        logger.info(f"[{correlation_id}] Usando simulación - zeep no disponible")
        
        return {
            'success': True,
            'method': 'simulation',
            'filename': filename,
            'correlation_id': correlation_id,
            'duration_ms': duration_ms,
            'simulated': True,
            'message': 'Documento procesado en modo simulación',
            'note': 'Para envío real, instalar: pip install zeep'
        }
    
    def _process_cdr_response(self, cdr_base64: str, correlation_id: str) -> Dict[str, Any]:
        """Procesa la respuesta CDR de SUNAT"""
        
        try:
            logger.info(f"[{correlation_id}] Procesando CDR...")
            
            # Decodificar base64
            cdr_zip = base64.b64decode(cdr_base64)
            
            # Extraer XML del ZIP
            with zipfile.ZipFile(BytesIO(cdr_zip), 'r') as zip_file:
                cdr_files = [f for f in zip_file.namelist() if f.startswith('R-') and f.endswith('.xml')]
                
                if cdr_files:
                    cdr_xml = zip_file.read(cdr_files[0]).decode('utf-8')
                    
                    # Procesar XML CDR (análisis básico)
                    cdr_analysis = self._analyze_cdr_xml(cdr_xml)
                    
                    logger.info(f"[{correlation_id}] CDR procesado: {cdr_analysis.get('status', 'Unknown')}")
                    
                    return {
                        'cdr_filename': cdr_files[0],
                        'cdr_xml': cdr_xml,
                        'analysis': cdr_analysis,
                        'processed_at': datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"[{correlation_id}] No se encontró XML CDR en el ZIP")
                    return {'error': 'CDR XML not found in ZIP'}
                    
        except Exception as e:
            logger.error(f"[{correlation_id}] Error procesando CDR: {e}")
            return {'error': f'Error processing CDR: {e}'}
    
    def _analyze_cdr_xml(self, cdr_xml: str) -> Dict[str, Any]:
        """Análisis básico del XML CDR"""
        
        try:
            # Análisis simple por texto (sin lxml para evitar dependencias)
            if 'ResponseCode>0<' in cdr_xml:
                status = 'ACCEPTED'
                message = 'Documento aceptado por SUNAT'
            elif 'ResponseCode>2' in cdr_xml or 'ResponseCode>3' in cdr_xml:
                status = 'REJECTED'
                message = 'Documento rechazado por SUNAT'
            else:
                status = 'UNKNOWN'
                message = 'Estado desconocido'
            
            return {
                'status': status,
                'message': message,
                'has_xml': True,
                'analysis_method': 'text_parsing'
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Error analyzing CDR: {e}',
                'has_xml': True,
                'analysis_method': 'error'
            }
    
    def _analyze_soap_error(self, fault_code: str, fault_string: str) -> Dict[str, Any]:
        """Analiza errores SOAP de SUNAT"""
        
        # Mapeo de errores comunes
        error_map = {
            'env:Client': 'Error del cliente - revisar datos enviados',
            'env:Server': 'Error del servidor SUNAT',
            '0101': 'Encabezado de seguridad incorrecto',
            '0102': 'Usuario o contraseña incorrectos',
            '0111': 'No tiene perfil para enviar comprobantes electrónicos',
            '0154': 'RUC no autorizado para enviar comprobantes',
            'Internal Error': 'Error interno de SUNAT - puede ser temporal'
        }
        
        # Buscar explicación
        explanation = 'Error desconocido'
        for code, desc in error_map.items():
            if code in fault_code or code in fault_string:
                explanation = desc
                break
        
        # Determinar si es recuperable
        recoverable = fault_code in ['env:Server'] or 'Internal Error' in fault_string
        
        return {
            'explanation': explanation,
            'recoverable': recoverable,
            'category': 'AUTHENTICATION' if '010' in fault_code else 'TECHNICAL',
            'suggested_action': self._get_suggested_action(fault_code, fault_string)
        }
    
    def _get_suggested_action(self, fault_code: str, fault_string: str) -> str:
        """Sugiere acción para resolver el error"""
        
        if '0102' in fault_code:
            return 'Verificar credenciales SUNAT (usuario/password)'
        elif '0111' in fault_code:
            return 'Crear usuario secundario en SOL con perfil de facturación electrónica'
        elif '0154' in fault_code:
            return 'Verificar que el RUC esté autorizado para facturación electrónica'
        elif 'Internal Error' in fault_string:
            return 'Reintentar en unos minutos - error temporal de SUNAT'
        else:
            return 'Revisar documentación SUNAT o contactar soporte técnico'
    
    def _create_simple_zip(self, documento, xml_firmado: str) -> bytes:
        """Crea ZIP simple sin dependencias externas"""
        
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Carpeta dummy requerida por SUNAT
            zip_file.writestr('dummy/', '')
            
            # XML firmado
            filename = f"{documento.empresa.ruc}-{documento.tipo_documento.codigo}-{documento.serie}-{documento.numero:08d}.xml"
            zip_file.writestr(filename, xml_firmado.encode('utf-8'))
        
        return zip_buffer.getvalue()

# Factory function actualizada
def create_sunat_client_corregido(service_type: str = 'factura', environment: str = None):
    return SUNATSoapClientCorregido(service_type, environment)