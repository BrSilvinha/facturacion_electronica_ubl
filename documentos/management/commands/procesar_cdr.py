# documentos/management/commands/procesar_cdr.py
"""
Comando para procesar CDR desde línea de comandos
Uso: python manage.py procesar_cdr --archivo cdr.xml --documento-id uuid
"""

import os
import base64
import zipfile
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.shortcuts import get_object_or_404
from documentos.models import DocumentoElectronico, LogOperacion
from sunat_integration.cdr_parser import cdr_parser

class Command(BaseCommand):
    help = 'Procesa CDR (Constancia de Recepción) de SUNAT'

    def add_arguments(self, parser):
        parser.add_argument(
            '--archivo',
            type=str,
            help='Ruta al archivo CDR (XML o ZIP)',
            required=True
        )
        parser.add_argument(
            '--documento-id',
            type=str,
            help='ID del documento a actualizar',
            required=True
        )
        parser.add_argument(
            '--no-actualizar',
            action='store_true',
            help='Solo analizar CDR sin actualizar documento',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada',
        )

    def handle(self, *args, **options):
        archivo = options['archivo']
        documento_id = options['documento_id']
        no_actualizar = options['no_actualizar']
        verbose = options['verbose']
        
        self.stdout.write("🔍 Procesador de CDR SUNAT")
        self.stdout.write("=" * 50)
        
        # Verificar archivo
        if not os.path.exists(archivo):
            raise CommandError(f"Archivo no encontrado: {archivo}")
        
        # Obtener documento
        try:
            documento = get_object_or_404(DocumentoElectronico, id=documento_id)
            self.stdout.write(f"📄 Documento: {documento.get_numero_completo()}")
        except Exception as e:
            raise CommandError(f"Error obteniendo documento: {e}")
        
        # Leer y procesar archivo
        try:
            cdr_xml = self._extract_cdr_content(archivo)
            self.stdout.write(f"📁 Archivo leído: {len(cdr_xml)} caracteres")
            
            if verbose:
                self.stdout.write(f"📝 Ruta: {archivo}")
                self.stdout.write(f"📊 Tamaño: {len(cdr_xml)} bytes")
        
        except Exception as e:
            raise CommandError(f"Error leyendo archivo: {e}")
        
        # Procesar CDR
        try:
            self.stdout.write("\n🔄 Procesando CDR...")
            cdr_data = cdr_parser.parse_cdr_xml(cdr_xml)
            
            self.stdout.write(self.style.SUCCESS("✅ CDR procesado exitosamente"))
            
            # Mostrar información del CDR
            self._display_cdr_info(cdr_data, verbose)
            
        except Exception as e:
            raise CommandError(f"Error procesando CDR: {e}")
        
        # Actualizar documento si se solicita
        if not no_actualizar:
            try:
                self.stdout.write("\n💾 Actualizando documento...")
                self._update_document(documento, cdr_data, cdr_xml)
                self.stdout.write(self.style.SUCCESS("✅ Documento actualizado"))
                
                # Log de operación
                LogOperacion.objects.create(
                    documento=documento,
                    operacion='CDR_COMMAND',
                    estado='SUCCESS',
                    mensaje=f'CDR procesado desde comando - Estado: {cdr_data["status"]}',
                    correlation_id=f'CMD-{archivo}'
                )
                
            except Exception as e:
                raise CommandError(f"Error actualizando documento: {e}")
        else:
            self.stdout.write("\n⏭️  Documento no actualizado (--no-actualizar)")
        
        self.stdout.write("\n🎉 Procesamiento completado")
    
    def _extract_cdr_content(self, archivo_path: str) -> str:
        """Extrae contenido CDR desde archivo XML o ZIP"""
        archivo_path = Path(archivo_path)
        
        if archivo_path.suffix.lower() == '.xml':
            # Archivo XML directo
            with open(archivo_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif archivo_path.suffix.lower() == '.zip':
            # Archivo ZIP
            with zipfile.ZipFile(archivo_path, 'r') as zip_file:
                # Buscar archivo CDR (comienza con R-)
                cdr_files = [f for f in zip_file.namelist() 
                           if f.startswith('R-') and f.endswith('.xml')]
                
                if not cdr_files:
                    raise CommandError("No se encontró archivo CDR en el ZIP")
                
                if len(cdr_files) > 1:
                    self.stdout.write(f"⚠️  Múltiples CDR encontrados: {cdr_files}")
                    self.stdout.write(f"📄 Usando: {cdr_files[0]}")
                
                return zip_file.read(cdr_files[0]).decode('utf-8')
        
        else:
            raise CommandError(f"Tipo de archivo no soportado: {archivo_path.suffix}")
    
    def _display_cdr_info(self, cdr_data: dict, verbose: bool = False):
        """Muestra información del CDR procesado"""
        
        self.stdout.write("\n📋 INFORMACIÓN DEL CDR")
        self.stdout.write("-" * 30)
        
        # Información básica
        self.stdout.write(f"🆔 ID CDR: {cdr_data.get('cdr_id', 'N/A')}")
        self.stdout.write(f"📅 Fecha emisión: {cdr_data.get('issue_date', 'N/A')}")
        self.stdout.write(f"🕐 Hora emisión: {cdr_data.get('issue_time', 'N/A')}")
        self.stdout.write(f"📅 Fecha respuesta: {cdr_data.get('response_date', 'N/A')}")
        self.stdout.write(f"🕐 Hora respuesta: {cdr_data.get('response_time', 'N/A')}")
        
        # Estado
        status = cdr_data.get('status', 'DESCONOCIDO')
        status_icon = "✅" if cdr_data.get('is_accepted') else "❌" if cdr_data.get('is_rejected') else "❓"
        
        self.stdout.write(f"\n{status_icon} ESTADO: {status}")
        self.stdout.write(f"📄 Documento: {cdr_data.get('document_reference', 'N/A')}")
        self.stdout.write(f"🔢 Código: {cdr_data.get('response_code', 'N/A')}")
        self.stdout.write(f"📝 Descripción: {cdr_data.get('response_description', 'N/A')}")
        
        # Partes
        if verbose:
            self.stdout.write(f"\n🏢 PARTES INVOLUCRADAS")
            self.stdout.write(f"📤 Emisor: {cdr_data.get('sender', {}).get('party_id', 'N/A')}")
            self.stdout.write(f"📥 Receptor: {cdr_data.get('receiver', {}).get('party_id', 'N/A')}")
            
            # Firma
            if cdr_data.get('has_signature'):
                self.stdout.write(f"\n✍️  FIRMA DIGITAL")
                self.stdout.write(f"🆔 ID Firma: {cdr_data.get('signature_id', 'N/A')}")
                self.stdout.write("✅ Documento firmado digitalmente")
            
            # Metadatos
            self.stdout.write(f"\n🔧 METADATOS")
            self.stdout.write(f"📦 Versión UBL: {cdr_data.get('ubl_version', 'N/A')}")
            self.stdout.write(f"🔧 Customization: {cdr_data.get('customization_id', 'N/A')}")
            self.stdout.write(f"⏰ Procesado: {cdr_data.get('parsed_at', 'N/A')}")
    
    def _update_document(self, documento, cdr_data: dict, cdr_xml: str):
        """Actualiza documento con información del CDR"""
        from django.utils import timezone
        
        # Actualizar campos CDR
        documento.cdr_xml = cdr_xml
        documento.cdr_estado = cdr_data['status']
        documento.cdr_codigo_respuesta = cdr_data.get('response_code', '0')
        documento.cdr_descripcion = cdr_data.get('response_description', '')
        documento.cdr_fecha_recepcion = timezone.now()
        
        # Actualizar estado del documento
        if cdr_data['is_accepted']:
            documento.estado = 'ACEPTADO'
        elif cdr_data['is_rejected']:
            documento.estado = 'RECHAZADO'
        else:
            documento.estado = 'PROCESADO'
        
        documento.save()
        
        self.stdout.write(f"📊 Estado documento: {documento.estado}")
        self.stdout.write(f"📊 Estado CDR: {documento.cdr_estado}")
        self.stdout.write(f"🔢 Código respuesta: {documento.cdr_codigo_respuesta}")
