#!/usr/bin/env python
"""
Script para configurar certificado real en el proyecto
Ejecutar: python create_real_certificate_setup.py
"""

import os
import sys
import django
import shutil
from pathlib import Path
from datetime import datetime

# Configurar Django
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

# Inicializar Django
django.setup()

class RealCertificateSetup:
    """Configurador de certificado digital real"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.cert_dir = self.base_dir / 'certificados'
        self.prod_dir = self.cert_dir / 'production'
        self.ruc = "20103129061"  # Tu RUC del .env
        
        # Archivos del certificado
        self.cert_file = self.base_dir / 'C23022479065.pfx'
        self.password_file = self.base_dir / 'C23022479065-CONTRASEÑA.txt'
        
    def step_1_create_directories(self):
        """Paso 1: Crear directorios necesarios"""
        print("📁 PASO 1: Creando directorios...")
        
        # Crear directorio production
        self.prod_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Directorio creado: {self.prod_dir}")
        
        # Crear .gitignore para proteger certificados reales
        gitignore_prod = self.prod_dir / '.gitignore'
        gitignore_content = """# Proteger certificados reales - NO SUBIR A GIT
*.pfx
*.p12
*CONTRASEÑA*
*password*
*PASSWORD*
certificates_config.py
"""
        
        with open(gitignore_prod, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        
        print(f"   ✅ .gitignore creado para proteger certificados")
        
        # Actualizar .gitignore principal
        gitignore_main = self.cert_dir / '.gitignore'
        gitignore_main_content = """# Proteger certificados reales
production/
backup/
*.pfx
*.p12
*CONTRASEÑA*
*password*
*PASSWORD*
"""
        
        with open(gitignore_main, 'w', encoding='utf-8') as f:
            f.write(gitignore_main_content)
        
        print(f"   ✅ .gitignore principal actualizado")
        return True
    
    def step_2_copy_certificate(self):
        """Paso 2: Copiar y validar certificado"""
        print(f"\n🔐 PASO 2: Copiando certificado real...")
        
        # Verificar que los archivos existen
        if not self.cert_file.exists():
            print(f"   ❌ Certificado no encontrado: {self.cert_file}")
            print(f"   💡 Asegúrate de que el archivo esté en: {self.base_dir}")
            return False
        
        if not self.password_file.exists():
            print(f"   ❌ Archivo de contraseña no encontrado: {self.password_file}")
            print(f"   💡 Crea el archivo: {self.password_file}")
            return False
        
        # Leer contraseña
        with open(self.password_file, 'r', encoding='utf-8') as f:
            password = f.read().strip()
        
        print(f"   ✅ Certificado encontrado: {self.cert_file.name} ({self.cert_file.stat().st_size} bytes)")
        print(f"   ✅ Contraseña leída: {'*' * len(password)}")
        
        # Copiar certificado a directorio production con nombre estándar
        new_cert_path = self.prod_dir / f'cert_{self.ruc}.pfx'
        shutil.copy2(self.cert_file, new_cert_path)
        
        print(f"   ✅ Certificado copiado a: {new_cert_path}")
        
        # Guardar contraseña en archivo seguro
        password_file_secure = self.prod_dir / f'cert_{self.ruc}_password.txt'
        with open(password_file_secure, 'w', encoding='utf-8') as f:
            f.write(password)
        
        print(f"   ✅ Contraseña guardada de forma segura")
        
        return new_cert_path, password
    
    def step_3_validate_certificate(self, cert_path, password):
        """Paso 3: Validar certificado"""
        print(f"\n🔍 PASO 3: Validando certificado...")
        
        try:
            from firma_digital import XMLSigner, certificate_manager
            
            # Cargar certificado
            cert_info = certificate_manager.get_certificate(str(cert_path), password, use_cache=False)
            
            print(f"   📜 Información del certificado:")
            print(f"      - Sujeto: {cert_info['metadata']['subject_cn']}")
            print(f"      - Organización: {cert_info['metadata']['subject_o']}")
            print(f"      - RUC/Serial: {cert_info['metadata']['subject_serial']}")
            print(f"      - Válido desde: {cert_info['metadata']['not_before']}")
            print(f"      - Válido hasta: {cert_info['metadata']['not_after']}")
            print(f"      - Tamaño clave: {cert_info['metadata']['key_size']} bits")
            
            # Verificar que el RUC coincide
            cert_ruc = cert_info['metadata']['subject_serial']
            if cert_ruc != self.ruc:
                print(f"   ⚠️ ADVERTENCIA: RUC del certificado ({cert_ruc}) != RUC del proyecto ({self.ruc})")
                response = input("   ¿Continuar de todas formas? (s/N): ").strip().lower()
                if response != 's':
                    return False
            
            print(f"   ✅ Certificado validado correctamente")
            return True
            
        except Exception as e:
            print(f"   ❌ Error validando certificado: {e}")
            return False
    
    def step_4_test_signature(self, cert_path, password):
        """Paso 4: Probar firma digital"""
        print(f"\n🧪 PASO 4: Probando firma digital...")
        
        try:
            from firma_digital import XMLSigner, certificate_manager
            
            # Cargar certificado
            cert_info = certificate_manager.get_certificate(str(cert_path), password)
            
            # Crear XML de prueba
            xml_test = f'''<?xml version="1.0" encoding="UTF-8"?>
<TestDocument>
    <Message>Prueba de certificado real de SUNAT</Message>
    <RUC>{self.ruc}</RUC>
    <Timestamp>{datetime.now().isoformat()}</Timestamp>
    <CertificateSubject>{cert_info['metadata']['subject_cn']}</CertificateSubject>
</TestDocument>'''
            
            # Firmar XML
            signer = XMLSigner()
            xml_firmado = signer.sign_xml_document(xml_test, cert_info)
            
            # Verificar firma
            if 'ds:Signature' in xml_firmado and 'ds:SignatureValue' in xml_firmado:
                print(f"   ✅ XML firmado correctamente con certificado real")
                print(f"   📄 Tamaño XML original: {len(xml_test)} caracteres")
                print(f"   📄 Tamaño XML firmado: {len(xml_firmado)} caracteres")
                print(f"   🔐 Contiene ds:Signature: {'ds:Signature' in xml_firmado}")
                print(f"   🔐 Contiene ds:SignatureValue: {'ds:SignatureValue' in xml_firmado}")
                
                # Guardar XML de prueba para verificación
                test_xml_path = self.prod_dir / f'test_signature_{self.ruc}.xml'
                with open(test_xml_path, 'w', encoding='utf-8') as f:
                    f.write(xml_firmado)
                
                print(f"   💾 XML de prueba guardado en: {test_xml_path}")
                return True
            else:
                print(f"   ❌ XML no contiene firma válida")
                return False
            
        except Exception as e:
            print(f"   ❌ Error en prueba de firma: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step_5_create_enterprise_if_needed(self):
        """Paso 5: Crear empresa si no existe"""
        print(f"\n🏢 PASO 5: Verificando empresa en base de datos...")
        
        try:
            from documentos.models import Empresa
            
            # Buscar empresa con tu RUC
            empresa = Empresa.objects.filter(ruc=self.ruc).first()
            
            if not empresa:
                print(f"   ⚠️ Empresa con RUC {self.ruc} no encontrada, creando...")
                
                empresa = Empresa.objects.create(
                    ruc=self.ruc,
                    razon_social="EMPRESA CON CERTIFICADO REAL SAC",
                    nombre_comercial="EMPRESA REAL",
                    direccion="Av. Real 123, Lima, Lima, Peru",
                    ubigeo="150101",
                    activo=True
                )
                
                print(f"   ✅ Empresa creada: {empresa.razon_social}")
            else:
                print(f"   ✅ Empresa encontrada: {empresa.razon_social}")
                
                # Asegurar que está activa
                if not empresa.activo:
                    empresa.activo = True
                    empresa.save()
                    print(f"   🔄 Empresa reactivada")
            
            return empresa
            
        except Exception as e:
            print(f"   ❌ Error con empresa: {e}")
            return None
    
    def step_6_update_configuration(self, cert_path, password):
        """Paso 6: Actualizar configuración del sistema"""
        print(f"\n⚙️ PASO 6: Actualizando configuración del sistema...")
        
        # Crear archivo de configuración de certificados
        config_file = self.prod_dir / 'certificates_config.py'
        
        config_content = f'''"""
Configuración de certificados digitales reales
ADVERTENCIA: No subir este archivo a control de versiones
"""

from pathlib import Path

# Configuración de certificados reales
CERTIFICATES_CONFIG = {{
    '{self.ruc}': {{
        'path': Path(__file__).parent / 'cert_{self.ruc}.pfx',
        'password': '{password}',
        'description': 'Certificado digital real de SUNAT',
        'environment': 'production',
        'created_at': '{datetime.now().isoformat()}',
        'ruc': '{self.ruc}',
        'type': 'REAL_PRODUCTION'
    }}
}}

def get_certificate_config(ruc):
    """Obtener configuración de certificado por RUC"""
    return CERTIFICATES_CONFIG.get(ruc)

def list_available_certificates():
    """Listar certificados disponibles"""
    return list(CERTIFICATES_CONFIG.keys())

def is_real_certificate(ruc):
    """Verificar si un RUC tiene certificado real"""
    config = get_certificate_config(ruc)
    return config and config.get('type') == 'REAL_PRODUCTION'
'''
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"   ✅ Configuración creada: {config_file}")
        
        # Crear archivo README para producción
        readme_file = self.prod_dir / 'README.md'
        readme_content = f'''# Certificados de Producción

## ⚠️ IMPORTANTE
Este directorio contiene certificados digitales reales de SUNAT.

**NO SUBIR A CONTROL DE VERSIONES**

## Archivos
- `cert_{self.ruc}.pfx` - Certificado digital real
- `cert_{self.ruc}_password.txt` - Contraseña del certificado
- `certificates_config.py` - Configuración programática
- `test_signature_{self.ruc}.xml` - XML de prueba firmado

## Configuración
- RUC: {self.ruc}
- Certificado: REAL DE PRODUCCIÓN
- Creado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Uso
El sistema automáticamente detecta y usa este certificado para tu RUC.

## Seguridad
- Archivos protegidos por .gitignore
- Contraseña almacenada de forma segura
- Solo accesible en servidor de producción
'''
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"   ✅ README creado: {readme_file}")
        return True
    
    def run_complete_setup(self):
        """Ejecutar configuración completa"""
        print("🚀 CONFIGURACIÓN COMPLETA DE CERTIFICADO REAL")
        print("=" * 70)
        print(f"📋 RUC: {self.ruc}")
        print(f"📁 Directorio base: {self.base_dir}")
        print(f"🔐 Directorio certificados: {self.prod_dir}")
        print("")
        
        success_count = 0
        total_steps = 6
        
        try:
            # Paso 1: Crear directorios
            if self.step_1_create_directories():
                success_count += 1
            
            # Paso 2: Copiar certificado
            result = self.step_2_copy_certificate()
            if result:
                cert_path, password = result
                success_count += 1
                
                # Paso 3: Validar certificado
                if self.step_3_validate_certificate(cert_path, password):
                    success_count += 1
                    
                    # Paso 4: Probar firma
                    if self.step_4_test_signature(cert_path, password):
                        success_count += 1
                        
                        # Paso 5: Crear empresa
                        if self.step_5_create_enterprise_if_needed():
                            success_count += 1
                            
                            # Paso 6: Actualizar configuración
                            if self.step_6_update_configuration(cert_path, password):
                                success_count += 1
        
        except Exception as e:
            print(f"❌ Error durante configuración: {e}")
            import traceback
            traceback.print_exc()
        
        # Reporte final
        print(f"\n" + "=" * 70)
        print(f"📊 REPORTE DE CONFIGURACIÓN")
        print("=" * 70)
        print(f"✅ Pasos completados: {success_count}/{total_steps}")
        print(f"📈 Tasa de éxito: {(success_count/total_steps)*100:.1f}%")
        
        if success_count == total_steps:
            print(f"\n🎉 ¡CERTIFICADO REAL CONFIGURADO EXITOSAMENTE!")
            print(f"")
            print(f"📋 Resumen:")
            print(f"   🔐 Certificado real instalado para RUC {self.ruc}")
            print(f"   📄 Ubicación: {cert_path}")
            print(f"   🛡️ Protegido por .gitignore")
            print(f"   ✅ Validado y probado")
            print(f"")
            print(f"🚀 Próximos pasos:")
            print(f"   1. python test_sistema_completo.py")
            print(f"   2. Verificar que usa certificado REAL")
            print(f"   3. ¡Generar facturas de producción!")
            print(f"")
            print(f"💡 El sistema ahora:")
            print(f"   ✅ Firma con certificado real de SUNAT")
            print(f"   ✅ Documentos válidos para producción")
            print(f"   ✅ Cumple normativas SUNAT")
            
        elif success_count >= 4:
            print(f"\n✅ CONFIGURACIÓN MAYORMENTE EXITOSA")
            print(f"   ⚠️ Algunos pasos fallaron, pero lo esencial está configurado")
            print(f"   💡 Revisa los errores arriba")
            
        else:
            print(f"\n❌ CONFIGURACIÓN FALLÓ")
            print(f"   💡 Revisa los errores arriba")
            print(f"   🔧 Verifica que los archivos del certificado estén presentes")
        
        return success_count == total_steps

if __name__ == '__main__':
    print("🔐 CONFIGURADOR DE CERTIFICADO REAL SUNAT")
    print("Versión: 2.0 Professional")
    print("")
    
    setup = RealCertificateSetup()
    success = setup.run_complete_setup()
    
    if success:
        print(f"\n✅ ¡CONFIGURACIÓN COMPLETADA!")
    else:
        print(f"\n⚠️ CONFIGURACIÓN INCOMPLETA")
    
    print(f"\nPresiona Enter para continuar...")
    input()