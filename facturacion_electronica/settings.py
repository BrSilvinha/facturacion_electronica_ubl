"""
Django settings for facturacion_electronica project.
VERSIÓN CORREGIDA - SUNAT Configuration Fixed
"""

from pathlib import Path
import os
from decouple import config
import zipfile 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-*!-78+dy0vgc8)6&q@f%3-usv)7bm^+w)8me=&--g6gp!yt$ns')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'documentos',
    'conversion',
    'firma_digital',
    'api_rest',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'facturacion_electronica.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'facturacion_electronica.wsgi.application'

# Database
DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.postgresql',
         'NAME': config('DB_NAME', default='facturacion_electronica_db'),
         'USER': config('DB_USER', default='facturacion_user'),
         'PASSWORD': config('DB_PASSWORD', default='facturacion123'),
         'HOST': config('DB_HOST', default='localhost'),
         'PORT': config('DB_PORT', default='5432'),
     }
 }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# Internationalization
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Configuración específica para Facturación Electrónica
FACTURACION_CONFIG = {
    'CERT_PATH': config('CERT_PATH', default='certificados/'),
    'XML_OUTPUT_PATH': 'xml_output/',
    'UBL_VERSION': '2.1',
}

# =============================================================================
# CONFIGURACIÓN NIVEL 2 - FIRMA DIGITAL REAL
# =============================================================================

import logging

# Directorios de certificados
CERTIFICATES_BASE_DIR = BASE_DIR / 'certificados'
CERTIFICATES_TEST_DIR = CERTIFICATES_BASE_DIR / 'test'
CERTIFICATES_PROD_DIR = CERTIFICATES_BASE_DIR / 'production'
CERTIFICATES_BACKUP_DIR = CERTIFICATES_BASE_DIR / 'backup'

# Configuración de Firma Digital (SIN xmlsec - Solo signxml + pyOpenSSL)
DIGITAL_SIGNATURE_CONFIG = {
    # Algoritmos criptográficos
    'SIGNATURE_ALGORITHM': 'RSA-SHA256',
    'DIGEST_ALGORITHM': 'SHA256',
    'CANONICALIZATION_METHOD': 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315',
    'USE_XMLSEC': False,  # Deshabilitado en Windows sin Build Tools
    
    # Configuración de certificados
    'CERT_TEST_DIR': str(CERTIFICATES_TEST_DIR),
    'CERT_PROD_DIR': str(CERTIFICATES_PROD_DIR),
    'CERT_BACKUP_DIR': str(CERTIFICATES_BACKUP_DIR),
    'CERT_CACHE_TIMEOUT': 3600,  # 1 hora en segundos
    
    # Validación
    'VALIDATE_CERT_CHAIN': True,
    'REQUIRE_CERT_NOT_EXPIRED': True,
    'MAX_CERT_AGE_DAYS': 1095,  # 3 años máximo
    
    # Performance
    'SIGNATURE_TIMEOUT': 30,  # 30 segundos máximo por firma
    'MAX_CONCURRENT_SIGNATURES': 10,
    
    # Logging
    'LOG_SIGNATURE_OPERATIONS': True,
    'LOG_CERT_OPERATIONS': True,
}

# Configuración de logging específica para firma digital
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_signature': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'signature.log',
            'formatter': 'verbose',
        },
        'file_certificates': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'certificates.log',
            'formatter': 'verbose',
        },
        'file_sunat': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'sunat.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'signature': {
            'handlers': ['file_signature', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'certificates': {
            'handlers': ['file_certificates', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'sunat': {
            'handlers': ['file_sunat', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# Crear directorio de logs si no existe
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Configuración de seguridad para certificados
CERTIFICATE_SECURITY = {
    # Encriptación de passwords de certificados
    'PASSWORD_ENCRYPTION_KEY': config('CERT_PASSWORD_KEY', default=''),
    'PASSWORD_SALT_LENGTH': 32,
    
    # Validación de certificados
    'ALLOWED_KEY_SIZES': [2048, 3072, 4096],  # RSA key sizes permitidos
    'ALLOWED_SIGNATURE_ALGORITHMS': ['sha256WithRSAEncryption'],
    
    # Restricciones
    'MAX_CERT_FILE_SIZE': 10 * 1024 * 1024,  # 10MB máximo
    'ALLOWED_CERT_EXTENSIONS': ['.pfx', '.p12'],
}

# Actualizar FACTURACION_CONFIG existente
FACTURACION_CONFIG.update({
    'DIGITAL_SIGNATURE_ENABLED': True,
    'SIGNATURE_REQUIRED': config('SIGNATURE_REQUIRED', default=True, cast=bool),
    'XML_DSIG_VERSION': '1.0',
    'SUNAT_SIGNATURE_VALIDATION': True,
})

# Cache en memoria si no hay Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'facturacion-cache',
        'TIMEOUT': 300,
    },
    'certificates': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'certificates-cache',
        'TIMEOUT': 3600,
    }
}

# =============================================================================
# 🔧 CONFIGURACIÓN INTEGRACIÓN SUNAT - CORREGIDA Y OPTIMIZADA
# =============================================================================

# Configuración principal SUNAT
SUNAT_CONFIG = {
    # Ambiente actual
    'ENVIRONMENT': config('SUNAT_ENVIRONMENT', default='beta'),
    
    # ✅ RUC CORREGIDO - Usar el RUC real de COMERCIAL LAVAGNA
    'RUC': config('SUNAT_RUC', default='20103129061'),  # ✅ CORREGIDO
    
    # Credenciales Beta - FIJAS para ambiente de pruebas
    'BETA_USER': config('SUNAT_BETA_USER', default='MODDATOS'),
    'BETA_PASSWORD': config('SUNAT_BETA_PASSWORD', default='MODDATOS'),
    
    # Credenciales Producción
    'PROD_USER': config('SUNAT_PROD_USER', default=''),
    'PROD_PASSWORD': config('SUNAT_PROD_PASSWORD', default=''),
    
    # 🔧 URLs de servicios CORREGIDAS - Sin puerto explícito
    'WSDL_URLS': {
        'beta': {
            'factura': config('SUNAT_BETA_WSDL_FACTURA', 
                            default='https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl'),
            'guia': config('SUNAT_BETA_WSDL_GUIA',
                         default='https://e-beta.sunat.gob.pe/ol-ti-itemision-guia-gem-beta/billService?wsdl'),
            'retencion': config('SUNAT_BETA_WSDL_RETENCION',
                              default='https://e-beta.sunat.gob.pe/ol-ti-itemision-otroscpe-gem-beta/billService?wsdl'),
        },
        'production': {
            'factura': config('SUNAT_PROD_WSDL_FACTURA',
                            default='https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService?wsdl'),
            'guia': config('SUNAT_PROD_WSDL_GUIA',
                         default='https://e-guiaremision.sunat.gob.pe/ol-ti-itemision-guiagem/billService?wsdl'),
            'retencion': config('SUNAT_PROD_WSDL_RETENCION',
                              default='https://e-factura.sunat.gob.pe/ol-ti-itemision-otroscpe-gem/billService?wsdl'),
        }
    },
    
    # 🔧 URLs de servicio SIN WSDL para requests directos
    'SERVICE_URLS': {
        'beta': {
            'factura': 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService',
            'guia': 'https://e-beta.sunat.gob.pe/ol-ti-itemision-guia-gem-beta/billService',
            'retencion': 'https://e-beta.sunat.gob.pe/ol-ti-itemision-otroscpe-gem-beta/billService',
        },
        'production': {
            'factura': 'https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService',
            'guia': 'https://e-guiaremision.sunat.gob.pe/ol-ti-itemision-guiagem/billService',
            'retencion': 'https://e-factura.sunat.gob.pe/ol-ti-itemision-otroscpe-gem/billService',
        }
    },
    
    # Configuración de conexión OPTIMIZADA
    'TIMEOUT': config('SUNAT_TIMEOUT', default=120, cast=int),
    'MAX_RETRIES': config('SUNAT_MAX_RETRIES', default=3, cast=int),
    'ENABLE_LOGGING': config('SUNAT_ENABLE_LOGGING', default=True, cast=bool),
    
    # 🔧 CONFIGURACIÓN WSDL MEJORADA
    'USE_LOCAL_WSDL': True,  # Usar WSDL local para evitar problemas de auth
    'LOCAL_WSDL_PATH': BASE_DIR / 'sunat_integration' / 'sunat_complete.wsdl',
    'WSDL_CACHE_TIMEOUT': 3600,  # Cache WSDL por 1 hora
    
    # Configuración de archivos
    'ZIP_COMPRESSION': zipfile.ZIP_DEFLATED,
    'XML_ENCODING': 'UTF-8',
    'TEMP_DIR': BASE_DIR / 'temp' / 'sunat',
    
    # Configuración de retry OPTIMIZADA
    'RETRY_DELAY': 2,  # segundos
    'EXPONENTIAL_BACKOFF': True,
    'RETRY_ON_WSDL_ERROR': True,
    
    # 🔧 CONFIGURACIÓN DE FALLBACK
    'ENABLE_FALLBACK_TO_LOCAL_WSDL': True,
    'ENABLE_SIMULATION_ON_ERROR': True,  # Para desarrollo
}

# Crear directorio temporal si no existe
SUNAT_CONFIG['TEMP_DIR'].mkdir(parents=True, exist_ok=True)

# Import necesario para zipfile
import zipfile

# =============================================================================
# CONFIGURACIÓN CORS - DESARROLLO
# =============================================================================

# Permitir todos los orígenes para desarrollo
CORS_ALLOW_ALL_ORIGINS = True

# Permitir credenciales (cookies, auth headers)
CORS_ALLOW_CREDENTIALS = True

# Métodos HTTP permitidos
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS', 
    'PATCH',
    'POST',
    'PUT',
]

# Headers permitidos
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Headers expuestos
CORS_EXPOSE_HEADERS = [
    'content-type',
    'x-csrftoken',
]

# Aplicar CORS solo a endpoints de API
CORS_URLS_REGEX = r'^/api/.*$'

# =============================================================================
# 🔧 CONFIGURACIÓN DEBUG ADICIONAL - SOLO PARA DESARROLLO
# =============================================================================

if DEBUG:
    # Logging más detallado en desarrollo
    LOGGING['handlers']['console']['level'] = 'DEBUG'
    LOGGING['loggers']['sunat']['level'] = 'DEBUG'
    
    # Configuración adicional para debugging SUNAT
    SUNAT_CONFIG.update({
        'DEBUG_MODE': True,
        'LOG_SOAP_REQUESTS': True,
        'LOG_SOAP_RESPONSES': True,
        'SAVE_REQUEST_RESPONSE_TO_FILE': True,
    })

print("🔧 Settings cargado con configuración SUNAT corregida")
print(f"✅ RUC configurado: {SUNAT_CONFIG['RUC']}")
print(f"✅ Ambiente: {SUNAT_CONFIG['ENVIRONMENT']}")
print(f"✅ Usuario completo será: {SUNAT_CONFIG['RUC']}{SUNAT_CONFIG['BETA_USER']}")