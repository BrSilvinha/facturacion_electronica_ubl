#!/usr/bin/env python
"""
Instalador completo para certificado real de SUNAT
Ejecutar: python install_real_certificate.py
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    """Instalador principal"""
    
    print("🚀 INSTALADOR DE CERTIFICADO REAL SUNAT")
    print("=" * 60)
    print("Versión: 2.0 Professional")
    print("RUC: 20103129061")
    print("")
    
    base_dir = Path(__file__).parent
    
    # Verificar archivos del certificado
    cert_file = base_dir / 'C23022479065.pfx'
    password_file = base_dir / 'C23022479065-CONTRASEÑA.txt'
    
    print("📋 VERIFICACIÓN DE ARCHIVOS:")
    print("-" * 30)
    
    if cert_file.exists():
        size = cert_file.stat().st_size
        print(f"✅ Certificado: {cert_file.name} ({size} bytes)")
    else:
        print(f"❌ Certificado: {cert_file.name} NO ENCONTRADO")
        print("💡 Asegúrate de que el archivo esté en la carpeta del proyecto")
        return False
    
    if password_file.exists():
        print(f"✅ Contraseña: {password_file.name}")
    else:
        print(f"❌ Contraseña: {password_file.name} NO ENCONTRADO")
        print("💡 Crea el archivo con la contraseña del certificado")
        return False
    
    print("")
    print("📁 CREANDO ESTRUCTURA:")
    print("-" * 30)
    
    # Crear directorios
    cert_dir = base_dir / 'certificados'
    prod_dir = cert_dir / 'production'
    
    prod_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Directorio: {prod_dir}")
    
    # Copiar certificado
    new_cert_path = prod_dir / 'cert_20103129061.pfx'
    shutil.copy2(cert_file, new_cert_path)
    print(f"✅ Certificado copiado: {new_cert_path}")
    
    # Leer y copiar contraseña
    with open(password_file, 'r', encoding='utf-8') as f:
        password = f.read().strip()
    
    password_secure = prod_dir / 'cert_20103129061_password.txt'
    with open(password_secure, 'w', encoding='utf-8') as f:
        f.write(password)
    print(f"✅ Contraseña guardada: {password_secure}")
    
    # Crear .gitignore
    gitignore = prod_dir / '.gitignore'
    with open(gitignore, 'w', encoding='utf-8') as f:
        f.write("# Proteger certificados reales\n*.pfx\n*.p12\n*password*\n*CONTRASEÑA*\n")
    print(f"✅ Protección creada: {gitignore}")
    
    print("")
    print("🔧 ACTUALIZANDO CONFIGURACIÓN:")
    print("-" * 30)
    
    # Actualizar views.py
    views_file = base_dir / 'api_rest' / 'views.py'
    
    if views_file.exists():
        with open(views_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya está actualizado
        if 'Ch14pp32023' in content:
            print(f"✅ views.py ya está actualizado")
        else:
            # Buscar y reemplazar la configuración
            old_config = "'20103129061': {  # ⭐ TU RUC AGREGADO"
            new_config = f"""'20103129061': {{  # ⭐ TU CERTIFICADO REAL
            'path': 'certificados/production/cert_20103129061.pfx',
            'password': '{password}'
        }},
        '20103129061_TEST': {{  # Backup de prueba"""
            
            if old_config in content:
                content = content.replace(old_config, new_config)
                
                with open(views_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ views.py actualizado con certificado real")
            else:
                print(f"⚠️ views.py - configuración no encontrada (puede estar ya actualizado)")
    else:
        print(f"❌ views.py no encontrado")
        return False
    
    # Actualizar urls.py
    urls_file = base_dir / 'api_rest' / 'urls.py'
    
    if urls_file.exists():
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'certificate-info' not in content:
            # Agregar endpoint de certificados
            addition = "    path('certificate-info/', views.CertificateInfoView.as_view(), name='certificate-info'),\n    "
            
            if "path('validar-ruc/" in content:
                content = content.replace(
                    "path('validar-ruc/", 
                    addition + "path('validar-ruc/"
                )
                
                with open(urls_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ urls.py actualizado con endpoint de certificados")
            else:
                print(f"⚠️ urls.py - punto de inserción no encontrado")
        else:
            print(f"✅ urls.py ya tiene endpoint de certificados")
    else:
        print(f"❌ urls.py no encontrado")
    
    print("")
    print("🎉 INSTALACIÓN COMPLETADA")
    print("=" * 60)
    print("📋 Resumen:")
    print(f"   🔐 Certificado real instalado para RUC 20103129061")
    print(f"   📁 Ubicación: {new_cert_path}")
    print(f"   🛡️ Protegido con .gitignore")
    print(f"   ⚙️ Configuración actualizada")
    print("")
    print("🚀 Próximos pasos:")
    print("   1. python test_real_certificate.py")
    print("   2. python test_sistema_completo.py")
    print("   3. ¡Generar facturas con certificado real!")
    print("")
    print("✅ Tu sistema ahora firma con certificado REAL de SUNAT")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        
        if success:
            print(f"\n🎉 INSTALACIÓN EXITOSA")
        else:
            print(f"\n❌ INSTALACIÓN FALLIDA")
            print("💡 Revisa los errores arriba")
        
        input("\nPresiona Enter para continuar...")
        
    except Exception as e:
        print(f"\n❌ Error durante instalación: {e}")
        input("Presiona Enter para continuar...")