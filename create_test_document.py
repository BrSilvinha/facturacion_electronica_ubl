#!/usr/bin/env python
"""
Crear documento de prueba para corregir error 0160
Archivo: create_test_document.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

import django
django.setup()

from documentos.models import (
    Empresa, TipoDocumento, DocumentoElectronico, 
    DocumentoLinea
)
from conversion.generators import generate_ubl_xml
from conversion.utils.calculations import TributaryCalculator
from firma_digital import XMLSigner, certificate_manager

def create_test_document():
    """Crea documento de prueba completo"""
    
    print("🚀 CREANDO DOCUMENTO DE PRUEBA PARA ERROR 0160")
    print("=" * 60)
    
    try:
        # 1. Verificar/Crear empresa
        print("📋 PASO 1: Verificando empresa...")
        empresa, created = Empresa.objects.get_or_create(
            ruc='20103129061',
            defaults={
                'razon_social': 'COMERCIAL LAVAGNA SAC',
                'nombre_comercial': 'COMERCIAL LAVAGNA',
                'direccion': 'AV. PRUEBA 123, LIMA, LIMA',
                'ubigeo': '150101',
                'activo': True
            }
        )
        
        if created:
            print(f"✅ Empresa creada: {empresa.razon_social}")
        else:
            print(f"✅ Empresa encontrada: {empresa.razon_social}")
        
        # 2. Verificar tipo de documento
        print("📋 PASO 2: Verificando tipo de documento...")
        tipo_doc, created = TipoDocumento.objects.get_or_create(
            codigo='01',
            defaults={
                'descripcion': 'Factura',
                'activo': True
            }
        )
        
        if created:
            print(f"✅ Tipo documento creado: {tipo_doc.descripcion}")
        else:
            print(f"✅ Tipo documento encontrado: {tipo_doc.descripcion}")
        
        # 3. Crear documento base
        print("📋 PASO 3: Creando documento...")
        
        # Buscar próximo número
        ultimo_numero = DocumentoElectronico.objects.filter(
            empresa=empresa,
            tipo_documento=tipo_doc,
            serie='F001'
        ).order_by('-numero').first()
        
        nuevo_numero = (ultimo_numero.numero + 1) if ultimo_numero else 1
        
        documento = DocumentoElectronico.objects.create(
            empresa=empresa,
            tipo_documento=tipo_doc,
            serie='F001',
            numero=nuevo_numero,
            receptor_tipo_doc='6',
            receptor_numero_doc='20987654321',
            receptor_razon_social='CLIENTE PRUEBA SAC',
            receptor_direccion='AV. CLIENTE 456, LIMA',
            fecha_emision=date.today(),
            moneda='PEN',
            estado='PENDIENTE'
        )
        
        print(f"✅ Documento creado: {documento.get_numero_completo()}")
        print(f"   📄 ID: {documento.id}")
        
        # 4. Crear líneas del documento
        print("📋 PASO 4: Creando líneas...")
        
        items_data = [
            {
                'descripcion': 'Producto de Prueba 1',
                'cantidad': Decimal('2.000'),
                'valor_unitario': Decimal('50.00'),
                'codigo_producto': 'PROD001',
                'unidad_medida': 'NIU',
                'afectacion_igv': '10'
            },
            {
                'descripcion': 'Servicio de Prueba 2',
                'cantidad': Decimal('1.000'),
                'valor_unitario': Decimal('100.00'),
                'codigo_producto': 'SERV001',
                'unidad_medida': 'ZZ',
                'afectacion_igv': '10'
            }
        ]
        
        total_documento = Decimal('0.00')
        igv_total = Decimal('0.00')
        
        for i, item_data in enumerate(items_data, 1):
            # Calcular totales del item
            calculo = TributaryCalculator.calculate_line_totals(
                cantidad=item_data['cantidad'],
                valor_unitario=item_data['valor_unitario'],
                afectacion_igv=item_data['afectacion_igv']
            )
            
            # Crear línea
            DocumentoLinea.objects.create(
                documento=documento,
                numero_linea=i,
                codigo_producto=item_data['codigo_producto'],
                descripcion=item_data['descripcion'],
                unidad_medida=item_data['unidad_medida'],
                cantidad=item_data['cantidad'],
                valor_unitario=item_data['valor_unitario'],
                valor_venta=calculo['valor_venta'],
                afectacion_igv=item_data['afectacion_igv'],
                igv_linea=calculo['igv_monto'],
                isc_linea=Decimal('0.00'),
                icbper_linea=Decimal('0.00')
            )
            
            total_documento += calculo['precio_venta']
            igv_total += calculo['igv_monto']
            
            print(f"   ✅ Línea {i}: {item_data['descripcion']} - S/ {calculo['precio_venta']}")
        
        # 5. Actualizar totales del documento
        print("📋 PASO 5: Calculando totales...")
        
        documento.subtotal = total_documento - igv_total
        documento.igv = igv_total
        documento.total = total_documento
        documento.save()
        
        print(f"   💰 Subtotal: S/ {documento.subtotal}")
        print(f"   🏛️ IGV: S/ {documento.igv}")
        print(f"   💸 Total: S/ {documento.total}")
        
        # 6. Generar XML UBL 2.1
        print("📋 PASO 6: Generando XML UBL 2.1...")
        
        try:
            xml_content = generate_ubl_xml(documento)
            documento.xml_content = xml_content
            documento.save()
            
            print(f"   ✅ XML UBL generado: {len(xml_content)} chars")
            print(f"   📋 Preview: {xml_content[:100]}...")
            
        except Exception as xml_error:
            print(f"   ❌ Error generando XML: {xml_error}")
            return None
        
        # 7. Firmar digitalmente
        print("📋 PASO 7: Firmando digitalmente...")
        
        try:
            # Configurar certificado real
            cert_config = {
                'path': 'certificados/production/C23022479065.pfx',
                'password': 'Ch14pp32023'
            }
            
            # Intentar firma real
            try:
                cert_info = certificate_manager.get_certificate(
                    cert_config['path'], 
                    cert_config['password']
                )
                
                signer = XMLSigner()
                xml_firmado = signer.sign_xml_document(xml_content, cert_info)
                
                print(f"   ✅ Firmado con certificado REAL C23022479065")
                documento.estado = 'FIRMADO'
                
            except Exception as e:
                print(f"   ⚠️ Firma real falló: {e}")
                print(f"   🔄 Usando firma simulada...")
                
                # Fallback a firma simulada
                timestamp = datetime.now().isoformat()
                xml_firmado = f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- FIRMA DIGITAL SIMULADA PARA TESTING -->
<!-- Timestamp: {timestamp} -->
<!-- Documento: {documento.get_numero_completo()} -->

{xml_content[xml_content.find('<Invoice'):] if '<Invoice' in xml_content else xml_content}

<!-- FIN FIRMA SIMULADA -->'''
                documento.estado = 'FIRMADO_SIMULADO'
            
            documento.xml_firmado = xml_firmado
            documento.save()
            
            print(f"   ✅ XML firmado: {len(xml_firmado)} chars")
            
        except Exception as sign_error:
            print(f"   ❌ Error en firma: {sign_error}")
            return None
        
        print()
        print("🎉 DOCUMENTO DE PRUEBA CREADO EXITOSAMENTE")
        print("=" * 60)
        print(f"📄 Documento: {documento.get_numero_completo()}")
        print(f"🆔 ID: {documento.id}")
        print(f"🏢 Empresa: {documento.empresa.razon_social}")
        print(f"👤 Cliente: {documento.receptor_razon_social}")
        print(f"💰 Total: S/ {documento.total}")
        print(f"📊 Estado: {documento.estado}")
        print(f"📏 XML: {len(documento.xml_firmado)} chars")
        print()
        print("🚀 AHORA EJECUTA: python fix_error_0160.py")
        
        return documento
        
    except Exception as e:
        print(f"❌ Error creando documento: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    create_test_document()