#!/usr/bin/env python
"""
Script para verificar la configuración del certificado real de SUNAT
Ejecutar: python verificar_certificado.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Agregar directorio del proyecto
sys.path.append(str(Path(__file__).parent))

def verificar_certificado_real():
    """Verifica la configuración del certificado real"""
    
    print("🔐 VERIFICACIÓN DEL CERTIFICADO REAL DE SUNAT")
    print("=" * 60)
    
    # 1. Verificar archivo .env
    env_file = Path('.env')
    if env_file.exists():
        print("✅ Archivo .env encontrado")
        try:
            # Intentar diferentes codificaciones
            encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(env_file, 'r', encoding=encoding) as f:
                        content = f.read()
                        print(f"   📝 Leído con codificación: {encoding}")
                        break
                except UnicodeDecodeError:
                    continue
            
            if content:
                if 'SUNAT_RUC=20103129061' in content:
                    print("✅ RUC real configurado: 20103129061")
                else:
                    print("❌ RUC real no encontrado en .env")
                    # Mostrar líneas que contienen SUNAT_RUC
                    lines = [line.strip() for line in content.split('\n') if 'SUNAT_RUC' in line]
                    if lines:
                        print(f"   💡 RUC encontrado: {lines[0]}")
            else:
                print("❌ No se pudo leer el archivo .env con ninguna codificación")
                
        except Exception as e:
            print(f"❌ Error leyendo .env: {e}")
    else:
        print("❌ Archivo .env no encontrado")
    
    # 2. Verificar certificado real
    cert_path = Path('certificados/production/cert_20103129061.pfx')
    if cert_path.exists():
        print(f"✅ Certificado real encontrado: {cert_path}")
        size_mb = cert_path.stat().st_size / 1024 / 1024
        print(f"   📏 Tamaño: {size_mb:.2f} MB")
    else:
        print(f"❌ Certificado real NO encontrado en: {cert_path}")
        print("   💡 Asegúrate de que el archivo esté en la ubicación correcta")
    
    # 3. Verificar archivo de contraseña
    password_files = [
        Path('C23022479065-CONTRASEÑA.txt'),
        Path('facturacion_electronica/C23022479065-CONTRASEÑA.txt'),
        Path('certificados/production/C23022479065-CONTRASEÑA.txt')
    ]
    
    password_found = False
    for password_file in password_files:
        if password_file.exists():
            print(f"✅ Archivo de contraseña encontrado: {password_file}")
            try:
                # Intentar diferentes codificaciones
                encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
                for encoding in encodings:
                    try:
                        with open(password_file, 'r', encoding=encoding) as f:
                            password = f.read().strip()
                            print(f"   🔑 Contraseña configurada: {password}")
                            password_found = True
                            break
                    except UnicodeDecodeError:
                        continue
                        
                if password_found:
                    break
                    
            except Exception as e:
                print(f"   ❌ Error leyendo contraseña: {e}")
    
    if not password_found:
        print("❌ Archivo de contraseña no encontrado en ubicaciones esperadas")
        print("   💡 Ubicaciones verificadas:")
        for pf in password_files:
            print(f"      - {pf}")
    
    # 4. Verificar estructura de directorios
    print("\n📁 ESTRUCTURA DE CERTIFICADOS:")
    cert_dirs = [
        'certificados/',
        'certificados/production/',
        'certificados/test/',
    ]
    
    for dir_path in cert_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ {dir_path}")
            # Listar archivos
            files = list(path.glob('*'))
            for file in files[:5]:  # Mostrar máximo 5 archivos
                print(f"   📄 {file.name}")
        else:
            print(f"❌ {dir_path}")
    
    # 5. Verificar configuración Django
    try:
        import django
        from django.conf import settings
        
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
        django.setup()
        
        sunat_config = settings.SUNAT_CONFIG
        print(f"\n⚙️ CONFIGURACIÓN SUNAT:")
        print(f"   🌐 Ambiente: {sunat_config.get('ENVIRONMENT')}")
        print(f"   🏢 RUC: {sunat_config.get('RUC')}")
        print(f"   👤 Usuario Beta: {sunat_config.get('BETA_USER')}")
        
        # Verificar configuración de firma
        sig_config = settings.DIGITAL_SIGNATURE_CONFIG
        print(f"\n✍️ CONFIGURACIÓN FIRMA DIGITAL:")
        print(f"   🔐 Directorio producción: {sig_config.get('CERT_PROD_DIR')}")
        print(f"   ⏱️ Timeout: {sig_config.get('SIGNATURE_TIMEOUT')}s")
        
    except Exception as e:
        print(f"❌ Error cargando configuración Django: {e}")
    
    print("\n" + "=" * 60)
    print("🚀 LISTO PARA PROBAR FIRMA REAL")

def test_certificado_carga():
    """Prueba cargar el certificado real"""
    
    print("\n🧪 PRUEBA DE CARGA DE CERTIFICADO")
    print("-" * 40)
    
    try:
        # Configurar Django
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
        django.setup()
        
        from firma_digital import XMLSigner, certificate_manager
        
        # Intentar cargar certificado real
        cert_path = 'certificados/production/cert_20103129061.pfx'
        password = 'Ch14pp32023'
        
        print(f"🔄 Cargando certificado: {cert_path}")
        
        cert_info = certificate_manager.get_certificate(cert_path, password)
        
        print("✅ Certificado cargado exitosamente!")
        print(f"   👤 Sujeto: {cert_info['metadata']['subject_cn']}")
        print(f"   🆔 RUC/Serial: {cert_info['metadata']['subject_serial']}")
        print(f"   📅 Válido hasta: {cert_info['metadata']['not_after']}")
        print(f"   🔐 Tamaño clave: {cert_info['metadata']['key_size']} bits")
        print(f"   🏷️ Algoritmo: {cert_info['metadata']['signature_algorithm']}")
        
        # Verificar que es un certificado real
        if 'production' in cert_path:
            print("🎯 CERTIFICADO REAL DE PRODUCCIÓN DETECTADO")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cargando certificado: {e}")
        return False

if __name__ == '__main__':
    # Verificar configuración
    verificar_certificado_real()
    
    # Probar carga de certificado
    if test_certificado_carga():
        print("\n🎉 ¡TODO LISTO PARA FIRMA REAL!")
        print("\n📋 SIGUIENTE PASO:")
        print("   1. Ejecutar servidor: python manage.py runserver")
        print("   2. Ir a: http://localhost:8000")
        print("   3. Crear factura con RUC 20103129061")
        print("   4. Generar XML - usará certificado REAL")
    else:
        print("\n⚠️ HAY PROBLEMAS CON EL CERTIFICADO")
        print("   Revisa la configuración antes de continuar")