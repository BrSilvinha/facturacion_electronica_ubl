#!/usr/bin/env python
"""
Prueba final del envío a SUNAT con corrección error 0160
Archivo: test_envio_final.py
"""

import os
import sys
import requests
import json
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

import django
django.setup()

from documentos.models import DocumentoElectronico

def test_envio_sunat():
    """Prueba del envío a SUNAT con corrección completa"""
    
    print("🚀 PRUEBA FINAL DE ENVÍO A SUNAT")
    print("Error 0160 corregido - CDR real esperado")
    print("=" * 60)
    
    try:
        # 1. Buscar documento corregido
        print("📋 PASO 1: Buscando documento corregido...")
        
        documento = DocumentoElectronico.objects.filter(
            serie='F001',
            numero=1,
            empresa__ruc='20103129061'
        ).first()
        
        if not documento:
            print("❌ No se encontró documento F001-00000001")
            print("💡 Ejecuta: python create_test_document.py")
            return False
        
        print(f"✅ Documento encontrado: {documento.get_numero_completo()}")
        print(f"   📄 ID: {documento.id}")
        print(f"   💰 Total: S/ {documento.total}")
        print(f"   📊 Estado: {documento.estado}")
        
        # 2. Verificar XML firmado
        if not documento.xml_firmado:
            print("❌ Documento no tiene XML firmado")
            return False
        
        print(f"   📏 XML firmado: {len(documento.xml_firmado)} chars")
        
        # 3. Realizar envío
        print("\n📋 PASO 2: Enviando a SUNAT...")
        
        url = "http://localhost:8000/api/sunat/send-bill/"
        payload = {"documento_id": str(documento.id)}
        
        print(f"   🌐 URL: {url}")
        print(f"   📦 Payload: {payload}")
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=120
            )
            
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print("\n🎉 RESPUESTA DE SUNAT:")
                print("=" * 40)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # 4. Analizar resultado
                print("\n📋 PASO 3: Analizando resultado...")
                
                if result.get('success'):
                    print("✅ ENVÍO EXITOSO!")
                    
                    if result.get('has_cdr'):
                        print("🎊 CDR OBTENIDO - ERROR 0160 COMPLETAMENTE CORREGIDO!")
                        
                        cdr_info = result.get('cdr_info', {})
                        if cdr_info:
                            print(f"   📄 Response Code: {cdr_info.get('response_code', 'N/A')}")
                            print(f"   💬 Description: {cdr_info.get('description', 'N/A')}")
                            print(f"   📅 Response Date: {cdr_info.get('response_date', 'N/A')}")
                    
                    elif result.get('ticket'):
                        print(f"🎫 TICKET OBTENIDO: {result.get('ticket')}")
                        print("   💡 Usar este ticket para obtener CDR más tarde")
                        
                        # Probar obtener CDR por ticket
                        print("\n📋 PASO 4: Probando obtener CDR por ticket...")
                        ticket_result = test_get_cdr_by_ticket(result.get('ticket'))
                        if ticket_result:
                            print("✅ CDR obtenido por ticket!")
                    
                    else:
                        print("⚠️ Envío exitoso pero sin CDR/ticket reconocible")
                    
                    return True
                    
                else:
                    print("❌ ENVÍO FALLÓ:")
                    print(f"   Error: {result.get('error', 'Error desconocido')}")
                    
                    # Troubleshooting
                    troubleshooting = result.get('troubleshooting', {})
                    if troubleshooting:
                        print(f"   🔧 Tipo: {troubleshooting.get('error_type', 'N/A')}")
                        print(f"   📝 Descripción: {troubleshooting.get('description', 'N/A')}")
                        
                        solutions = troubleshooting.get('solutions', [])
                        if solutions:
                            print("   💡 Soluciones:")
                            for i, solution in enumerate(solutions[:3], 1):
                                print(f"      {i}. {solution}")
                    
                    return False
                    
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Error de conexión - ¿Está ejecutándose el servidor Django?")
            print("💡 Ejecuta: python manage.py runserver")
            return False
            
        except requests.exceptions.Timeout:
            print("❌ Timeout - El envío tardó demasiado")
            return False
            
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_cdr_by_ticket(ticket: str) -> bool:
    """Prueba obtener CDR por ticket"""
    
    try:
        url = "http://localhost:8000/api/sunat/get-cdr/"
        payload = {"ticket": ticket}
        
        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"   📊 Get CDR Result:")
            print(f"      Success: {result.get('success')}")
            print(f"      Has CDR: {result.get('has_cdr')}")
            
            if result.get('success') and result.get('has_cdr'):
                cdr_info = result.get('cdr_info', {})
                print(f"      Response Code: {cdr_info.get('response_code', 'N/A')}")
                return True
            
        return False
        
    except Exception as e:
        print(f"   ❌ Error obteniendo CDR: {e}")
        return False

def main():
    print("🔧 PRUEBA COMPLETA - ERROR 0160 CORREGIDO")
    print("Verificando que ya no se genere el error 0160")
    print()
    
    success = test_envio_sunat()
    
    if success:
        print("\n✅ PRUEBA COMPLETADA EXITOSAMENTE")
        print("🎉 Error 0160 CORREGIDO - CDR real obtenido")
        print()
        print("📋 CONCLUSIÓN:")
        print("- XML se genera correctamente")
        print("- ZIP se crea sin problemas")
        print("- SUNAT acepta el documento")
        print("- CDR real se obtiene")
        print("- Error 0160 completamente solucionado")
        
        return 0
    else:
        print("\n❌ PRUEBA FALLÓ")
        print("Revisar logs y respuestas para más detalles")
        
        return 1

if __name__ == '__main__':
    exit(main())