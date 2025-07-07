import os
import sys
import django
from django.conf import settings
import requests
import tempfile
import zipfile
from io import BytesIO
from lxml import etree
from zeep import Client, Settings
from zeep.transports import Transport
from zeep.wsse import UsernameToken
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import warnings
warnings.filterwarnings('ignore')

# Configuración Django
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

class SUNATClientFixed:
    """Cliente SUNAT corregido con mejor manejo de autenticación"""
    
    # URLs oficiales SUNAT
    SUNAT_URLS = {
        'produccion': {
            'factura': 'https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService',
            'guia': 'https://e-guiaremision.sunat.gob.pe/ol-ti-itemision-guia-gem/billService',
            'retencion': 'https://e-factura.sunat.gob.pe/ol-ti-itemision-otroscpe-gem/billService'
        },
        'beta': {
            'factura': 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService',
            'guia': 'https://e-beta.sunat.gob.pe/ol-ti-itemision-guia-gem-beta/billService',
            'retencion': 'https://e-beta.sunat.gob.pe/ol-ti-itemision-otroscpe-gem-beta/billService'
        }
    }
    
    def __init__(self, ruc, username, password, environment='beta', document_type='factura'):
        self.ruc = ruc
        self.username = username
        self.password = password
        self.environment = environment
        self.document_type = document_type
        
        # Construir usuario completo
        self.full_username = f"{ruc}{username}"
        
        # URL del servicio
        self.service_url = self.SUNAT_URLS[environment][document_type]
        self.wsdl_url = f"{self.service_url}?wsdl"
        
        # Cliente SOAP
        self.client = None
        self.session = None
        
        print(f"🔧 SUNATClientFixed inicializado:")
        print(f"   RUC: {ruc}")
        print(f"   Usuario: {username}")
        print(f"   Usuario completo: {self.full_username}")
        print(f"   Ambiente: {environment}")
        print(f"   Tipo: {document_type}")
        print(f"   WSDL: {self.wsdl_url}")
    
    def create_session(self):
        """Crear sesión HTTP con autenticación y configuración robusta"""
        session = requests.Session()
        
        # Configurar autenticación
        session.auth = HTTPBasicAuth(self.full_username, self.password)
        
        # Headers requeridos
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/xml,application/xml,application/soap+xml,*/*',
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': '""',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Configurar reintentos
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Verificar SSL pero permitir algunos problemas
        session.verify = True
        
        self.session = session
        return session
    
    def test_credentials(self):
        """Probar credenciales con diferentes métodos"""
        print("\n🔐 Probando credenciales...")
        
        if not self.session:
            self.create_session()
        
        # Método 1: Acceso directo al WSDL
        print("📋 Método 1: Acceso directo al WSDL")
        try:
            response = self.session.get(self.wsdl_url, timeout=30)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ WSDL accesible")
                return True
            elif response.status_code == 401:
                print("   ❌ Credenciales incorrectas")
            else:
                print(f"   ⚠️ Error: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Método 2: Probar con diferentes formatos de usuario
        print("\n📋 Método 2: Probando formatos de usuario")
        user_formats = [
            f"{self.ruc}{self.username}",
            f"{self.ruc}{self.username}",
            self.username,
            f"{self.ruc}_{self.username}",
            f"{self.ruc}-{self.username}"
        ]
        
        for user_format in user_formats:
            print(f"   Probando: {user_format}")
            try:
                temp_session = requests.Session()
                temp_session.auth = HTTPBasicAuth(user_format, self.password)
                temp_session.headers.update(self.session.headers)
                
                response = temp_session.get(self.wsdl_url, timeout=15)
                if response.status_code == 200:
                    print(f"   ✅ Funciona con: {user_format}")
                    self.full_username = user_format
                    self.session.auth = HTTPBasicAuth(user_format, self.password)
                    return True
                else:
                    print(f"   ❌ {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return False
    
    def create_soap_client(self):
        """Crear cliente SOAP con configuración robusta"""
        print("\n🔧 Creando cliente SOAP...")
        
        if not self.session:
            self.create_session()
        
        try:
            # Configuración de transporte
            transport = Transport(
                session=self.session,
                timeout=120,
                operation_timeout=120,
                cache=False
            )
            
            # Configuración de Zeep
            settings = Settings(
                strict=False,
                xml_huge_tree=True,
                forbid_entities=False,
                forbid_external=False,
                forbid_dtd=False,
                raw_response=False,
                xsd_ignore_sequence_order=True
            )
            
            # Crear cliente
            print(f"   WSDL: {self.wsdl_url}")
            self.client = Client(
                wsdl=self.wsdl_url,
                transport=transport,
                settings=settings
            )
            
            # Configurar WS-Security
            self.client.wsse = UsernameToken(
                self.full_username,
                self.password
            )
            
            print("   ✅ Cliente SOAP creado exitosamente")
            return True
            
        except Exception as e:
            print(f"   ❌ Error creando cliente: {e}")
            
            # Intentar con WSDL local
            return self.create_soap_client_local()
    
    def create_soap_client_local(self):
        """Crear cliente SOAP con WSDL local"""
        print("\n📁 Creando cliente SOAP con WSDL local...")
        
        try:
            # Descargar WSDL
            print("   Descargando WSDL...")
            if not self.session:
                self.create_session()
            
            response = self.session.get(self.wsdl_url, timeout=30)
            if response.status_code != 200:
                print(f"   ❌ Error descargando WSDL: {response.status_code}")
                return False
            
            # Guardar temporalmente
            with tempfile.NamedTemporaryFile(mode='w', suffix='.wsdl', delete=False) as f:
                f.write(response.text)
                wsdl_path = f.name
            
            print(f"   ✅ WSDL guardado en: {wsdl_path}")
            
            # Crear cliente con archivo local
            transport = Transport(
                session=self.session,
                timeout=120,
                operation_timeout=120
            )
            
            settings = Settings(
                strict=False,
                xml_huge_tree=True,
                forbid_entities=False,
                forbid_external=False,
                forbid_dtd=False
            )
            
            # Usar file:// URL correctamente
            file_url = f"file://{wsdl_path.replace(os.sep, '/')}"
            print(f"   Usando: {file_url}")
            
            self.client = Client(
                wsdl=file_url,
                transport=transport,
                settings=settings
            )
            
            # Configurar WS-Security
            self.client.wsse = UsernameToken(
                self.full_username,
                self.password
            )
            
            print("   ✅ Cliente SOAP con WSDL local creado")
            return True
            
        except Exception as e:
            print(f"   ❌ Error con WSDL local: {e}")
            return False
    
    def test_connection(self):
        """Probar conexión completa"""
        print("\n🧪 Probando conexión completa...")
        
        # Paso 1: Probar credenciales
        if not self.test_credentials():
            print("❌ Credenciales no válidas")
            return False
        
        # Paso 2: Crear cliente SOAP
        if not self.create_soap_client():
            print("❌ No se pudo crear cliente SOAP")
            return False
        
        # Paso 3: Verificar operaciones
        try:
            operations = list(self.client.service._operations.keys())
            print(f"   ✅ Operaciones disponibles: {operations}")
            
            # Verificar operaciones críticas
            required_ops = ['sendBill', 'getStatus']
            available_ops = [op for op in required_ops if op in operations]
            
            if available_ops:
                print(f"   ✅ Operaciones críticas disponibles: {available_ops}")
                return True
            else:
                print(f"   ❌ Operaciones críticas no disponibles")
                return False
                
        except Exception as e:
            print(f"   ❌ Error verificando operaciones: {e}")
            return False
    
    def send_bill(self, filename, xml_content):
        """Enviar factura a SUNAT"""
        print(f"\n📤 Enviando factura: {filename}")
        
        if not self.client:
            print("❌ Cliente no inicializado")
            return None
        
        try:
            # Crear ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(filename, xml_content)
            
            zip_data = zip_buffer.getvalue()
            
            # Enviar
            response = self.client.service.sendBill(
                fileName=filename.replace('.xml', '.zip'),
                contentFile=zip_data
            )
            
            print("✅ Factura enviada exitosamente")
            return response
            
        except Exception as e:
            print(f"❌ Error enviando factura: {e}")
            return None
    
    def get_status(self, ruc, document_type, series, number):
        """Consultar estado de documento"""
        print(f"\n📋 Consultando estado: {ruc}-{document_type}-{series}-{number}")
        
        if not self.client:
            print("❌ Cliente no inicializado")
            return None
        
        try:
            response = self.client.service.getStatus(
                rucComprobante=ruc,
                tipoComprobante=document_type,
                serieComprobante=series,
                numeroComprobante=number
            )
            
            print("✅ Estado consultado exitosamente")
            return response
            
        except Exception as e:
            print(f"❌ Error consultando estado: {e}")
            return None

def test_sunat_client():
    """Función de prueba principal"""
    print("🚀 PRUEBA SUNAT CLIENT CORREGIDO")
    print("=" * 60)
    
    # Configuración desde settings
    try:
        RUC = getattr(settings, 'SUNAT_RUC', '20123456789')
        USERNAME = getattr(settings, 'SUNAT_USERNAME', 'MODDATOS')
        PASSWORD = getattr(settings, 'SUNAT_PASSWORD', 'MODDATOS')
        ENVIRONMENT = getattr(settings, 'SUNAT_ENVIRONMENT', 'beta')
        
        print(f"✅ RUC: {RUC}")
        print(f"✅ Usuario: {USERNAME}")
        print(f"✅ Password: {'*' * len(PASSWORD)}")
        print(f"✅ Ambiente: {ENVIRONMENT}")
        
    except Exception as e:
        print(f"❌ Error leyendo configuración: {e}")
        print("⚠️ Usando valores por defecto")
        RUC = '20123456789'
        USERNAME = 'MODDATOS'
        PASSWORD = 'MODDATOS'
        ENVIRONMENT = 'beta'
    
    print("\n" + "=" * 60)
    print("INICIANDO PRUEBAS")
    print("=" * 60)
    
    # Crear cliente
    client = SUNATClientFixed(
        ruc=RUC,
        username=USERNAME,
        password=PASSWORD,
        environment=ENVIRONMENT,
        document_type='factura'
    )
    
    # Probar conexión
    success = client.test_connection()
    
    print("\n" + "=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)
    
    if success:
        print("✅ CONEXIÓN EXITOSA")
        print("✅ Cliente SUNAT funcionando correctamente")
        return client
    else:
        print("❌ CONEXIÓN FALLIDA")
        print("❌ Revisar credenciales y configuración")
        return None

if __name__ == "__main__":
    test_sunat_client()