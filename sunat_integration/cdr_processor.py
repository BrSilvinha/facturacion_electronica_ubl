"""
Procesador de CDR (Constancia de Recepción) de SUNAT
Ubicación: sunat_integration/cdr_processor.py
"""

import zipfile
import logging
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional
from lxml import etree

from .exceptions import SUNATCDRError
from .utils import generate_correlation_id

logger = logging.getLogger('sunat')

class CDRProcessor:
    """
    Procesador de Constancia de Recepción (CDR) de SUNAT
    Extrae y procesa información de respuestas XML según Manual del Programador
    """
    
    def __init__(self):
        self.namespaces = {
            'ar': 'urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'ds': 'http://www.w3.org/2000/09/xmldsig#'
        }
    
    def process_cdr_zip(self, cdr_zip_content: bytes, correlation_id: str = None) -> Dict[str, Any]:
        """
        Procesa archivo ZIP de CDR de SUNAT
        
        Args:
            cdr_zip_content: Contenido del ZIP de CDR
            correlation_id: ID de correlación opcional
        
        Returns:
            Dict con información procesada del CDR
        """
        
        correlation_id = correlation_id or generate_correlation_id()
        
        try:
            logger.info(f"[{correlation_id}] Procesando CDR ZIP: {len(cdr_zip_content)} bytes")
            
            # Extraer XML del ZIP
            cdr_xml = self._extract_cdr_xml_from_zip(cdr_zip_content)
            
            # Procesar XML
            cdr_data = self.process_cdr_xml(cdr_xml, correlation_id)
            
            # Agregar información del ZIP
            cdr_data.update({
                'zip_size_bytes': len(cdr_zip_content),
                'zip_processed_at': datetime.now(),
                'correlation_id': correlation_id
            })
            
            logger.info(f"[{correlation_id}] CDR procesado: Estado {cdr_data['response_code']}")
            
            return cdr_data
            
        except Exception as e:
            logger.error(f"[{correlation_id}] Error procesando CDR ZIP: {e}")
            raise SUNATCDRError(f"Error procesando CDR: {e}")
    
    def process_cdr_xml(self, cdr_xml: str, correlation_id: str = None) -> Dict[str, Any]:
        """
        Procesa XML de CDR de SUNAT
        
        Args:
            cdr_xml: Contenido XML del CDR
            correlation_id: ID de correlación opcional
        
        Returns:
            Dict con información extraída del CDR
        """
        
        correlation_id = correlation_id or generate_correlation_id()
        
        try:
            logger.debug(f"[{correlation_id}] Procesando CDR XML: {len(cdr_xml)} caracteres")
            
            # Parsear XML
            root = etree.fromstring(cdr_xml.encode('utf-8'))
            
            # Extraer información básica
            basic_info = self._extract_basic_info(root)
            
            # Extraer información del emisor (SUNAT)
            sender_info = self._extract_sender_info(root)
            
            # Extraer información del receptor
            receiver_info = self._extract_receiver_info(root)
            
            # Extraer respuesta del documento
            document_response = self._extract_document_response(root)
            
            # Extraer notas/observaciones
            notes = self._extract_notes(root)
            
            # Determinar estado final
            final_status = self._determine_final_status(document_response, notes)
            
            cdr_data = {
                # Información básica
                'cdr_id': basic_info.get('id'),
                'issue_date': basic_info.get('issue_date'),
                'issue_time': basic_info.get('issue_time'),
                'response_date': basic_info.get('response_date'),
                'response_time': basic_info.get('response_time'),
                
                # Partes involucradas
                'sender': sender_info,
                'receiver': receiver_info,
                
                # Respuesta del documento
                'document_id': document_response.get('document_id'),
                'response_code': document_response.get('response_code'),
                'response_description': document_response.get('response_description'),
                
                # Notas y observaciones
                'notes': notes,
                'has_observations': len(notes) > 0,
                
                # Estado final
                'is_accepted': final_status['is_accepted'],
                'is_rejected': final_status['is_rejected'],
                'has_errors': final_status['has_errors'],
                'status_summary': final_status['summary'],
                
                # Metadatos
                'xml_content': cdr_xml,
                'processed_at': datetime.now(),
                'correlation_id': correlation_id
            }
            
            return cdr_data
            
        except etree.XMLSyntaxError as e:
            logger.error(f"[{correlation_id}] XML CDR inválido: {e}")
            raise SUNATCDRError(f"XML CDR inválido: {e}")
        
        except Exception as e:
            logger.error(f"[{correlation_id}] Error procesando CDR XML: {e}")
            raise SUNATCDRError(f"Error procesando CDR XML: {e}")
    
    def _extract_cdr_xml_from_zip(self, zip_content: bytes) -> str:
        """Extrae XML de CDR desde archivo ZIP"""
        
        try:
            with zipfile.ZipFile(BytesIO(zip_content), 'r') as zip_file:
                # Buscar archivo que comience con 'R-'
                cdr_files = [f for f in zip_file.namelist() if f.startswith('R-') and f.endswith('.xml')]
                
                if not cdr_files:
                    raise SUNATCDRError("No se encontró archivo CDR en el ZIP")
                
                if len(cdr_files) > 1:
                    logger.warning(f"Múltiples archivos CDR encontrados: {cdr_files}")
                
                # Leer primer archivo CDR
                cdr_filename = cdr_files[0]
                cdr_xml = zip_file.read(cdr_filename).decode('utf-8')
                
                logger.debug(f"CDR extraído: {cdr_filename}")
                return cdr_xml
                
        except zipfile.BadZipFile:
            raise SUNATCDRError("Archivo ZIP de CDR corrupto")
    
    def _extract_basic_info(self, root: etree.Element) -> Dict[str, Any]:
        """Extrae información básica del CDR"""
        
        return {
            'id': self._get_text(root, './/cbc:ID'),
            'issue_date': self._get_text(root, './/cbc:IssueDate'),
            'issue_time': self._get_text(root, './/cbc:IssueTime'),
            'response_date': self._get_text(root, './/cbc:ResponseDate'),
            'response_time': self._get_text(root, './/cbc:ResponseTime'),
            'ubl_version': self._get_text(root, './/cbc:UBLVersionID'),
            'customization_id': self._get_text(root, './/cbc:CustomizationID')
        }
    
    def _extract_sender_info(self, root: etree.Element) -> Dict[str, Any]:
        """Extrae información del emisor (SUNAT)"""
        
        sender_party = root.find('.//cac:SenderParty', self.namespaces)
        if sender_party is None:
            return {}
        
        return {
            'ruc': self._get_text(sender_party, './/cbc:ID'),
            'party_type': 'SUNAT'
        }
    
    def _extract_receiver_info(self, root: etree.Element) -> Dict[str, Any]:
        """Extrae información del receptor (empresa)"""
        
        receiver_party = root.find('.//cac:ReceiverParty', self.namespaces)
        if receiver_party is None:
            return {}
        
        return {
            'ruc': self._get_text(receiver_party, './/cbc:ID'),
            'party_type': 'EMPRESA'
        }
    
    def _extract_document_response(self, root: etree.Element) -> Dict[str, Any]:
        """Extrae respuesta del documento"""
        
        doc_response = root.find('.//cac:DocumentResponse', self.namespaces)
        if doc_response is None:
            return {}
        
        response = doc_response.find('.//cac:Response', self.namespaces)
        doc_reference = doc_response.find('.//cac:DocumentReference', self.namespaces)
        
        result = {}
        
        if response is not None:
            result.update({
                'reference_id': self._get_text(response, './/cbc:ReferenceID'),
                'response_code': self._get_text(response, './/cbc:ResponseCode'),
                'response_description': self._get_text(response, './/cbc:Description')
            })
        
        if doc_reference is not None:
            result['document_id'] = self._get_text(doc_reference, './/cbc:ID')
        
        return result
    
    def _extract_notes(self, root: etree.Element) -> list:
        """Extrae notas y observaciones"""
        
        notes = []
        note_elements = root.findall('.//cbc:Note', self.namespaces)
        
        for note_element in note_elements:
            note_text = note_element.text
            if note_text:
                # Parsear formato: CÓDIGO - DESCRIPCIÓN
                if ' - ' in note_text:
                    parts = note_text.split(' - ', 1)
                    notes.append({
                        'code': parts[0].strip(),
                        'description': parts[1].strip(),
                        'full_text': note_text
                    })
                else:
                    notes.append({
                        'code': None,
                        'description': note_text,
                        'full_text': note_text
                    })
        
        return notes
    
    def _determine_final_status(self, document_response: Dict[str, Any], notes: list) -> Dict[str, Any]:
        """Determina el estado final del documento según CDR"""
        
        response_code = document_response.get('response_code', '')
        
        # Códigos de respuesta SUNAT:
        # 0 = Aceptado
        # 2xxx = Rechazado por errores de validación
        # 3xxx = Rechazado por errores de contenido
        # 4xxx = Observaciones (aceptado con advertencias)
        
        is_accepted = response_code == '0'
        is_rejected = response_code.startswith(('2', '3')) if response_code else False
        has_errors = is_rejected
        has_observations = len(notes) > 0
        
        if is_accepted and not has_observations:
            summary = "ACEPTADO"
        elif is_accepted and has_observations:
            summary = "ACEPTADO_CON_OBSERVACIONES"
        elif is_rejected:
            summary = "RECHAZADO"
        else:
            summary = "ESTADO_DESCONOCIDO"
        
        return {
            'is_accepted': is_accepted,
            'is_rejected': is_rejected,
            'has_errors': has_errors,
            'has_observations': has_observations,
            'summary': summary
        }
    
    def _get_text(self, element: etree.Element, xpath: str) -> Optional[str]:
        """Obtiene texto de un elemento usando XPath"""
        
        if element is None:
            return None
        
        found = element.find(xpath, self.namespaces)
        return found.text if found is not None else None
    
    def get_error_summary(self, cdr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera resumen de errores del CDR
        
        Args:
            cdr_data: Datos procesados del CDR
        
        Returns:
            Dict con resumen de errores
        """
        
        summary = {
            'has_errors': cdr_data.get('has_errors', False),
            'has_observations': cdr_data.get('has_observations', False),
            'is_accepted': cdr_data.get('is_accepted', False),
            'response_code': cdr_data.get('response_code'),
            'response_description': cdr_data.get('response_description'),
            'error_count': 0,
            'observation_count': 0,
            'errors': [],
            'observations': []
        }
        
        notes = cdr_data.get('notes', [])
        
        for note in notes:
            note_code = note.get('code', '')
            
            # Clasificar según código
            if note_code and note_code.startswith(('2', '3')):
                # Error
                summary['errors'].append(note)
                summary['error_count'] += 1
            elif note_code and note_code.startswith('4'):
                # Observación
                summary['observations'].append(note)
                summary['observation_count'] += 1
            else:
                # Sin clasificar - asumir observación
                summary['observations'].append(note)
                summary['observation_count'] += 1
        
        return summary
    
    def format_cdr_for_display(self, cdr_data: Dict[str, Any]) -> str:
        """
        Formatea información del CDR para mostrar al usuario
        
        Args:
            cdr_data: Datos procesados del CDR
        
        Returns:
            String formateado para mostrar
        """
        
        lines = []
        
        # Encabezado
        lines.append("=" * 60)
        lines.append("CONSTANCIA DE RECEPCIÓN SUNAT")
        lines.append("=" * 60)
        
        # Información básica
        lines.append(f"ID CDR: {cdr_data.get('cdr_id', 'N/A')}")
        lines.append(f"Documento: {cdr_data.get('document_id', 'N/A')}")
        lines.append(f"Fecha emisión: {cdr_data.get('issue_date', 'N/A')}")
        lines.append(f"Hora emisión: {cdr_data.get('issue_time', 'N/A')}")
        lines.append("")
        
        # Estado
        status = cdr_data.get('status_summary', 'DESCONOCIDO')
        lines.append(f"ESTADO: {status}")
        lines.append(f"Código respuesta: {cdr_data.get('response_code', 'N/A')}")
        lines.append(f"Descripción: {cdr_data.get('response_description', 'N/A')}")
        lines.append("")
        
        # Notas y observaciones
        notes = cdr_data.get('notes', [])
        if notes:
            lines.append("NOTAS Y OBSERVACIONES:")
            lines.append("-" * 40)
            for i, note in enumerate(notes, 1):
                lines.append(f"{i}. {note.get('full_text', 'Sin descripción')}")
            lines.append("")
        
        # Información técnica
        lines.append("INFORMACIÓN TÉCNICA:")
        lines.append("-" * 40)
        lines.append(f"Procesado: {cdr_data.get('processed_at', 'N/A')}")
        lines.append(f"Correlación: {cdr_data.get('correlation_id', 'N/A')}")
        
        return "\n".join(lines)

# Instancia global
cdr_processor = CDRProcessor()