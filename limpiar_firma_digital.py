#!/usr/bin/env python
"""
Script para limpiar completamente los comentarios de firma digital
Ubicación: limpiar_firma_digital.py (ARCHIVO NUEVO EN RAÍZ DEL PROYECTO)
Ejecutar: python limpiar_firma_digital.py
"""

import os
import re
from pathlib import Path
from datetime import datetime

def limpiar_comentarios_firma():
    """Limpia todos los comentarios de firma en templates y código"""
    
    print("🔥 LIMPIANDO COMENTARIOS DE FIRMA DIGITAL")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Archivos a limpiar
    archivos_limpiar = [
        'conversion/templates/ubl/factura.xml',
        'conversion/templates/ubl/boleta.xml',
        'conversion/templates/ubl/nota_credito.xml',
        'conversion/templates/ubl/nota_debito.xml'
    ]
    
    # Patrones de comentarios a eliminar
    patrones_eliminar = [
        r'<!-- Aquí va la firma digital[^>]*-->',
        r'<!-- Aquí irá la firma digital[^>]*-->',
        r'<!--[^>]*firma[^>]*-->',
        r'<!--[^>]*Firma[^>]*-->',
        r'<!--[^>]*FIRMA[^>]*-->',
        r'<!--[^>]*digital[^>]*-->',
        r'<!--[^>]*signature[^>]*-->',
        r'<!--\s*Aquí\s*va\s*la\s*firma\s*digital\s*-->',
        r'<!--\s*Aquí\s*irá\s*la\s*firma\s*digital\s*-->'
    ]
    
    archivos_procesados = 0
    
    for archivo in archivos_limpiar:
        if os.path.exists(archivo):
            print(f"🧹 Limpiando: {archivo}")
            
            # Leer archivo
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Aplicar limpieza
            contenido_original = contenido
            
            for patron in patrones_eliminar:
                contenido = re.sub(patron, '', contenido, flags=re.IGNORECASE)
            
            # Limpiar espacios extra
            contenido = re.sub(r'\n\s*\n', '\n', contenido)
            
            # Guardar si hubo cambios
            if contenido != contenido_original:
                with open(archivo, 'w', encoding='utf-8') as f:
                    f.write(contenido)
                print(f"✅ {archivo} limpiado")
                archivos_procesados += 1
            else:
                print(f"ℹ️ {archivo} ya estaba limpio")
        else:
            print(f"⚠️ No encontrado: {archivo}")
    
    print(f"\n🎯 RESULTADO: {archivos_procesados} archivos procesados")
    
    if archivos_procesados > 0:
        print("✅ Comentarios de firma eliminados exitosamente")
        print("🔄 Reinicia el servidor: python manage.py runserver")
    else:
        print("ℹ️ No se encontraron comentarios para eliminar")

def verificar_implementacion():
    """Verifica que los archivos estén correctamente implementados"""
    
    print("\n🔍 VERIFICANDO IMPLEMENTACIÓN...")
    print("-" * 30)
    
    verificaciones = []
    
    # 1. Verificar generador principal
    gen_file = 'conversion/generators/__init__.py'
    if os.path.exists(gen_file):
        with open(gen_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '_apply_real_digital_signature' in content:
            verificaciones.append(("Generador principal", True))
        else:
            verificaciones.append(("Generador principal", False))
    else:
        verificaciones.append(("Generador principal", False))
    
    # 2. Verificar templates
    templates = ['factura.xml', 'boleta.xml']
    for template in templates:
        template_file = f'conversion/templates/ubl/{template}'
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar que NO tenga comentarios de firma
            has_comments = '<!-- Aquí' in content or '<!-- Firma' in content
            verificaciones.append((f"Template {template}", not has_comments))
        else:
            verificaciones.append((f"Template {template}", False))
    
    # 3. Verificar XMLSigner
    signer_file = 'firma_digital/xml_signer.py'
    if os.path.exists(signer_file):
        with open(signer_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'sign_xml_document_clean' in content and '_remove_signature_comments' in content:
            verificaciones.append(("XMLSigner métodos", True))
        else:
            verificaciones.append(("XMLSigner métodos", False))
    else:
        verificaciones.append(("XMLSigner métodos", False))
    
    # Mostrar resultados
    exitosos = 0
    for nombre, resultado in verificaciones:
        estado = "✅" if resultado else "❌"
        print(f"{estado} {nombre}")
        if resultado:
            exitosos += 1
    
    print(f"\n📊 Verificaciones exitosas: {exitosos}/{len(verificaciones)}")
    
    return exitosos == len(verificaciones)

def generar_test_xml():
    """Genera un XML de prueba para verificar que no tenga comentarios"""
    
    print("\n🧪 GENERANDO XML DE PRUEBA...")
    
    try:
        import os
        import sys
        import django
        
        # Configurar Django
        sys.path.append('.')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
        django.setup()
        
        from documentos.models import Empresa, TipoDocumento, DocumentoElectronico
        from conversion.generators import generate_ubl_xml
        
        # Buscar empresa de prueba
        try:
            empresa = Empresa.objects.get(ruc='20103129061')
        except Empresa.DoesNotExist:
            print("❌ Empresa de prueba no encontrada")
            return False
        
        # Crear documento de prueba temporal
        documento = DocumentoElectronico(
            empresa=empresa,
            tipo_documento=TipoDocumento.objects.get(codigo='01'),
            serie='F001',
            numero=9999,  # Número temporal
            receptor_tipo_doc='6',
            receptor_numero_doc='20123456789',
            receptor_razon_social='CLIENTE TEST',
            fecha_emision='2025-07-14',
            moneda='PEN',
            subtotal=100,
            igv=18,
            total=118
        )
        
        # Generar XML
        xml_content = generate_ubl_xml(documento)
        
        # Verificar que NO tenga comentarios de firma
        if '<!-- Aquí' in xml_content or '<!-- Firma' in xml_content:
            print("❌ XML aún contiene comentarios de firma")
            print("💡 Verificar implementación de métodos")
            return False
        else:
            print("✅ XML generado SIN comentarios de firma")
            
            # Guardar XML de prueba
            with open('test_xml_limpio.xml', 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print("📄 XML guardado en: test_xml_limpio.xml")
            print("🔗 Probar en: https://probar-xml.nubefact.com/")
            return True
        
    except Exception as e:
        print(f"❌ Error generando XML de prueba: {e}")
        return False

def mostrar_instrucciones():
    """Muestra instrucciones de implementación"""
    
    print("\n📋 INSTRUCCIONES DE IMPLEMENTACIÓN")
    print("=" * 50)
    print()
    print("1. REEMPLAZAR ARCHIVOS COMPLETOS:")
    print("   ✏️ conversion/generators/__init__.py")
    print("   ✏️ conversion/templates/ubl/factura.xml")
    print("   ✏️ conversion/templates/ubl/boleta.xml")
    print()
    print("2. AGREGAR MÉTODOS A XMLSigner:")
    print("   ✏️ firma_digital/xml_signer.py")
    print("   📝 Agregar métodos: sign_xml_document_clean, _remove_signature_comments, etc.")
    print()
    print("3. MODIFICAR GenerarXMLView:")
    print("   ✏️ api_rest/views.py")
    print("   📝 Reemplazar método de firma con versión limpia")
    print()
    print("4. EJECUTAR LIMPIEZA:")
    print("   🧹 python limpiar_firma_digital.py")
    print()
    print("5. VERIFICAR RESULTADO:")
    print("   🔄 python manage.py runserver")
    print("   🌐 POST /api/generar-xml/")
    print("   🔗 Probar en: https://probar-xml.nubefact.com/")
    print()
    print("🎯 RESULTADO ESPERADO:")
    print("   - XML sin comentarios: <!-- Aquí va la firma digital -->")
    print("   - Firma digital real o simulada incluida")
    print("   - Validación exitosa en NUBEFACT")

def main():
    """Función principal"""
    
    print("🔥 SCRIPT DE LIMPIEZA DE FIRMA DIGITAL")
    print("=" * 60)
    
    # 1. Limpiar comentarios existentes
    limpiar_comentarios_firma()
    
    # 2. Verificar implementación
    implementacion_ok = verificar_implementacion()
    
    # 3. Generar XML de prueba
    if implementacion_ok:
        test_ok = generar_test_xml()
        
        if test_ok:
            print("\n🎉 ¡IMPLEMENTACIÓN EXITOSA!")
            print("✅ XML generado sin comentarios de firma")
            print("🚀 Listo para probar en NUBEFACT")
        else:
            print("\n⚠️ IMPLEMENTACIÓN INCOMPLETA")
            mostrar_instrucciones()
    else:
        print("\n❌ IMPLEMENTACIÓN FALTANTE")
        mostrar_instrucciones()
    
    print("\n" + "=" * 60)
    print("Script completado")

if __name__ == '__main__':
    main()