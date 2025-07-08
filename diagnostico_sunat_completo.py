#!/usr/bin/env python
"""
Diagnóstico completo del sistema SUNAT con CDR
Ubicación: diagnostico_sunat_completo.py
"""

import os
import sys
import json
import base64
import zipfile
import requests
from io import BytesIO
from pathlib import Path
from datetime import datetime

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

class DiagnosticoSUNAT:
    """Diagnóstico completo del sistema SUNAT"""
    
    def __init__(self):
        self.resultados = []
        self.errores_criticos = []
        self.setup_django()
    
    def setup_django(self):
        """Configurar Django"""
        try:
            import django
            django.setup()
            self.django_ok = True
        except Exception as e:
            self.django_ok = False
            self.errores_criticos.append(f"Error configurando Django: {e}")
    
    def print_header(self, titulo):
        """Imprimir encabezado de sección"""
        print(f"\n{'='*60}")
        print(f"🔍 {titulo}")
        print(f"{'='*60}")
    
    def print_check(self, nombre, status, detalles="", error=""):
        """Imprimir resultado de verificación"""
        icons = {'OK': '✅', 'ERROR': '❌', 'WARNING': '⚠️', 'INFO': 'ℹ️'}
        icon = icons.get(status, '❓')
        
        print(f"{icon} {nombre}: {status}")
        if detalles:
            print(f"   📋 {detalles}")
        if error:
            print(f"   ❌ Error: {error}")
        
        self.resultados.append({
            'nombre': nombre,
            'status': status,
            'detalles': detalles,
            'error': error
        })
        
        if status == 'ERROR':
            self.errores_criticos.append(f"{nombre}: {error}")
    
    def verificar_dependencias(self):
        """Verificar dependencias críticas"""
        self.print_header("VERIFICACIÓN DE DEPENDENCIAS")
        
        dependencias = [
            ('requests', 'Comunicación HTTP'),
            ('zeep', 'Cliente SOAP'),
            ('lxml', 'Procesamiento XML'),
            ('cryptography', 'Certificados digitales'),
            ('django', 'Framework web'),
            ('rest_framework', 'API REST')
        ]
        
        for dep, desc in dependencias:
            try:
                mod = __import__(dep)
                version = getattr(mod, '__version__', 'N/A')
                self.print_check(
                    f"{dep}",
                    "OK",
                    f"{desc} - Versión: {version}"
                )
            except ImportError:
                self.print_check(
                    f"{dep}",
                    "ERROR",
                    desc,
                    f"Módulo no encontrado - Instalar: pip install {dep}"
                )
    
    def verificar_configuracion(self):
        """Verificar configuración Django y SUNAT"""
        self.print_header("VERIFICACIÓN DE CONFIGURACIÓN")
        
        if not self.django_ok:
            self.print_check("Django", "ERROR", "", "Django no configurado correctamente")
            return
        
        try:
            from django.conf import settings
            
            # Verificar SUNAT_CONFIG
            if hasattr(settings, 'SUNAT_CONFIG'):
                config = settings.SUNAT_CONFIG
                self.print_check("SUNAT_CONFIG", "OK", "Configuración SUNAT cargada")
                
                # Verificar campos críticos
                campos_criticos = ['ENVIRONMENT', 'RUC', 'BETA_USER', 'BETA_PASSWORD']
                for campo in campos_criticos:
                    valor = config.get(campo)
                    if valor:
                        # Ocultar password para seguridad
                        display_valor = "***" if 'PASSWORD' in campo else valor
                        self.print_check(
                            f"  {campo}",
                            "OK",
                            f"Configurado: {display_valor}"
                        )
                    else:
                        self.print_check(
                            f"  {campo}",
                            "ERROR",
                            "",
                            f"Campo {campo} no configurado"
                        )
                
                # Verificar URLs
                if 'WSDL_URLS' in config:
                    urls = config['WSDL_URLS'].get('beta', {})
                    self.print_check(
                        "  URLs WSDL Beta",
                        "OK",
                        f"Configuradas: {len(urls)} URLs"
                    )
                else:
                    self.print_check("  URLs WSDL", "ERROR", "", "URLs no configuradas")
                    
            else:
                self.print_check("SUNAT_CONFIG", "ERROR", "", "SUNAT_CONFIG no encontrado en settings")
            
            # Verificar DIGITAL_SIGNATURE_CONFIG
            if hasattr(settings, 'DIGITAL_SIGNATURE_CONFIG'):
                self.print_check("DIGITAL_SIGNATURE_CONFIG", "OK", "Configuración de firma digital cargada")
            else:
                self.print_check("DIGITAL_SIGNATURE_CONFIG", "WARNING", "", "Configuración de firma no encontrada")
                
        except Exception as e:
            self.print_check("Configuración Django", "ERROR", "", str(e))
    
    def verificar_certificados(self):
        """Verificar certificados digitales"""
        self.print_header("VERIFICACIÓN DE CERTIFICADOS")
        
        if not self.django_ok:
            self.print_check("Certificados", "ERROR", "", "Django no disponible")
            return
        
        try:
            # Verificar certificado real
            cert_real_path = Path('certificados/production/cert_20103129061.pfx')
            if cert_real_path.exists():
                size_kb = cert_real_path.stat().st_size / 1024
                self.print_check(
                    "Certificado Real",
                    "OK",
                    f"Encontrado: {size_kb:.1f} KB"
                )
                
                # Probar carga del certificado
                try:
                    from firma_digital import certificate_manager
                    cert_info = certificate_manager.get_certificate(
                        str(cert_real_path),
                        'Ch14pp32023'
                    )
                    
                    subject = cert_info['metadata']['subject_cn']
                    expires = cert_info['metadata']['not_after']
                    
                    self.print_check(
                        "  Carga de Certificado",
                        "OK",
                        f"Sujeto: {subject}, Expira: {expires.strftime('%Y-%m-%d')}"
                    )
                    
                except Exception as e:
                    self.print_check(
                        "  Carga de Certificado",
                        "ERROR",
                        "",
                        str(e)
                    )
            else:
                self.print_check(
                    "Certificado Real",
                    "ERROR",
                    "",
                    f"No encontrado en: {cert_real_path}"
                )
            
            # Verificar certificados de prueba
            cert_test_dir = Path('certificados/test')
            if cert_test_dir.exists():
                test_certs = list(cert_test_dir.glob('*.pfx'))
                self.print_check(
                    "Certificados de Prueba",
                    "OK",
                    f"Encontrados: {len(test_certs)} certificados"
                )
            else:
                self.print_check(
                    "Certificados de Prueba",
                    "WARNING",
                    "",
                    "Directorio de prueba no encontrado"
                )
                
        except Exception as e:
            self.print_check("Verificación Certificados", "ERROR", "", str(e))
    
    def verificar_conectividad_sunat(self):
        """Verificar conectividad con SUNAT"""
        self.print_header("VERIFICACIÓN CONECTIVIDAD SUNAT")
        
        try:
            # URLs para probar
            urls_test = [
                "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService",
                "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
            ]
            
            # Credenciales
            username = "20103129061MODDATOS"
            password = "MODDATOS"
            
            for url in urls_test:
                try:
                    response = requests.get(
                        url,
                        auth=requests.auth.HTTPBasicAuth(username, password),
                        timeout=30,
                        verify=True
                    )
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '')
                        size = len(response.content)
                        
                        if 'wsdl' in url and 'xml' in content_type:
                            self.print_check(
                                f"WSDL SUNAT",
                                "OK",
                                f"Descargado: {size} bytes, Content-Type: {content_type}"
                            )
                        else:
                            self.print_check(
                                f"Servicio SUNAT",
                                "OK",
                                f"Respuesta: {response.status_code}, Tamaño: {size} bytes"
                            )
                    else:
                        self.print_check(
                            f"URL: {url}",
                            "ERROR",
                            "",
                            f"HTTP {response.status_code}"
                        )
                        
                except Exception as e:
                    self.print_check(
                        f"URL: {url}",
                        "ERROR",
                        "",
                        str(e)
                    )
                    
        except Exception as e:
            self.print_check("Conectividad SUNAT", "ERROR", "", str(e))
    
    def probar_cliente_soap(self):
        """Probar cliente SOAP con zeep"""
        self.print_header("PRUEBA CLIENTE SOAP")
        
        try:
            from zeep import Client, Settings
            from zeep.transports import Transport
            import requests
            from requests.auth import HTTPBasicAuth
            
            # Configurar sesión
            session = requests.Session()
            session.auth = HTTPBasicAuth("20103129061MODDATOS", "MODDATOS")
            session.verify = True
            
            # Configurar zeep
            transport = Transport(session=session, timeout=60)
            settings = Settings(strict=False, xml_huge_tree=True)
            
            wsdl_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl"
            
            self.print_check("Inicialización zeep", "INFO", "Cargando WSDL...")
            
            client = Client(wsdl_url, transport=transport, settings=settings)
            
            # Verificar operaciones
            operations = [op for op in dir(client.service) if not op.startswith('_')]
            
            self.print_check(
                "Cliente SOAP",
                "OK",
                f"Operaciones disponibles: {', '.join(operations)}"
            )
            
            # Verificar sendBill específicamente
            if hasattr(client.service, 'sendBill'):
                self.print_check(
                    "  Operación sendBill",
                    "OK",
                    "Disponible para envío de documentos"
                )
            else:
                self.print_check(
                    "  Operación sendBill",
                    "ERROR",
                    "",
                    "sendBill no disponible"
                )
                
        except ImportError:
            self.print_check(
                "Cliente SOAP",
                "ERROR",
                "",
                "zeep no instalado - pip install zeep"
            )
        except Exception as e:
            self.print_check(
                "Cliente SOAP",
                "ERROR",
                "",
                str(e)
            )
    
    def verificar_documentos_test(self):
        """Verificar documentos de prueba"""
        self.print_header("VERIFICACIÓN DOCUMENTOS DE PRUEBA")
        
        if not self.django_ok:
            self.print_check("Documentos", "ERROR", "", "Django no disponible")
            return
        
        try:
            from documentos.models import DocumentoElectronico
            
            # Estadísticas generales
            total_docs = DocumentoElectronico.objects.count()
            docs_firmados = DocumentoElectronico.objects.exclude(xml_firmado__isnull=True).count()
            
            self.print_check(
                "Documentos Totales",
                "OK" if total_docs > 0 else "WARNING",
                f"Total: {total_docs}, Firmados: {docs_firmados}"
            )
            
            # Último documento firmado
            last_doc = DocumentoElectronico.objects.filter(
                xml_firmado__isnull=False
            ).order_by('-created_at').first()
            
            if last_doc:
                xml_size = len(last_doc.xml_firmado)
                has_signature = '<ds:Signature' in last_doc.xml_firmado
                
                self.print_check(
                    "Último Documento",
                    "OK",
                    f"{last_doc.get_numero_completo()}, XML: {xml_size:,} chars, Firma: {'Sí' if has_signature else 'No'}"
                )
                
                # Probar creación de ZIP
                try:
                    zip_buffer = BytesIO()
                    filename = f"{last_doc.empresa.ruc}-{last_doc.tipo_documento.codigo}-{last_doc.serie}-{last_doc.numero:08d}.xml"
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        zip_file.writestr('dummy/', '')
                        zip_file.writestr(filename, last_doc.xml_firmado.encode('utf-8'))
                    
                    zip_size = len(zip_buffer.getvalue())
                    
                    self.print_check(
                        "  Creación ZIP",
                        "OK",
                        f"ZIP generado: {zip_size:,} bytes"
                    )
                    
                except Exception as e:
                    self.print_check(
                        "  Creación ZIP",
                        "ERROR",
                        "",
                        str(e)
                    )
            else:
                self.print_check(
                    "Documentos Firmados",
                    "WARNING",
                    "",
                    "No hay documentos firmados para probar"
                )
                
        except Exception as e:
            self.print_check("Verificación Documentos", "ERROR", "", str(e))
    
    def probar_envio_manual(self):
        """Probar envío manual con XML simple"""
        self.print_header("PRUEBA ENVÍO MANUAL")
        
        try:
            # XML UBL mínimo para prueba
            xml_simple = '''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:ID>F001-00000001</cbc:ID>
    <cbc:IssueDate>2025-07-08</cbc:IssueDate>
    <cbc:InvoiceTypeCode>01</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>PEN</cbc:DocumentCurrencyCode>
</Invoice>'''
            
            # Crear ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr('dummy/', '')
                zip_file.writestr('20103129061-01-F001-00000001.xml', xml_simple.encode('utf-8'))
            
            zip_content = zip_buffer.getvalue()
            content_base64 = base64.b64encode(zip_content).decode('utf-8')
            
            self.print_check(
                "Preparación ZIP",
                "OK",
                f"ZIP de prueba: {len(zip_content)} bytes"
            )
            
            # SOAP envelope
            soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Header>
        <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
            <wsse:UsernameToken>
                <wsse:Username>20103129061MODDATOS</wsse:Username>
                <wsse:Password>MODDATOS</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soap:Header>
    <soap:Body>
        <sendBill xmlns="http://service.sunat.gob.pe">
            <fileName>20103129061-01-F001-00000001.zip</fileName>
            <contentFile>{content_base64}</contentFile>
        </sendBill>
    </soap:Body>
</soap:Envelope>'''
            
            # Enviar request
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'sendBill'
            }
            
            url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService"
            
            self.print_check("Envío SOAP", "INFO", "Enviando request a SUNAT...")
            
            response = requests.post(
                url,
                data=soap_body,
                headers=headers,
                timeout=60,
                verify=True
            )
            
            # Analizar respuesta
            if response.status_code == 200:
                if 'applicationResponse' in response.text:
                    self.print_check(
                        "Respuesta SUNAT",
                        "OK",
                        "CDR detectado en respuesta - ¡ÉXITO!"
                    )
                elif 'faultstring' in response.text:
                    # Extraer mensaje de error
                    import re
                    fault_match = re.search(r'<faultstring[^>]*>([^<]+)</faultstring>', response.text)
                    fault_msg = fault_match.group(1) if fault_match else "Error desconocido"
                    
                    self.print_check(
                        "Respuesta SUNAT",
                        "ERROR",
                        "",
                        f"SOAP Fault: {fault_msg}"
                    )
                else:
                    self.print_check(
                        "Respuesta SUNAT",
                        "WARNING",
                        f"Respuesta inesperada: {len(response.text)} caracteres"
                    )
            else:
                self.print_check(
                    "Respuesta SUNAT",
                    "ERROR",
                    "",
                    f"HTTP {response.status_code}: {response.text[:200]}..."
                )
                
        except Exception as e:
            self.print_check("Envío Manual", "ERROR", "", str(e))
    
    def generar_reporte(self):
        """Generar reporte final"""
        self.print_header("REPORTE FINAL")
        
        total_checks = len(self.resultados)
        ok_checks = len([r for r in self.resultados if r['status'] == 'OK'])
        error_checks = len([r for r in self.resultados if r['status'] == 'ERROR'])
        warning_checks = len([r for r in self.resultados if r['status'] == 'WARNING'])
        
        print(f"📊 ESTADÍSTICAS:")
        print(f"   ✅ Exitosos: {ok_checks}/{total_checks}")
        print(f"   ❌ Errores: {error_checks}/{total_checks}")
        print(f"   ⚠️ Advertencias: {warning_checks}/{total_checks}")
        
        # Estado general
        if error_checks == 0:
            estado_general = "🎉 EXCELENTE"
        elif error_checks <= 2:
            estado_general = "⚠️ FUNCIONAL CON PROBLEMAS MENORES"
        else:
            estado_general = "❌ REQUIERE CORRECCIONES"
        
        print(f"\n🎯 ESTADO GENERAL: {estado_general}")
        
        # Errores críticos
        if self.errores_criticos:
            print(f"\n🚨 ERRORES CRÍTICOS A RESOLVER:")
            for i, error in enumerate(self.errores_criticos, 1):
                print(f"   {i}. {error}")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        
        if error_checks > 0:
            print(f"   1. Corregir errores críticos listados arriba")
            
            # Recomendaciones específicas
            if any('zeep' in error for error in self.errores_criticos):
                print(f"   2. Instalar zeep: pip install zeep")
            
            if any('Certificado' in error for error in self.errores_criticos):
                print(f"   3. Verificar certificados en certificados/production/")
            
            if any('SUNAT' in error for error in self.errores_criticos):
                print(f"   4. Verificar conectividad y credenciales SUNAT")
        
        else:
            print(f"   ✅ Sistema funcionando correctamente")
            print(f"   🚀 Listo para enviar documentos a SUNAT")
        
        # Próximos pasos
        print(f"\n🔄 PRÓXIMOS PASOS:")
        if error_checks == 0:
            print(f"   1. Probar envío real con documento firmado")
            print(f"   2. Verificar recepción de CDR")
            print(f"   3. Implementar en producción")
        else:
            print(f"   1. Ejecutar correcciones recomendadas")
            print(f"   2. Re-ejecutar diagnóstico: python diagnostico_sunat_completo.py")
            print(f"   3. Probar envío cuando todos los checks estén OK")
        
        # Guardar reporte en archivo
        try:
            reporte = {
                'timestamp': datetime.now().isoformat(),
                'estadisticas': {
                    'total': total_checks,
                    'ok': ok_checks,
                    'error': error_checks,
                    'warning': warning_checks
                },
                'estado_general': estado_general,
                'errores_criticos': self.errores_criticos,
                'resultados_detallados': self.resultados
            }
            
            with open('diagnostico_sunat_report.json', 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)
            
            print(f"\n📋 Reporte guardado en: diagnostico_sunat_report.json")
            
        except Exception as e:
            print(f"\n⚠️ No se pudo guardar reporte: {e}")
    
    def ejecutar_diagnostico_completo(self):
        """Ejecutar diagnóstico completo paso a paso"""
        
        print("🚀 DIAGNÓSTICO COMPLETO DEL SISTEMA SUNAT")
        print("=" * 60)
        print("Este diagnóstico verificará todo el sistema paso a paso")
        print("para identificar por qué no recibes el CDR de SUNAT.")
        print("")
        
        # Ejecutar todas las verificaciones
        self.verificar_dependencias()
        self.verificar_configuracion()
        self.verificar_certificados()
        self.verificar_conectividad_sunat()
        self.probar_cliente_soap()
        self.verificar_documentos_test()
        
        # Preguntar si hacer prueba de envío
        print(f"\n" + "="*60)
        respuesta = input("¿Desea ejecutar prueba de envío manual a SUNAT? (s/n): ").lower()
        
        if respuesta in ['s', 'si', 'y', 'yes']:
            self.probar_envio_manual()
        
        # Generar reporte final
        self.generar_reporte()

def crear_script_correccion():
    """Crear script de corrección automática"""
    
    script_content = '''#!/usr/bin/env python
"""
Script de corrección automática para problemas comunes
"""

import subprocess
import sys

def instalar_dependencias():
    """Instalar dependencias faltantes"""
    dependencias = [
        'zeep',
        'lxml', 
        'requests',
        'cryptography'
    ]
    
    for dep in dependencias:
        print(f"Instalando {dep}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])

def verificar_certificados():
    """Verificar que los certificados estén en su lugar"""
    from pathlib import Path
    
    cert_real = Path('certificados/production/cert_20103129061.pfx')
    if not cert_real.exists():
        print("❌ Certificado real no encontrado")
        print("💡 Coloca tu certificado .pfx en certificados/production/")
        return False
    
    print("✅ Certificado real encontrado")
    return True

def main():
    print("🔧 CORRECCIÓN AUTOMÁTICA DE PROBLEMAS SUNAT")
    print("=" * 50)
    
    try:
        print("1. Instalando dependencias...")
        instalar_dependencias()
        
        print("2. Verificando certificados...")
        verificar_certificados()
        
        print("3. Ejecutando diagnóstico...")
        from diagnostico_sunat_completo import DiagnosticoSUNAT
        diagnostico = DiagnosticoSUNAT()
        diagnostico.ejecutar_diagnostico_completo()
        
    except Exception as e:
        print(f"❌ Error en corrección: {e}")

if __name__ == '__main__':
    main()
'''
    
    with open('corregir_sunat.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("📋 Script de corrección creado: corregir_sunat.py")

def main():
    """Función principal"""
    
    try:
        diagnostico = DiagnosticoSUNAT()
        diagnostico.ejecutar_diagnostico_completo()
        
        # Ofrecer crear script de corrección
        print(f"\n" + "="*60)
        respuesta = input("¿Desea crear script de corrección automática? (s/n): ").lower()
        
        if respuesta in ['s', 'si', 'y', 'yes']:
            crear_script_correccion()
        
        print(f"\n🎯 DIAGNÓSTICO COMPLETADO")
        print(f"💡 Revisa los resultados y sigue las recomendaciones")
        
        return True
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Diagnóstico interrumpido por el usuario")
        return False
        
    except Exception as e:
        print(f"\n\n❌ Error ejecutando diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)