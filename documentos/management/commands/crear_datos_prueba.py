# documentos/management/commands/crear_datos_prueba.py
"""
Comando para crear datos de prueba necesarios para los escenarios
"""

from django.core.management.base import BaseCommand
from documentos.models import TipoDocumento, Empresa

class Command(BaseCommand):
    help = 'Crea datos de prueba para los escenarios SUNAT'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Creando datos de prueba para escenarios SUNAT...')
        
        # Crear tipos de documento
        tipos_documento = [
            ('01', 'Factura'),
            ('03', 'Boleta de Venta'),
            ('07', 'Nota de Crédito'),
            ('08', 'Nota de Débito'),
            ('09', 'Guía de Remisión Remitente'),
        ]
        
        self.stdout.write('\n📄 Creando tipos de documento...')
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
        
        # Crear empresa de prueba
        self.stdout.write('\n🏢 Creando empresa de prueba...')
        
        empresa, created = Empresa.objects.get_or_create(
            ruc='20103129061',
            defaults={
                'razon_social': 'COMERCIAL LAVAGNA SAC',
                'nombre_comercial': 'LAVAGNA',
                'direccion': 'AV. LIMA 123, LIMA, LIMA',
                'ubigeo': '150101',
                'activo': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Empresa creada: {empresa.razon_social}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'→ Empresa ya existe: {empresa.razon_social}')
            )
        
        # Verificar certificado
        self.stdout.write('\n🔐 Verificando certificado...')
        import os
        cert_path = 'certificados/production/C23022479065.pfx'
        
        if os.path.exists(cert_path):
            self.stdout.write(
                self.style.SUCCESS(f'✓ Certificado encontrado: {cert_path}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Certificado NO encontrado: {cert_path}')
            )
            self.stdout.write('   Asegúrate de tener el certificado en la ubicación correcta')
        
        # Mostrar endpoints disponibles
        self.stdout.write('\n🧪 Endpoints de prueba disponibles:')
        endpoints = [
            'GET  /api/test/ - Menú de escenarios',
            'POST /api/test/scenario-1-boleta-completa/ - Boleta completa',
            'POST /api/test/scenario-2-factura-gravada/ - Factura gravada',
            'POST /api/test/scenario-3-factura-exonerada/ - Factura exonerada',
            'POST /api/test/scenario-4-factura-mixta/ - Factura mixta',
            'POST /api/test/scenario-5-factura-exportacion/ - Factura exportación',
            'POST /api/test/run-all-scenarios/ - Ejecutar todos',
        ]
        
        for endpoint in endpoints:
            self.stdout.write(f'   {endpoint}')
        
        self.stdout.write('\n🎉 ¡Datos de prueba creados exitosamente!')
        self.stdout.write('💡 Ejecuta: python manage.py runserver')
        self.stdout.write('🌐 Luego ve a: http://localhost:8000/api/test/')
        self.stdout.write('🔗 Para probar: https://probar-xml.nubefact.com/')