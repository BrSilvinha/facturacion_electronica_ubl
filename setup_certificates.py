#!/usr/bin/env python
"""
Script para configurar la estructura de certificados para Nivel 2
Ejecutar desde la raíz del proyecto Django
"""

import os
import sys
from pathlib import Path

def create_certificate_structure():
    """Crea la estructura de directorios para certificados"""
    
    # Directorio base del proyecto
    base_dir = Path(__file__).parent
    
    # Directorios a crear
    directories = [
        'certificados',
        'certificados/test',
        'certificados/production',
        'certificados/backup',
        'certificados/templates',
        'logs',  # Para logs de firma digital
    ]
    
    print("🔐 Configurando estructura de certificados para Nivel 2...")
    print(f"📁 Directorio base: {base_dir}")
    
    for directory in directories:
        dir_path = base_dir / directory
        
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Creado: {directory}/")
        else:
            print(f"ℹ️  Ya existe: {directory}/")
    
    # Crear archivos de configuración
    create_config_files(base_dir)
    
    # Crear .gitignore para certificados de producción
    create_gitignore(base_dir)
    
    print("\n🎉 ¡Estructura de certificados configurada exitosamente!")
    print("📝 Próximo paso: Implementar generadores de certificados de prueba")

def create_config_files(base_dir):
    """Crea archivos de configuración para certificados"""
    
    # Configuración para certificados de test
    test_config = """# Configuración para Certificados de Prueba
# Archivo: certificados/test/config.ini

[DEFAULT]
country = PE
state = Lima
locality = Lima
organization = Empresa Test
organizational_unit = IT Department
email = test@empresa.com

[TEST_CERT_1]
common_name = Test Certificate 1
ruc = 20123456789
validity_days = 365
key_size = 2048

[TEST_CERT_2]
common_name = Test Certificate 2
ruc = 20987654321
validity_days = 730
key_size = 2048
"""
    
    config_path = base_dir / 'certificados' / 'test' / 'config.ini'
    if not config_path.exists():
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(test_config)
        print(f"✅ Creado: certificados/test/config.ini")
    
    # README para certificados
    readme_content = """# 🔐 Gestión de Certificados Digitales

## Estructura de Directorios

- `test/` - Certificados auto-firmados para desarrollo y testing
- `production/` - Certificados reales (NO incluir en git)
- `backup/` - Respaldos de certificados
- `templates/` - Plantillas y configuraciones

## Certificados de Test

Los certificados en `test/` son auto-firmados y solo para desarrollo.
**NO USAR EN PRODUCCIÓN**.

Generar certificados de test:
```bash
python certificados/generate_test_certs.py
```

## Certificados de Producción

Los certificados reales deben:
1. Ser emitidos por una CA autorizada por SUNAT
2. Estar en formato PFX con password
3. Almacenarse de forma segura
4. **NUNCA** incluirse en control de versiones

## Seguridad

- Los certificados de producción están en `.gitignore`
- Los passwords se almacenan encriptados en la BD
- Los certificados se cargan en memoria solo cuando se necesitan

## Estado del Nivel 2

✅ Estructura creada
⏳ Generador de certificados de test
⏳ Gestor de certificados
⏳ Implementación XML-DSig
⏳ Integración con API
"""
    
    readme_path = base_dir / 'certificados' / 'README.md'
    if not readme_path.exists():
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✅ Creado: certificados/README.md")

def create_gitignore(base_dir):
    """Crea/actualiza .gitignore para proteger certificados de producción"""
    
    gitignore_content = """
# 🔐 CERTIFICADOS DIGITALES - NIVEL 2
# Proteger certificados de producción
certificados/production/
certificados/backup/
*.pfx
*.p12
*.key
*.pem
!certificados/test/*.pfx
!certificados/test/*.pem

# Logs de firma digital
logs/
*.log
"""
    
    gitignore_path = base_dir / '.gitignore'
    
    if gitignore_path.exists():
        # Leer contenido existente
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Solo agregar si no existe ya
        if 'CERTIFICADOS DIGITALES' not in existing_content:
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write(gitignore_content)
            print(f"✅ Actualizado: .gitignore con protección de certificados")
        else:
            print(f"ℹ️  .gitignore ya tiene protección de certificados")
    else:
        # Crear nuevo .gitignore
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print(f"✅ Creado: .gitignore con protección de certificados")

if __name__ == '__main__':
    try:
        create_certificate_structure()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)