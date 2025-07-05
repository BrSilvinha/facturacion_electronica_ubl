"""
Utilidades comunes para integración SUNAT
Ubicación: sunat_integration/utils.py
VERSIÓN CORREGIDA - Credenciales SUNAT Beta arregladas
"""

import re
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from django.conf import settings

def get_sunat_filename(documento, extension='zip') -> str:
    """
    Genera nombre de archivo según especificaciones SUNAT
    
    Args:
        documento: Instancia de DocumentoElectronico
        extension: Extensión del archivo (zip, xml)
    
    Returns:
        Nombre de archivo válido para SUNAT
    """
    
    ruc = documento.empresa.ruc
    tipo = documento.tipo_documento.codigo
    serie = documento.serie
    numero = f"{documento.numero:08d}"
    
    return f"{ruc}-{tipo}-{serie}-{numero}.{extension}"

def get_sunat_credentials(environment: str = None) -> Dict[str, str]:
    """
    Obtiene credenciales SUNAT según ambiente - CORREGIDO
    
    Args:
        environment: 'beta' o 'production'
    
    Returns:
        Dict con ruc, username y password
    """
    
    config = settings.SUNAT_CONFIG
    env = environment or config['ENVIRONMENT']
    ruc = config['RUC']
    
    if env == 'beta':
        # Para SUNAT Beta: usuario y password fijos
        username = config['BETA_USER']  # 'MODDATOS'
        password = config['BETA_PASSWORD']  # 'MODDATOS'
    else:
        # Para Producción: usuario real de la empresa
        username = config['PROD_USER']
        password = config['PROD_PASSWORD']
    
    # ⚠️ IMPORTANTE: No agregar RUC aquí, se hace en soap_client
    return {
        'ruc': ruc,
        'username': username,  # Solo el usuario base
        'password': password
    }

def get_wsdl_url(service_type: str = 'factura', environment: str = None) -> str:
    """
    Obtiene URL del WSDL según tipo de servicio y ambiente
    
    Args:
        service_type: 'factura', 'guia', 'retencion'
        environment: 'beta' o 'production'
    
    Returns:
        URL del WSDL
    """
    
    config = settings.SUNAT_CONFIG
    env = environment or config['ENVIRONMENT']
    
    return config['WSDL_URLS'][env][service_type]

def validate_ruc_format(ruc: str) -> bool:
    """
    Valida formato de RUC peruano
    
    Args:
        ruc: RUC a validar
    
    Returns:
        True si es válido
    """
    
    if not ruc or len(ruc) != 11:
        return False
    
    return bool(re.match(r'^\d{11}$', ruc))

def generate_correlation_id() -> str:
    """
    Genera ID de correlación único para trazabilidad
    
    Returns:
        ID único
    """
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    hash_suffix = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:6]
    
    return f"SUNAT-{timestamp}-{hash_suffix}"

def sanitize_xml_content(xml_content: str) -> str:
    """
    Limpia contenido XML para envío a SUNAT
    
    Args:
        xml_content: Contenido XML
    
    Returns:
        XML limpio
    """
    
    # Remover BOM si existe
    if xml_content.startswith('\ufeff'):
        xml_content = xml_content[1:]
    
    # Asegurar encoding UTF-8
    if '<?xml' in xml_content and 'encoding=' not in xml_content:
        xml_content = xml_content.replace(
            '<?xml version="1.0"?>',
            '<?xml version="1.0" encoding="UTF-8"?>'
        )
    
    return xml_content.strip()

def parse_sunat_error_response(response_text: str) -> Dict[str, Any]:
    """
    Parsea respuesta de error de SUNAT
    
    Args:
        response_text: Texto de respuesta
    
    Returns:
        Dict con información del error
    """
    
    error_info = {
        'error_code': None,
        'error_message': response_text,
        'is_business_error': False,
        'is_technical_error': False
    }
    
    # Buscar códigos de error conocidos
    if 'faultcode' in response_text:
        error_info['is_technical_error'] = True
        
        # Extraer código de error
        import re
        fault_code_match = re.search(r'<faultcode[^>]*>([^<]+)</faultcode>', response_text)
        if fault_code_match:
            error_info['error_code'] = fault_code_match.group(1)
        
        # Extraer mensaje de error
        fault_string_match = re.search(r'<faultstring[^>]*>([^<]+)</faultstring>', response_text)
        if fault_string_match:
            error_info['error_message'] = fault_string_match.group(1)
    
    elif any(code in response_text for code in ['2000', '3000', '4000']):
        error_info['is_business_error'] = True
    
    return error_info

def format_sunat_datetime(dt: datetime) -> str:
    """
    Formatea datetime para SUNAT (YYYY-MM-DD)
    
    Args:
        dt: Datetime a formatear
    
    Returns:
        Fecha formateada
    """
    
    return dt.strftime('%Y-%m-%d')

def is_production_environment() -> bool:
    """
    Verifica si estamos en ambiente de producción
    
    Returns:
        True si es producción
    """
    
    return settings.SUNAT_CONFIG['ENVIRONMENT'] == 'production'