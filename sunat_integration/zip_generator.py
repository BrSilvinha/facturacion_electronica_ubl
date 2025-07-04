"""
Generador de archivos ZIP para SUNAT según especificaciones técnicas
Ubicación: sunat_integration/zip_generator.py
"""

import zipfile
import logging
from io import BytesIO
from pathlib import Path
from typing import Union, Dict, Any
from django.conf import settings

from .utils import get_sunat_filename, sanitize_xml_content
from .exceptions import SUNATZipError

logger = logging.getLogger('sunat')

class SUNATZipGenerator:
    """
    Generador de archivos ZIP según especificaciones SUNAT
    Manual del Programador - RS 097-2012/SUNAT
    """
    
    def __init__(self):
        self.config = settings.SUNAT_CONFIG
        self.compression = self.config.get('ZIP_COMPRESSION', zipfile.ZIP_DEFLATED)
        self.encoding = self.config.get('XML_ENCODING', 'UTF-8')
        
    def create_document_zip(self, documento, xml_firmado: str) -> bytes:
        """
        Crea archivo ZIP para documentos individuales (facturas, notas)
        
        Estructura según SUNAT:
        - Archivo ZIP con nombre específico
        - Carpeta dummy vacía
        - Archivo XML firmado
        
        Args:
            documento: Instancia de DocumentoElectronico
            xml_firmado: XML firmado digitalmente
        
        Returns:
            Contenido del archivo ZIP en bytes
        
        Raises:
            SUNATZipError: Si hay error creando el ZIP
        """
        
        try:
            logger.info(f"Creando ZIP para documento: {documento.get_numero_completo()}")
            
            # Generar nombres de archivo
            xml_filename = get_sunat_filename(documento, 'xml')
            
            # Limpiar contenido XML
            xml_content = sanitize_xml_content(xml_firmado)
            
            # Crear ZIP en memoria
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', self.compression) as zip_file:
                # 1. Crear carpeta dummy vacía (requerido por SUNAT)
                zip_file.writestr('dummy/', '')
                logger.debug("Carpeta dummy creada")
                
                # 2. Agregar XML firmado
                zip_file.writestr(xml_filename, xml_content.encode(self.encoding))
                logger.debug(f"XML agregado: {xml_filename}")
                
                # 3. Validar estructura del ZIP
                self._validate_zip_structure(zip_file, expected_files=[xml_filename])
            
            zip_content = zip_buffer.getvalue()
            
            logger.info(f"ZIP creado exitosamente: {len(zip_content)} bytes")
            
            return zip_content
            
        except Exception as e:
            logger.error(f"Error creando ZIP para documento {documento.get_numero_completo()}: {e}")
            raise SUNATZipError(f"Error creando ZIP: {e}")
    
    def create_summary_zip(self, archivo_resumen: str, xml_content: str) -> bytes:
        """
        Crea archivo ZIP para resúmenes diarios y comunicaciones de baja
        
        Args:
            archivo_resumen: Nombre del archivo (ej: 20123456789-RC-20250628-1)
            xml_content: Contenido XML del resumen
        
        Returns:
            Contenido del archivo ZIP en bytes
        """
        
        try:
            logger.info(f"Creando ZIP para resumen: {archivo_resumen}")
            
            xml_filename = f"{archivo_resumen}.xml"
            xml_content = sanitize_xml_content(xml_content)
            
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', self.compression) as zip_file:
                # Carpeta dummy
                zip_file.writestr('dummy/', '')
                
                # XML de resumen
                zip_file.writestr(xml_filename, xml_content.encode(self.encoding))
                
                self._validate_zip_structure(zip_file, expected_files=[xml_filename])
            
            zip_content = zip_buffer.getvalue()
            logger.info(f"ZIP resumen creado: {len(zip_content)} bytes")
            
            return zip_content
            
        except Exception as e:
            logger.error(f"Error creando ZIP resumen {archivo_resumen}: {e}")
            raise SUNATZipError(f"Error creando ZIP resumen: {e}")
    
    def create_batch_zip(self, documentos: list, xml_contents: Dict[str, str]) -> bytes:
        """
        Crea archivo ZIP para lotes de documentos (máximo 500)
        
        Args:
            documentos: Lista de DocumentoElectronico
            xml_contents: Dict con {documento_id: xml_firmado}
        
        Returns:
            Contenido del archivo ZIP en bytes
        """
        
        try:
            if len(documentos) > 500:
                raise SUNATZipError("Lote excede máximo de 500 documentos")
            
            logger.info(f"Creando ZIP lote con {len(documentos)} documentos")
            
            zip_buffer = BytesIO()
            expected_files = []
            
            with zipfile.ZipFile(zip_buffer, 'w', self.compression) as zip_file:
                # Carpeta dummy
                zip_file.writestr('dummy/', '')
                
                # Agregar cada documento
                for documento in documentos:
                    xml_filename = get_sunat_filename(documento, 'xml')
                    xml_content = xml_contents.get(str(documento.id))
                    
                    if not xml_content:
                        raise SUNATZipError(f"XML no encontrado para documento {documento.get_numero_completo()}")
                    
                    xml_content = sanitize_xml_content(xml_content)
                    zip_file.writestr(xml_filename, xml_content.encode(self.encoding))
                    expected_files.append(xml_filename)
                
                self._validate_zip_structure(zip_file, expected_files)
            
            zip_content = zip_buffer.getvalue()
            logger.info(f"ZIP lote creado: {len(zip_content)} bytes, {len(documentos)} documentos")
            
            return zip_content
            
        except Exception as e:
            logger.error(f"Error creando ZIP lote: {e}")
            raise SUNATZipError(f"Error creando ZIP lote: {e}")
    
    def save_zip_to_file(self, zip_content: bytes, filepath: Union[str, Path]) -> Path:
        """
        Guarda contenido ZIP en archivo físico
        
        Args:
            zip_content: Contenido del ZIP
            filepath: Ruta donde guardar
        
        Returns:
            Path del archivo guardado
        """
        
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(zip_content)
            
            logger.info(f"ZIP guardado en: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error guardando ZIP: {e}")
            raise SUNATZipError(f"Error guardando ZIP: {e}")
    
    def extract_zip_content(self, zip_content: bytes) -> Dict[str, str]:
        """
        Extrae contenido de un archivo ZIP
        
        Args:
            zip_content: Contenido del ZIP en bytes
        
        Returns:
            Dict con {filename: content}
        """
        
        try:
            files_content = {}
            
            with zipfile.ZipFile(BytesIO(zip_content), 'r') as zip_file:
                for filename in zip_file.namelist():
                    if filename.endswith('.xml'):
                        content = zip_file.read(filename).decode(self.encoding)
                        files_content[filename] = content
            
            logger.info(f"ZIP extraído: {len(files_content)} archivos XML")
            return files_content
            
        except Exception as e:
            logger.error(f"Error extrayendo ZIP: {e}")
            raise SUNATZipError(f"Error extrayendo ZIP: {e}")
    
    def _validate_zip_structure(self, zip_file: zipfile.ZipFile, expected_files: list):
        """
        Valida estructura del ZIP según especificaciones SUNAT
        
        Args:
            zip_file: Archivo ZIP abierto
            expected_files: Lista de archivos esperados
        """
        
        file_list = zip_file.namelist()
        
        # Verificar carpeta dummy
        if 'dummy/' not in file_list:
            raise SUNATZipError("Falta carpeta dummy/ requerida por SUNAT")
        
        # Verificar archivos XML esperados
        for expected_file in expected_files:
            if expected_file not in file_list:
                raise SUNATZipError(f"Archivo esperado no encontrado: {expected_file}")
        
        # Verificar que no hay archivos no permitidos
        xml_files = [f for f in file_list if f.endswith('.xml')]
        if len(xml_files) != len(expected_files):
            raise SUNATZipError("Número de archivos XML no coincide con lo esperado")
        
        logger.debug(f"Estructura ZIP validada: {len(file_list)} archivos")
    
    def get_zip_info(self, zip_content: bytes) -> Dict[str, Any]:
        """
        Obtiene información detallada de un archivo ZIP
        
        Args:
            zip_content: Contenido del ZIP
        
        Returns:
            Dict con información del ZIP
        """
        
        try:
            info = {
                'size_bytes': len(zip_content),
                'files': [],
                'xml_files_count': 0,
                'has_dummy_folder': False,
                'compression_ratio': 0
            }
            
            with zipfile.ZipFile(BytesIO(zip_content), 'r') as zip_file:
                uncompressed_size = 0
                
                for file_info in zip_file.filelist:
                    file_data = {
                        'filename': file_info.filename,
                        'size_compressed': file_info.compress_size,
                        'size_uncompressed': file_info.file_size,
                        'is_xml': file_info.filename.endswith('.xml')
                    }
                    
                    info['files'].append(file_data)
                    uncompressed_size += file_info.file_size
                    
                    if file_data['is_xml']:
                        info['xml_files_count'] += 1
                    
                    if file_info.filename == 'dummy/':
                        info['has_dummy_folder'] = True
                
                # Calcular ratio de compresión
                if uncompressed_size > 0:
                    info['compression_ratio'] = round(
                        (1 - len(zip_content) / uncompressed_size) * 100, 2
                    )
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo info ZIP: {e}")
            return {'error': str(e)}

# Instancia global
zip_generator = SUNATZipGenerator()