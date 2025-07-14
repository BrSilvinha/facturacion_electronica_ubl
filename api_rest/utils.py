# api_rest/utils.py - Utilidades para limpiar XML

import re
from typing import str

def clean_xml_for_sunat(xml_content: str) -> str:
    """
    Limpia XML para SUNAT eliminando caracteres problemáticos
    Soluciona error: Content is not allowed in prolog
    """
    
    if not xml_content:
        return xml_content
    
    # 1. Remover BOM UTF-8 si existe
    if xml_content.startswith('\ufeff'):
        xml_content = xml_content[1:]
    
    # 2. Remover espacios y saltos de línea al inicio
    xml_content = xml_content.lstrip()
    
    # 3. Verificar que empiece con <?xml
    if not xml_content.startswith('<?xml'):
        # Buscar la declaración XML y remover todo lo anterior
        xml_start = xml_content.find('<?xml')
        if xml_start > 0:
            xml_content = xml_content[xml_start:]
    
    # 4. Remover caracteres de control (excepto tab, LF, CR)
    xml_content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_content)
    
    # 5. Asegurar que la declaración XML use comillas dobles
    xml_content = re.sub(
        r"<\?xml\s+version\s*=\s*['\"]([^'\"]*)['\"](\s+encoding\s*=\s*['\"]([^'\"]*)['\"])?[^>]*\?>",
        r'<?xml version="\1" encoding="\3"?>',
        xml_content
    )
    
    # 6. Normalizar saltos de línea
    xml_content = xml_content.replace('\r\n', '\n').replace('\r', '\n')
    
    return xml_content

def validate_xml_structure(xml_content: str) -> tuple:
    """
    Valida la estructura básica del XML
    Returns: (is_valid, error_message)
    """
    
    try:
        # Limpiar primero
        clean_xml = clean_xml_for_sunat(xml_content)
        
        # Verificar que empiece con declaración XML
        if not clean_xml.strip().startswith('<?xml'):
            return False, "XML debe empezar con declaración <?xml"
        
        # Verificar que contenga Invoice
        if '<Invoice' not in clean_xml:
            return False, "XML debe contener elemento Invoice"
        
        # Verificar que contenga RUC en signature
        if '<cbc:ID>20103129061</cbc:ID>' not in clean_xml:
            return False, "XML debe contener RUC en cac:Signature"
        
        # Verificar estructura básica
        required_elements = [
            '<cbc:UBLVersionID>',
            '<cbc:CustomizationID>',
            '<cac:AccountingSupplierParty>',
            '<cac:AccountingCustomerParty>',
            '<cac:InvoiceLine>'
        ]
        
        for element in required_elements:
            if element not in clean_xml:
                return False, f"Elemento requerido faltante: {element}"
        
        return True, "XML válido"
        
    except Exception as e:
        return False, f"Error validando XML: {str(e)}"

def format_xml_for_display(xml_content: str) -> str:
    """
    Formatea XML para mostrar en respuestas de API
    """
    try:
        from xml.dom import minidom
        
        # Limpiar primero
        clean_xml = clean_xml_for_sunat(xml_content)
        
        # Parsear y formatear
        dom = minidom.parseString(clean_xml)
        pretty_xml = dom.toprettyxml(indent="  ", encoding=None)
        
        # Remover líneas vacías extra
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        return '\n'.join(lines)
        
    except Exception:
        # Si falla el formateo, retornar XML limpio
        return clean_xml_for_sunat(xml_content)