#!/usr/bin/env python
# verificar_escenarios.py - SCRIPT DE VERIFICACIÓN COMPLETO
"""
Script para verificar que todo esté configurado correctamente para los escenarios de prueba
Ejecutar: python verificar_escenarios.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

def verificar_archivos():
    """Verifica que todos los archivos necesarios existan"""
    print("🔍 Verificando archivos necesarios...")
    
    archivos_requeridos = [
        'api_rest/views_test_scenarios.py',
        'conversion/generators/boleta_generator.py',
        'conversion/templates/ubl/boleta.xml',
        'documentos/management/commands/crear_datos_prueba.py',
        'certificados/production/C23022479065.pfx',
        'facturacion_electronica/C23022479065-CONTRASEÑA.txt'
    ]
    
    archivos_faltantes = []
    archivos_existentes = []
    
    for archivo in archivos_requeridos:
        if os.path.exists(archivo):
            archivos_existentes.append(archivo)
            print(f"✅ {archivo}")
        else:
            archivos_faltantes.append(archivo)
            print(f"❌ {archivo}")
    
    return len(archivos_faltantes) == 0, archivos_faltantes

def verificar_base_datos():
    """Verifica configuración de base de datos"""
    print("\n🗄️ Verificando base de datos...")
    
    try:
        from documentos.models import TipoDocumento, Empresa
        
        # Verificar tipos de documento
        tipos_count = TipoDocumento.objects.count()
        print(f"✅ Tipos de documento: {tipos_count}")
        
        # Verificar empresa de prueba
        try:
            empresa = Empresa.objects.get(ruc='20103129061')
            print(f"✅ Empresa de prueba: {empresa.razon_social}")
            return True
        except Empresa.DoesNotExist:
            print("❌ Empresa de prueba no encontrada")
            print("💡 Ejecuta: python manage.py crear_datos_prueba")
            return False
            
    except Exception as e:
        print(f"❌ Error de base de datos: {e}")
        print("💡 Ejecuta: python manage.py migrate")
        return False

def verificar_certificado():
    """Verifica certificado digital"""
    print("\n🔐 Verificando certificado digital...")
    
    cert_path = 'certificados/production/C23022479065.pfx'
    password_path = 'facturacion_electronica/C23022479065-CONTRASEÑA.txt'
    
    if not os.path.exists(cert_path):
        print(f"❌ Certificado no encontrado: {cert_path}")
        return False
    
    if not os.path.exists(password_path):
        print(f"❌ Archivo de contraseña no encontrado: {password_path}")
        return False
    
    try:
        # Leer contraseña
        with open(password_path, 'r') as f:
            password = f.read().strip()
        
        # Verificar que el certificado se puede cargar
        from firma_digital import certificate_manager
        cert_info = certificate_manager.get_certificate(cert_path, password)
        
        print(f"✅ Certificado válido")
        print(f"   Sujeto: {cert_info['metadata']['subject_cn']}")
        print(f"   Válido hasta: {cert_info['metadata']['not_after']}")
        return True
        
    except Exception as e:
        print(f"❌ Error cargando certificado: {e}")
        return False

def verificar_endpoints():
    """Verifica que los endpoints estén disponibles"""
    print("\n🌐 Verificando endpoints...")
    
    try:
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        
        # Verificar endpoint de menú
        try:
            response = client.get('/api/test/')
            if response.status_code == 200:
                print("✅ Endpoint de menú funcionando")
                return True
            else:
                print(f"❌ Endpoint de menú error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error endpoint de menú: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando endpoints: {e}")
        return False

def verificar_dependencias():
    """Verifica dependencias Python"""
    print("\n📦 Verificando dependencias...")
    
    dependencias = [
        ('lxml', 'lxml'),
        ('cryptography', 'cryptography'),
        ('signxml', 'signxml'),
        ('jinja2', 'Jinja2'),
        ('django', 'Django'),
        ('djangorestframework', 'rest_framework')
    ]
    
    dependencias_faltantes = []
    
    for modulo, nombre in dependencias:
        try:
            __import__(modulo)
            print(f"✅ {nombre}")
        except ImportError:
            dependencias_faltantes.append(nombre)
            print(f"❌ {nombre}")
    
    if dependencias_faltantes:
        print(f"\n💡 Instalar dependencias faltantes:")
        print(f"pip install {' '.join(dependencias_faltantes)}")
        return False
    
    return True

def main():
    print("🧪 VERIFICADOR DE ESCENARIOS SUNAT")
    print("=" * 50)
    
    verificaciones = [
        ("Archivos necesarios", verificar_archivos),
        ("Dependencias Python", verificar_dependencias),
        ("Base de datos", verificar_base_datos),
        ("Certificado digital", verificar_certificado),
        ("Endpoints API", verificar_endpoints)
    ]
    
    resultados = []
    
    for nombre, funcion in verificaciones:
        try:
            if callable(funcion):
                resultado = funcion()
            else:
                resultado = funcion
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"❌ Error en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)
    
    exitosos = 0
    for nombre, resultado in resultados:
        if isinstance(resultado, tuple):
            resultado, detalles = resultado
        
        if resultado:
            print(f"✅ {nombre}")
            exitosos += 1
        else:
            print(f"❌ {nombre}")
    
    print(f"\n🎯 RESULTADO: {exitosos}/{len(verificaciones)} verificaciones exitosas")
    
    if exitosos == len(verificaciones):
        print("\n🎉 ¡TODO LISTO PARA PROBAR!")
        print("🚀 Ejecuta: python manage.py runserver")
        print("🌐 Ve a: http://localhost:8000/api/test/")
        print("📋 Endpoints disponibles:")
        print("   POST /api/test/scenario-1-boleta-completa/")
        print("   POST /api/test/scenario-2-factura-gravada/")
        print("   POST /api/test/scenario-3-factura-exonerada/")
        print("   POST /api/test/scenario-4-factura-mixta/")
        print("   POST /api/test/scenario-5-factura-exportacion/")
        print("\n🔗 Para probar XMLs: https://probar-xml.nubefact.com/")
    else:
        print("\n⚠️  NECESITAS CORREGIR LOS ERRORES ANTES DE CONTINUAR")
        print("💡 Revisa los mensajes de error arriba")
    
    return exitosos == len(verificaciones)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)