# Crear directorio: documentos/management/commands/
# Archivo: documentos/management/commands/poblar_datos_iniciales.py

from django.core.management.base import BaseCommand
from documentos.models import TipoDocumento

class Command(BaseCommand):
    help = 'Pobla la base de datos con datos iniciales de SUNAT'

    def handle(self, *args, **options):
        # Tipos de Documento según catálogo SUNAT
        tipos_documento = [
            ('01', 'Factura'),
            ('03', 'Boleta de Venta'),
            ('07', 'Nota de Crédito'),
            ('08', 'Nota de Débito'),
            ('09', 'Guía de Remisión Remitente'),
            ('20', 'Comprobante de Retención'),
            ('40', 'Comprobante de Percepción'),
        ]
        
        self.stdout.write('Creando tipos de documento...')
        
        for codigo, descripcion in tipos_documento:
            tipo_doc, created = TipoDocumento.objects.get_or_create(
                codigo=codigo,
                defaults={'descripcion': descripcion}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado: {codigo} - {descripcion}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'→ Ya existe: {codigo} - {descripcion}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n¡Datos iniciales cargados exitosamente!')
        )