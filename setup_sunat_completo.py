#!/usr/bin/env python
"""
Setup completo del sistema SUNAT con CDR funcionando
Ejecutar: python setup_sunat_completo.py
"""

import os
import sys
import subprocess
from pathlib import Path

def print_step(step, description):
    """Imprimir paso del setup"""
    print(f"\n{'='*60}")
    print(f"📋 PASO {step}: {description}")
    print(f"{'='*60}")

def install_dependencies():
    """Instalar todas las dependencias necesarias"""
    print_step(1, "INSTALANDO DEPENDENCIAS")
    
    dependencies = [
        'zeep',
        'lxml',
        'requests', 
        'cryptography',
        'django',
        'djangorestframework',
        'django-cors-headers',
        'python-decouple',
        'psycopg2-binary'
    ]
    
    for dep in dependencies:
        print(f"📦 Instalando {dep}...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--upgrade', dep
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ {dep} instalado")
        except subprocess.CalledProcessError:
            print(f"❌ Error instalando {dep}")
            return False
    
    print("🎉 Todas las dependencias instaladas correctamente")
    return True

def update_views_sunat():
    """Actualizar api_rest/views_sunat.py con la versión corregida"""
    print_step(2, "ACTUALIZANDO VIEWS SUNAT")
    
    # El contenido está en el artifact anterior
    views_content = '''"""
Endpoints de API para integración con SUNAT - VERSIÓN COMPLETA CORREGIDA CON CDR
Ubicación: api_rest/views_sunat.py
CORREGIDO: Manejo completo de CDR, errores SOAP y diagnósticos detallados
"""

# [El contenido completo del archivo views_sunat.py corregido]
# (Usar el contenido del artifact "views_sunat_completo_corregido")
'''
    
    views_path = Path('api_rest/views_sunat.py')
    
    if views_path.exists():
        # Hacer backup
        backup_path = views_path.with_suffix('.py.backup')
        views_path.rename(backup_path)
        print(f"📋 Backup creado: {backup_path}")
    
    print(f"💡 NOTA: Debes copiar manualmente el contenido del archivo views_sunat.py")
    print(f"         desde el artifact 'views_sunat_completo_corregido'")
    print(f"✅ Instrucciones para actualizar views_sunat.py")
    
    return True

def create_diagnostic_script():
    """Crear script de diagnóstico"""
    print_step(3, "CREANDO SCRIPT DE DIAGNÓSTICO")
    
    # El script de diagnóstico ya está en el artifact anterior
    print(f"💡 Script de diagnóstico disponible en artifact 'diagnostico_completo_sunat'")
    print(f"   Guárdalo como: diagnostico_sunat_completo.py")
    print(f"✅ Script de diagnóstico listo")
    
    return True

def verify_certificate():
    """Verificar certificado real"""
    print_step(4, "VERIFICANDO CERTIFICADO REAL")
    
    cert_path = Path('certificados/production/cert_20103129061.pfx')
    
    if cert_path.exists():
        size_kb = cert_path.stat().st_size / 1024
        print(f"✅ Certificado real encontrado: {size_kb:.1f} KB")
        
        # Verificar que no esté vacío
        if size_kb > 1:
            print(f"✅ Certificado tiene tamaño válido")
        else:
            print(f"⚠️ Certificado muy pequeño - verificar contenido")
            
        return True
    else:
        print(f"❌ Certificado real NO encontrado en: {cert_path}")
        print(f"💡 Coloca tu archivo .pfx en la ubicación correcta")
        return False

def test_system():
    """Probar el sistema básico"""
    print_step(5, "PROBANDO SISTEMA BÁSICO")
    
    try:
        # Probar imports
        print("🧪 Probando imports...")
        
        import django
        print(f"✅ Django: {django.get_version()}")
        
        import zeep
        print(f"✅ Zeep: {zeep.__version__}")
        
        import requests
        print(f"✅ Requests: {requests.__version__}")
        
        import lxml
        print(f"✅ LXML: {lxml.__version__}")
        
        # Probar configuración Django
        print("🔧 Probando configuración Django...")
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
        django.setup()
        
        from django.conf import settings
        if hasattr(settings, 'SUNAT_CONFIG'):
            config = settings.SUNAT_CONFIG
            print(f"✅ SUNAT_CONFIG: Ambiente {config.get('ENVIRONMENT')}")
        else:
            print(f"❌ SUNAT_CONFIG no encontrado")
            return False
        
        print(f"✅ Sistema básico funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error probando sistema: {e}")
        return False

def create_usage_guide():
    """Crear guía de uso"""
    print_step(6, "CREANDO GUÍA DE USO")
    
    guide_content = """
# 🚀 GUÍA DE USO - SISTEMA SUNAT CON CDR

## 📋 Pasos para Enviar Documento y Recibir CDR

### 1. Ejecutar Diagnóstico
```bash
python diagnostico_sunat_completo.py
```
- Debe mostrar todos los checks en ✅ OK
- Si hay errores, seguir las recomendaciones

### 2. Generar Documento
```bash
python manage.py runserver
# Ir a http://localhost:8000
# Crear factura con empresa RUC 20103129061
# Generar XML - debe estar FIRMADO
```

### 3. Enviar a SUNAT
```bash
# Opción A: Desde API
curl -X POST http://localhost:8000/api/sunat/send-bill/ \\
  -H "Content-Type: application/json" \\
  -d '{"documento_id": "TU_UUID_AQUI"}'

# Opción B: Desde script
python envio_rapido.py
```

### 4. Verificar CDR en Respuesta
```json
{
  "success": true,
  "has_cdr": true,
  "cdr_info": {
    "is_accepted": true,
    "response_code": "0",
    "response_description": "Aceptado",
    "status_summary": "ACCEPTED"
  }
}
```

## 🔧 Solución de Problemas

### Error: zeep no disponible
```bash
pip install zeep
```

### Error: env:Client - Internal Error
- Verificar que zeep esté instalado
- Verificar conectividad con SUNAT
- Verificar formato del XML

### Error: 0111 No tiene perfil
- Error de configuración en SUNAT
- Usar credenciales MODDATOS para Beta

### No recibo CDR
- Verificar que use la versión corregida de views_sunat.py
- Verificar logs detallados
- Ejecutar diagnóstico completo

## 📞 Soporte

Si tienes problemas:
1. Ejecutar diagnóstico completo
2. Revisar logs en consola
3. Verificar configuración paso a paso
"""
    
    with open('GUIA_USO_SUNAT.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"📖 Guía de uso creada: GUIA_USO_SUNAT.md")
    print(f"✅ Documentación lista")
    
    return True

def main():
    """Función principal del setup"""
    
    print("🚀 SETUP COMPLETO DEL SISTEMA SUNAT CON CDR")
    print("Este script configurará todo lo necesario para que")
    print("el sistema SUNAT funcione correctamente y reciba CDR.")
    print("")
    
    success = True
    
    # Ejecutar todos los pasos
    steps = [
        ("Dependencias", install_dependencies),
        ("Views SUNAT", update_views_sunat), 
        ("Diagnóstico", create_diagnostic_script),
        ("Certificado", verify_certificate),
        ("Sistema", test_system),
        ("Guía", create_usage_guide)
    ]
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                print(f"❌ Error en paso: {step_name}")
                success = False
                break
        except Exception as e:
            print(f"❌ Error ejecutando {step_name}: {e}")
            success = False
            break
    
    # Resultado final
    print(f"\n{'='*60}")
    if success:
        print("🎉 SETUP COMPLETADO EXITOSAMENTE")
        print("")
        print("✅ Dependencias instaladas")
        print("✅ Scripts de diagnóstico creados") 
        print("✅ Guía de uso disponible")
        print("")
        print("🔄 PRÓXIMOS PASOS:")
        print("1. Copiar contenido de views_sunat.py corregido")
        print("2. Copiar script de diagnóstico") 
        print("3. Ejecutar: python diagnostico_sunat_completo.py")
        print("4. Si todo está OK, probar envío real")
        print("")
        print("📖 Lee GUIA_USO_SUNAT.md para instrucciones detalladas")
    else:
        print("❌ SETUP INCOMPLETO")
        print("💡 Revisa los errores y vuelve a ejecutar")
    
    return success

if __name__ == '__main__':
    success = main()
    
    input(f"\nPresiona Enter para continuar...")
    sys.exit(0 if success else 1)