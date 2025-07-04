#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prueba simplificada sin emojis para Windows
Ubicacion: simple_test.py (en la raiz del proyecto)
"""

import os
import sys
import django
from pathlib import Path
from datetime import date
from decimal import Decimal

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

def test_models():
    """Prueba modelos básicos"""
    print("1. Probando modelos...")
    
    try:
        from documentos.models import Empresa, TipoDocumento
        
        # Verificar tipos de documento
        tipos = TipoDocumento.objects.filter(activo=True)
        print(f"   - Tipos documento: {tipos.count()}")
        
        # Verificar empresas
        empresas = Empresa.objects.filter(activo=True)
        print(f"   - Empresas: {empresas.count()}")
        
        return True
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_calculations():
    """Prueba cálculos tributarios"""
    print("2. Probando cálculos...")
    
    try:
        from conversion.utils.calculations import TributaryCalculator
        
        result = TributaryCalculator.calculate_line_totals(
            cantidad=Decimal('2'),
            valor_unitario=Decimal('100.00'),
            afectacion_igv='10'
        )
        
        print(f"   - Valor venta: {result['valor_venta']}")
        print(f"   - IGV: {result['igv_monto']}")
        print(f"   - Total: {result['precio_venta']}")
        
        return True
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_xml_generation():
    """Prueba generación XML básica"""
    print("3. Probando generación XML...")
    
    try:
        from conversion.generators import UBLGeneratorFactory
        
        supported = UBLGeneratorFactory.get_supported_document_types()
        print(f"   - Tipos soportados: {supported}")
        
        if '01' in supported:
            generator = UBLGeneratorFactory.create_generator('01')
            print(f"   - Generador factura: OK")
        
        return True
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_certificates():
    """Prueba certificados"""
    print("4. Probando certificados...")
    
    try:
        from firma_digital import certificate_manager
        
        cert_path = 'certificados/test/test_cert_empresa1.pfx'
        if Path(cert_path).exists():
            cert_info = certificate_manager.get_certificate(cert_path, 'test123')
            print(f"   - Certificado cargado: {cert_info['metadata']['subject_cn']}")
            return True
        else:
            print("   - Certificado no encontrado")
            return False
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_api_basic():
    """Prueba API básica"""
    print("5. Probando API...")
    
    try:
        from api_rest.views import TestAPIView
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/api/test/')
        
        view = TestAPIView()
        response = view.get(request)
        
        if response.status_code == 200:
            print("   - API funcionando")
            return True
        else:
            print(f"   - API error: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def create_simple_document():
    """Crea documento simple para pruebas"""
    print("6. Creando documento simple...")
    
    try:
        from documentos.models import Empresa, TipoDocumento, DocumentoElectronico
        from conversion.utils.calculations import TributaryCalculator
        
        # Obtener empresa
        empresa = Empresa.objects.filter(activo=True).first()
        if not empresa:
            print("   - No hay empresas disponibles")
            return False
        
        # Obtener tipo documento
        tipo_doc = TipoDocumento.objects.filter(codigo='01', activo=True).first()
        if not tipo_doc:
            print("   - Tipo documento 01 no disponible")
            return False
        
        # Calcular totales simples
        items_data = [{
            'cantidad': Decimal('1'),
            'valor_unitario': Decimal('100.00'),
            'afectacion_igv': '10',
            'descripcion': 'Producto de prueba'
        }]
        
        # Calcular
        items_calculated = []
        for item in items_data:
            calc = TributaryCalculator.calculate_line_totals(
                cantidad=item['cantidad'],
                valor_unitario=item['valor_unitario'],
                afectacion_igv=item['afectacion_igv']
            )
            calc['descripcion'] = item['descripcion']
            items_calculated.append(calc)
        
        # Totales del documento
        totals = TributaryCalculator.calculate_document_totals(items_calculated)
        
        # Crear documento
        documento = DocumentoElectronico.objects.create(
            empresa=empresa,
            tipo_documento=tipo_doc,
            serie='F001',
            numero=999,  # Número de prueba
            receptor_tipo_doc='6',
            receptor_numero_doc='20987654321',
            receptor_razon_social='CLIENTE DE PRUEBA SAC',
            fecha_emision=date.today(),
            moneda='PEN',
            subtotal=totals['total_valor_venta'],
            igv=totals['total_igv'],
            total=totals['total_precio_venta'],
            estado='BORRADOR'
        )
        
        print(f"   - Documento creado: {documento.get_numero_completo()}")
        print(f"   - Total: S/ {documento.total}")
        
        return True
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def main():
    """Función principal"""
    print("PRUEBA SIMPLIFICADA DEL SISTEMA")
    print("=" * 40)
    
    tests = [
        test_models,
        test_calculations,
        test_xml_generation,
        test_certificates,
        test_api_basic,
        create_simple_document,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
                print("   EXITOSO")
            else:
                print("   FALLO")
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print("\n" + "=" * 40)
    print(f"RESULTADO: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("SISTEMA FUNCIONANDO CORRECTAMENTE")
        print("\nPróximos pasos:")
        print("1. python manage.py runserver")
        print("2. Abrir http://localhost:8000/api/test/")
        return 0
    else:
        print("ALGUNOS PROBLEMAS DETECTADOS")
        print("Ejecutar: python fix_windows_issues.py")
        return 1

if __name__ == '__main__':
    exit(main())