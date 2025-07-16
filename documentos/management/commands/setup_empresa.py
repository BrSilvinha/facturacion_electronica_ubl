# Crear archivo: documentos/management/commands/setup_empresa.py

from django.core.management.base import BaseCommand
from documentos.models import Empresa, TipoDocumento
import uuid

class Command(BaseCommand):
    help = 'Configura empresa y tipos de documento para el dashboard'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Configurando empresa y tipos de documento...')
        
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
                self.stdout.write(f'✓ Creado: {codigo} - {descripcion}')
            else:
                self.stdout.write(f'→ Ya existe: {codigo} - {descripcion}')
        
        # Crear empresa principal con ID específico
        empresa_id = "c11dba61-2837-4bcc-b197-301e78168582"
        
        self.stdout.write('\n🏢 Configurando empresa principal...')
        
        try:
            # Intentar obtener la empresa existente
            empresa = Empresa.objects.get(id=empresa_id)
            self.stdout.write(f'→ Empresa ya existe: {empresa.razon_social}')
            
        except Empresa.DoesNotExist:
            # Crear nueva empresa con ID específico
            empresa = Empresa()
            empresa.id = uuid.UUID(empresa_id)
            empresa.ruc = '20103129061'
            empresa.razon_social = 'COMERCIAL LAVAGNA SAC'
            empresa.nombre_comercial = 'LAVAGNA'
            empresa.direccion = 'AV. LIMA 123, LIMA, LIMA'
            empresa.ubigeo = '150101'
            empresa.activo = True
            empresa.save()
            
            self.stdout.write(f'✓ Empresa creada: {empresa.razon_social}')
        
        # Mostrar información de la empresa
        self.stdout.write('\n📋 INFORMACIÓN DE LA EMPRESA:')
        self.stdout.write(f'ID: {empresa.id}')
        self.stdout.write(f'RUC: {empresa.ruc}')
        self.stdout.write(f'Razón Social: {empresa.razon_social}')
        self.stdout.write(f'Activo: {empresa.activo}')
        
        # Verificar certificado
        self.stdout.write('\n🔐 Verificando certificado...')
        import os
        cert_path = 'certificados/production/C23022479065.pfx'
        
        if os.path.exists(cert_path):
            self.stdout.write(f'✓ Certificado encontrado: {cert_path}')
        else:
            self.stdout.write(f'❌ Certificado NO encontrado: {cert_path}')
        
        # Información del dashboard
        self.stdout.write('\n🎯 CONFIGURACIÓN PARA EL DASHBOARD:')
        self.stdout.write('En el archivo static/js/general.js:')
        self.stdout.write(f'EMPRESA_ID: "{empresa.id}"')
        
        self.stdout.write('\n✅ ¡Configuración completada!')
        self.stdout.write('💡 Ahora puedes usar el dashboard sin errores.')
        self.stdout.write('🚀 Ejecuta: python manage.py runserver')