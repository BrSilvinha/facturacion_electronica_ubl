# sunat_integration/cdr_parser.py
"""
Parser y Generador de CDR (Constancia de Recepción) SUNAT
CREAR ESTE ARCHIVO EN: sunat_integration/cdr_parser.py
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Importación segura de lxml
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    print("⚠️ lxml no está instalado. Instalar con: pip install lxml")

from django.utils import timezone

logger = logging.getLogger('sunat')

class CDRParser:
    """Parser para CDR de SUNAT - ApplicationResponse XML"""
    
    def __init__(self):
        self.namespaces = {
            'ar': 'urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
            'ds': 'http://www.w3.org/2000/09/xmldsig#'
        }
        
        if not LXML_AVAILABLE:
            logger.warning("lxml no disponible - funcionalidad limitada")
    
    def parse_cdr_xml(self, cdr_xml: str) -> Dict[str, Any]:
        """
        Parsea XML de CDR y extrae información estructurada
        
        Args:
            cdr_xml: XML de ApplicationResponse
            
        Returns:
            Dict con información del CDR parseada
        """
        if not LXML_AVAILABLE:
            # Fallback sin lxml
            return self._parse_cdr_simple(cdr_xml)
        
        try:
            # Limpiar XML antes de parsear
            cdr_xml = self._clean_xml_content(cdr_xml)
            
            # Parsear XML
            root = etree.fromstring(cdr_xml.encode('utf-8'))
            
            # Información básica
            basic_info = self._extract_basic_info(root)
            
            # Información de partes
            sender_info = self._extract_sender_info(root)
            receiver_info = self._extract_receiver_info(root)
            
            # Respuesta del documento
            document_response = self._extract_document_response(root)
            
            # Firma digital
            signature_info = self._extract_signature_info(root)
            
            # Determinar estado final
            final_status = self._determine_status(document_response)
            
            return {
                # Información básica del CDR
                'cdr_id': basic_info.get('id'),
                'ubl_version': basic_info.get('ubl_version'),
                'customization_id': basic_info.get('customization_id'),
                'issue_date': basic_info.get('issue_date'),
                'issue_time': basic_info.get('issue_time'),
                'response_date': basic_info.get('response_date'),
                'response_time': basic_info.get('response_time'),
                
                # Partes involucradas
                'sender': sender_info,  # SUNAT
                'receiver': receiver_info,  # Empresa
                
                # Respuesta del documento
                'document_reference': document_response.get('document_id'),
                'response_code': document_response.get('response_code'),
                'response_description': document_response.get('description'),
                'recipient_party': document_response.get('recipient_party'),
                
                # Firma
                'has_signature': signature_info.get('has_signature', False),
                'signature_id': signature_info.get('signature_id'),
                
                # Estado procesado
                'status': final_status['status'],
                'is_accepted': final_status['is_accepted'],
                'is_rejected': final_status['is_rejected'],
                'status_message': final_status['message'],
                
                # Metadatos
                'xml_content': cdr_xml,
                'parsed_at': timezone.now(),
                'parser_version': '1.0'
            }
            
        except Exception as e:
            logger.error(f"Error parseando CDR: {e}")
            # Fallback a parser simple
            return self._parse_cdr_simple(cdr_xml)
    
    def _parse_cdr_simple(self, cdr_xml: str) -> Dict[str, Any]:
        """Parser simple sin lxml usando regex"""
        import re
        
        try:
            # Extraer información básica usando regex
            cdr_id = self._extract_with_regex(cdr_xml, r'<cbc:ID[^>]*>([^<]+)</cbc:ID>')
            response_date = self._extract_with_regex(cdr_xml, r'<cbc:ResponseDate[^>]*>([^<]+)</cbc:ResponseDate>')
            response_time = self._extract_with_regex(cdr_xml, r'<cbc:ResponseTime[^>]*>([^<]+)</cbc:ResponseTime>')
            
            # Información del documento
            reference_id = self._extract_with_regex(cdr_xml, r'<cbc:ReferenceID[^>]*>([^<]+)</cbc:ReferenceID>')
            response_code = self._extract_with_regex(cdr_xml, r'<cbc:ResponseCode[^>]*>([^<]+)</cbc:ResponseCode>')
            description = self._extract_with_regex(cdr_xml, r'<cbc:Description[^>]*>([^<]+)</cbc:Description>')
            
            # Determinar estado
            is_accepted = response_code == '0'
            is_rejected = response_code and response_code.startswith(('2', '3'))
            
            if is_accepted:
                status = 'ACEPTADO'
                message = description or 'Documento aceptado por SUNAT'
            elif is_rejected:
                status = 'RECHAZADO'
                message = description or f'Documento rechazado - Código: {response_code}'
            else:
                status = 'DESCONOCIDO'
                message = description or f'Estado desconocido - Código: {response_code}'
            
            return {
                'cdr_id': cdr_id,
                'response_date': response_date,
                'response_time': response_time,
                'document_reference': reference_id,
                'response_code': response_code,
                'response_description': description,
                'status': status,
                'is_accepted': is_accepted,
                'is_rejected': is_rejected,
                'status_message': message,
                'xml_content': cdr_xml,
                'parsed_at': timezone.now(),
                'parser_version': '1.0-simple'
            }
            
        except Exception as e:
            logger.error(f"Error en parser simple: {e}")
            return {
                'error': str(e),
                'xml_content': cdr_xml,
                'parsed_at': timezone.now(),
                'parser_version': '1.0-error'
            }
    
    def _extract_with_regex(self, xml_content: str, pattern: str) -> Optional[str]:
        """Extrae contenido usando regex"""
        import re
        match = re.search(pattern, xml_content)
        return match.group(1) if match else None
    
    def _clean_xml_content(self, xml_content: str) -> str:
        """Limpia contenido XML para procesamiento"""
        if not xml_content:
            return xml_content
        
        # Remover BOM UTF-8 si existe
        if xml_content.startswith('\ufeff'):
            xml_content = xml_content[1:]
        
        # Remover espacios al inicio
        xml_content = xml_content.lstrip()
        
        return xml_content
    
    def _extract_basic_info(self, root) -> Dict[str, Any]:
        """Extrae información básica del ApplicationResponse"""
        if not LXML_AVAILABLE:
            return {}
        
        return {
            'id': self._get_text(root, './/cbc:ID'),
            'ubl_version': self._get_text(root, './/cbc:UBLVersionID'),
            'customization_id': self._get_text(root, './/cbc:CustomizationID'),
            'issue_date': self._get_text(root, './/cbc:IssueDate'),
            'issue_time': self._get_text(root, './/cbc:IssueTime'),
            'response_date': self._get_text(root, './/cbc:ResponseDate'),
            'response_time': self._get_text(root, './/cbc:ResponseTime')
        }
    
    def _extract_sender_info(self, root) -> Dict[str, Any]:
        """Extrae información del emisor (SUNAT)"""
        if not LXML_AVAILABLE:
            return {}
        
        sender = root.find('.//cac:SenderParty', self.namespaces)
        if sender is not None:
            return {
                'party_id': self._get_text(sender, './/cbc:ID'),
                'party_type': 'SUNAT'
            }
        return {}
    
    def _extract_receiver_info(self, root) -> Dict[str, Any]:
        """Extrae información del receptor (Empresa)"""
        if not LXML_AVAILABLE:
            return {}
        
        receiver = root.find('.//cac:ReceiverParty', self.namespaces)
        if receiver is not None:
            return {
                'party_id': self._get_text(receiver, './/cbc:ID'),
                'party_type': 'EMPRESA'
            }
        return {}
    
    def _extract_document_response(self, root) -> Dict[str, Any]:
        """Extrae respuesta del documento"""
        if not LXML_AVAILABLE:
            return {}
        
        doc_response = root.find('.//cac:DocumentResponse', self.namespaces)
        if doc_response is None:
            return {}
        
        response = doc_response.find('.//cac:Response', self.namespaces)
        doc_ref = doc_response.find('.//cac:DocumentReference', self.namespaces)
        recipient = doc_response.find('.//cac:RecipientParty', self.namespaces)
        
        result = {}
        
        if response is not None:
            result.update({
                'reference_id': self._get_text(response, './/cbc:ReferenceID'),
                'response_code': self._get_text(response, './/cbc:ResponseCode'),
                'description': self._get_text(response, './/cbc:Description')
            })
        
        if doc_ref is not None:
            result['document_id'] = self._get_text(doc_ref, './/cbc:ID')
        
        if recipient is not None:
            result['recipient_party'] = self._get_text(recipient, './/cbc:ID')
        
        return result
    
    def _extract_signature_info(self, root) -> Dict[str, Any]:
        """Extrae información de firma digital"""
        if not LXML_AVAILABLE:
            return {'has_signature': False}
        
        signature = root.find('.//ds:Signature', self.namespaces)
        
        if signature is not None:
            return {
                'has_signature': True,
                'signature_id': signature.get('Id', ''),
            }
        
        # Buscar firma en cac:Signature también
        cac_signature = root.find('.//cac:Signature', self.namespaces)
        if cac_signature is not None:
            return {
                'has_signature': True,
                'signature_id': self._get_text(cac_signature, './/cbc:ID'),
                'signatory_party': self._get_text(cac_signature, './/cac:SignatoryParty//cbc:Name')
            }
        
        return {'has_signature': False}
    
    def _determine_status(self, document_response: Dict[str, Any]) -> Dict[str, Any]:
        """Determina el estado final basado en el código de respuesta"""
        response_code = document_response.get('response_code', '')
        description = document_response.get('description', '')
        
        if response_code == '0':
            return {
                'status': 'ACEPTADO',
                'is_accepted': True,
                'is_rejected': False,
                'message': description or 'Documento aceptado por SUNAT'
            }
        elif response_code.startswith(('2', '3')):
            return {
                'status': 'RECHAZADO',
                'is_accepted': False,
                'is_rejected': True,
                'message': description or f'Documento rechazado - Código: {response_code}'
            }
        elif response_code.startswith('4'):
            return {
                'status': 'ACEPTADO_CON_OBSERVACIONES',
                'is_accepted': True,
                'is_rejected': False,
                'message': description or f'Documento aceptado con observaciones - Código: {response_code}'
            }
        else:
            return {
                'status': 'DESCONOCIDO',
                'is_accepted': False,
                'is_rejected': False,
                'message': description or f'Estado desconocido - Código: {response_code}'
            }
    
    def _get_text(self, element, xpath: str) -> Optional[str]:
        """Obtiene texto de un elemento usando XPath"""
        if element is None or not LXML_AVAILABLE:
            return None
        
        try:
            found = element.find(xpath, self.namespaces)
            return found.text if found is not None else None
        except Exception as e:
            logger.debug(f"Error extrayendo texto con xpath {xpath}: {e}")
            return None


class CDRGenerator:
    """Generador de CDR para respuestas simuladas"""
    
    def __init__(self):
        self.sunat_ruc = "20131312955"  # RUC de SUNAT
    
    def generate_cdr_response(self, documento, response_code: str = "0", 
                            description: str = None) -> str:
        """
        Genera CDR de respuesta simulado
        
        Args:
            documento: DocumentoElectronico
            response_code: Código de respuesta SUNAT
            description: Descripción personalizada
            
        Returns:
            XML de ApplicationResponse
        """
        
        now = datetime.now()
        cdr_id = str(int(now.timestamp() * 1000))  # ID único basado en timestamp
        
        if description is None:
            if response_code == "0":
                description = f"La Factura numero {documento.get_numero_completo()}, ha sido aceptada"
            elif response_code.startswith(('2', '3')):
                description = f"La Factura numero {documento.get_numero_completo()}, ha sido rechazada"
            else:
                description = f"Documento {documento.get_numero_completo()} procesado con código {response_code}"
        
        # Template de ApplicationResponse
        cdr_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<ar:ApplicationResponse xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" 
                        xmlns:ar="urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2" 
                        xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" 
                        xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2" 
                        xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2" 
                        xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  
  <ext:UBLExtensions>
    <ext:UBLExtension>
      <ext:ExtensionContent>
        <ds:Signature Id="SignSUNAT">
          <ds:SignedInfo>
            <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#WithComments"/>
            <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha512"/>
            <ds:Reference URI="">
              <ds:Transforms>
                <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
                <ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#WithComments"/>
              </ds:Transforms>
              <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha512"/>
              <ds:DigestValue>SIMULATED_DIGEST_VALUE_FOR_TESTING</ds:DigestValue>
            </ds:Reference>
          </ds:SignedInfo>
          <ds:SignatureValue>SIMULATED_SIGNATURE_VALUE_FOR_TESTING</ds:SignatureValue>
          <ds:KeyInfo>
            <ds:X509Data>
              <ds:X509Certificate>SIMULATED_CERTIFICATE_FOR_TESTING</ds:X509Certificate>
            </ds:X509Data>
          </ds:KeyInfo>
        </ds:Signature>
      </ext:ExtensionContent>
    </ext:UBLExtension>
  </ext:UBLExtensions>
  
  <cbc:UBLVersionID>2.0</cbc:UBLVersionID>
  <cbc:CustomizationID>1.0</cbc:CustomizationID>
  <cbc:ID>{cdr_id}</cbc:ID>
  <cbc:IssueDate>{documento.fecha_emision.strftime('%Y-%m-%d')}T{now.strftime('%H:%M:%S')}</cbc:IssueDate>
  <cbc:IssueTime>00:00:00</cbc:IssueTime>
  <cbc:ResponseDate>{now.strftime('%Y-%m-%d')}</cbc:ResponseDate>
  <cbc:ResponseTime>{now.strftime('%H:%M:%S')}</cbc:ResponseTime>
  
  <cac:Signature>
    <cbc:ID>SignSUNAT</cbc:ID>
    <cac:SignatoryParty>
      <cac:PartyIdentification>
        <cbc:ID>{self.sunat_ruc}</cbc:ID>
      </cac:PartyIdentification>
      <cac:PartyName>
        <cbc:Name>SUNAT</cbc:Name>
      </cac:PartyName>
    </cac:SignatoryParty>
    <cac:DigitalSignatureAttachment>
      <cac:ExternalReference>
        <cbc:URI>#SignSUNAT</cbc:URI>
      </cac:ExternalReference>
    </cac:DigitalSignatureAttachment>
  </cac:Signature>
  
  <cac:SenderParty>
    <cac:PartyIdentification>
      <cbc:ID>{self.sunat_ruc}</cbc:ID>
    </cac:PartyIdentification>
  </cac:SenderParty>
  
  <cac:ReceiverParty>
    <cac:PartyIdentification>
      <cbc:ID>{documento.empresa.ruc}</cbc:ID>
    </cac:PartyIdentification>
  </cac:ReceiverParty>
  
  <cac:DocumentResponse>
    <cac:Response>
      <cbc:ReferenceID>{documento.get_numero_completo()}</cbc:ReferenceID>
      <cbc:ResponseCode>{response_code}</cbc:ResponseCode>
      <cbc:Description>{description}</cbc:Description>
    </cac:Response>
    <cac:DocumentReference>
      <cbc:ID>{documento.get_numero_completo()}</cbc:ID>
    </cac:DocumentReference>
    <cac:RecipientParty>
      <cac:PartyIdentification>
        <cbc:ID>{documento.receptor_tipo_doc}-{documento.receptor_numero_doc}</cbc:ID>
      </cac:PartyIdentification>
    </cac:RecipientParty>
  </cac:DocumentResponse>
  
</ar:ApplicationResponse>'''
        
        return cdr_xml


# Instancias globales
cdr_parser = CDRParser()
cdr_generator = CDRGenerator()