#!/usr/bin/env python
"""
Corrector de problemas específicos de Windows
Ubicación: fix_windows_issues.py (en la raíz del proyecto)
"""

import os
import sys
import django
from pathlib import Path

# Configurar encoding para Windows
if sys.platform.startswith('win'):
    import locale
    # Forzar UTF-8 en Windows
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

def fix_database_issues():
    """Corrige problemas de base de datos"""
    print("🔧 Corrigiendo problemas de base de datos...")
    
    try:
        django.setup()
        
        # Verificar y corregir comando de poblado
        from django.core.management import execute_from_command_line
        
        print("   📊 Ejecutando migraciones nuevamente...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Poblar datos iniciales de forma segura
        print("   📋 Poblando datos iniciales...")
        from documentos.models import TipoDocumento
        
        tipos_documento = [
            ('01', 'Factura'),
            ('03', 'Boleta de Venta'),
            ('07', 'Nota de Crédito'),
            ('08', 'Nota de Débito'),
        ]
        
        for codigo, descripcion in tipos_documento:
            tipo_doc, created = TipoDocumento.objects.get_or_create(
                codigo=codigo,
                defaults={'descripcion': descripcion}
            )
            
            if created:
                print(f"   ✅ Creado: {codigo} - {descripcion}")
            else:
                print(f"   ℹ️  Ya existe: {codigo} - {descripcion}")
        
        print("   ✅ Base de datos corregida")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def fix_log_model():
    """Corrige el modelo LogOperacion para permitir documento_id nulo"""
    print("\n🔧 Corrigiendo modelo LogOperacion...")
    
    try:
        # Verificar si el campo documento_id puede ser nulo
        from documentos.models import LogOperacion
        
        # Crear migración para permitir documento_id nulo
        migration_content = '''# Generated fix for LogOperacion
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('documentos', '0002_alter_documentolinea_valor_unitario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logoperacion',
            name='documento',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='documentos.documentoelectronico'),
        ),
    ]
'''
        
        # Crear archivo de migración
        migration_file = Path('documentos/migrations/0003_alter_logoperacion_documento.py')
        
        if not migration_file.exists():
            with open(migration_file, 'w', encoding='utf-8') as f:
                f.write(migration_content)
            
            print("   ✅ Migración creada")
        else:
            print("   ℹ️  Migración ya existe")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def fix_sunat_urls():
    """Corrige URLs de SUNAT en .env"""
    print("\n🔧 Corrigiendo URLs de SUNAT...")
    
    try:
        env_file = Path('.env')
        
        if not env_file.exists():
            print("   ❌ Archivo .env no encontrado")
            return False
        
        # Leer contenido actual
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # URLs corregidas
        new_urls = {
            'SUNAT_BETA_WSDL_FACTURA': 'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl',
            'SUNAT_BETA_WSDL_GUIA': 'https://e-beta.sunat.gob.pe/ol-ti-itemision-guia-gem-beta/billService?wsdl',
            'SUNAT_BETA_WSDL_RETENCION': 'https://e-beta.sunat.gob.pe/ol-ti-itemision-otroscpe-gem-beta/billService?wsdl',
        }
        
        # Reemplazar URLs
        updated = False
        for key, new_url in new_urls.items():
            old_pattern = f"{key}=https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
            new_pattern = f"{key}={new_url}"
            
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                updated = True
        
        # Guardar cambios
        if updated:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("   ✅ URLs de SUNAT actualizadas")
        else:
            print("   ℹ️  URLs ya están correctas")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def create_test_empresa():
    """Crea empresa de prueba con RUC correcto"""
    print("\n🔧 Creando empresa de prueba...")
    
    try:
        from documentos.models import Empresa
        
        empresa, created = Empresa.objects.get_or_create(
            ruc='20123456789',
            defaults={
                'razon_social': 'EMPRESA TEST FACTURACIÓN SAC',
                'nombre_comercial': 'EMPRESA TEST',
                'direccion': 'AV. LARCO 123, MIRAFLORES, LIMA',
                'ubigeo': '150101',
                'activo': True
            }
        )
        
        if created:
            print(f"   ✅ Empresa creada: {empresa.razon_social}")
        else:
            print(f"   ℹ️  Empresa existe: {empresa.razon_social}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def run_safe_test():
    """Ejecuta una prueba segura sin problemas de encoding"""
    print("\n🧪 Ejecutando prueba segura...")
    
    try:
        # Probar generación XML simple
        from conversion.generators import UBLGeneratorFactory
        
        supported_types = UBLGeneratorFactory.get_supported_document_types()
        print(f"   ✅ Tipos de documento soportados: {supported_types}")
        
        # Probar cálculos tributarios
        from conversion.utils.calculations import TributaryCalculator
        from decimal import Decimal
        
        result = TributaryCalculator.calculate_line_totals(
            cantidad=Decimal('1'),
            valor_unitario=Decimal('100.00'),
            afectacion_igv='10'
        )
        
        print(f"   ✅ Cálculo tributario: Valor {result['valor_venta']}, IGV {result['igv_monto']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 CORRECTOR DE PROBLEMAS WINDOWS")
    print("Sistema de Facturación Electrónica")
    print("=" * 50)
    
    fixes = [
        ("Base de datos", fix_database_issues),
        ("Modelo LogOperacion", fix_log_model),
        ("URLs SUNAT", fix_sunat_urls),
        ("Empresa de prueba", create_test_empresa),
        ("Prueba segura", run_safe_test),
    ]
    
    success_count = 0
    
    for fix_name, fix_func in fixes:
        try:
            if fix_func():
                success_count += 1
        except Exception as e:
            print(f"💥 Error en {fix_name}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESUMEN: {success_count}/{len(fixes)} correcciones exitosas")
    
    if success_count == len(fixes):
        print("🎉 ¡Todos los problemas corregidos!")
        print("\n📝 Próximos pasos:")
        print("1. python manage.py migrate")
        print("2. python test_signature.py")
        print("3. python manage.py runserver")
        return 0
    else:
        print("⚠️  Algunos problemas persisten")
        print("🔧 Revisar errores específicos")
        return 1

if __name__ == '__main__':
    exit(main())