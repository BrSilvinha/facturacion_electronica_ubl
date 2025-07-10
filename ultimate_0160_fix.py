#!/usr/bin/env python
"""
SOLUCIÓN DEFINITIVA ERROR 0160 SUNAT
Archivo: ultimate_0160_fix.py

Este script implementa la solución más avanzada para el error 0160,
incluyendo verificación de transmisión y debugging completo.
"""

import os
import sys
import base64
import zipfile
import requests
from io import BytesIO
from pathlib import Path
from datetime import datetime
import json

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')

import django
django.setup()

from documentos.models import DocumentoElectronico

class Ultimate0160Fixer:
    """Solución definitiva para el error 0160"""
    
    def __init__(self):
        self.correlation_id = f"ULTIMATE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"🚀 [{self.correlation_id}] SOLUCIÓN DEFINITIVA ERROR 0160 SUNAT")
        print("=" * 70)
        
        # Credenciales SUNAT
        self.ruc = "20103129061"
        self.usuario_base = "MODDATOS"
        self.password = "MODDATOS"
        self.usuario_completo = f"{self.ruc}{self.usuario_base}"
        self.service_url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService"
    
    def run_ultimate_fix(self):
        """Ejecuta la solución definitiva"""
        
        print("📋 FASE 1: OBTENER Y VERIFICAR DOCUMENTO")
        documento = self._get_document()
        if not documento:
            return False
        
        print("📋 FASE 2: CREAR ZIP CON MÁXIMA VERIFICACIÓN")
        zip_content = self._create_ultimate_zip(documento)
        if not zip_content:
            return False
        
        print("📋 FASE 3: MÚLTIPLES MÉTODOS DE ENVÍO")
        success = self._try_multiple_send_methods(documento, zip_content)
        
        return success
    
    def _get_document(self):
        """Obtiene el documento más reciente"""
        try:
            documento = DocumentoElectronico.objects.filter(
                serie='F001',
                numero=1,
                empresa__ruc=self.ruc
            ).first()
            
            if not documento:
                print("❌ No se encontró documento F001-00000001")
                return None
            
            print(f"✅ Documento: {documento.get_numero_completo()}")
            print(f"   📄 ID: {documento.id}")
            print(f"   📏 XML: {len(documento.xml_firmado)} chars")
            
            return documento
            
        except Exception as e:
            print(f"❌ Error obteniendo documento: {e}")
            return None
    
    def _create_ultimate_zip(self, documento):
        """Crea ZIP con verificación máxima"""
        
        print(f"   🔧 Creando ZIP con verificación MÁXIMA...")
        
        try:
            # 1. Preparar XML con limpieza extrema
            xml_content = documento.xml_firmado.strip()
            
            # Remover BOM
            if xml_content.startswith('\ufeff'):
                xml_content = xml_content[1:]
            
            # Asegurar encoding UTF-8
            if not xml_content.startswith('<?xml version="1.0" encoding="UTF-8"?>'):
                if xml_content.startswith('<?xml'):
                    import re
                    xml_content = re.sub(r'<\?xml[^>]*\?>', '<?xml version="1.0" encoding="UTF-8"?>', xml_content)
                else:
                    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content
            
            print(f"      📏 XML limpio: {len(xml_content)} chars")
            print(f"      📋 Preview: {xml_content[:100]}...")
            
            # 2. Crear ZIP con configuración específica SUNAT
            zip_buffer = BytesIO()
            xml_filename = f"{self.ruc}-01-{documento.serie}-{documento.numero:08d}.xml"
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as zip_file:
                # Carpeta dummy
                zip_file.writestr('dummy/', '')
                
                # XML con encoding explícito
                xml_bytes = xml_content.encode('utf-8')
                zip_file.writestr(xml_filename, xml_bytes)
                
                print(f"      📦 Archivos agregados:")
                print(f"         - dummy/ (carpeta)")
                print(f"         - {xml_filename} ({len(xml_bytes)} bytes)")
            
            zip_content = zip_buffer.getvalue()
            
            # 3. Verificación extrema del ZIP
            self._verify_zip_extremely(zip_content, xml_filename)
            
            # 4. Guardar ZIP para análisis
            self._save_ultimate_zip(zip_content, xml_filename)
            
            return zip_content
            
        except Exception as e:
            print(f"      ❌ Error creando ZIP: {e}")
            return None
    
    def _verify_zip_extremely(self, zip_content, expected_filename):
        """Verificación extrema del ZIP"""
        
        print(f"      🔍 Verificación EXTREMA del ZIP...")
        
        # Verificar tamaño
        print(f"         📦 Tamaño ZIP: {len(zip_content)} bytes")
        
        if len(zip_content) < 1000:
            raise Exception(f"ZIP muy pequeño: {len(zip_content)} bytes")
        
        # Verificar contenido
        with zipfile.ZipFile(BytesIO(zip_content), 'r') as zip_file:
            files = zip_file.namelist()
            print(f"         📋 Archivos: {files}")
            
            if len(files) != 2:
                raise Exception(f"ZIP debe tener 2 archivos, tiene: {len(files)}")
            
            if 'dummy/' not in files:
                raise Exception("Falta carpeta dummy/")
            
            if expected_filename not in files:
                raise Exception(f"Falta archivo {expected_filename}")
            
            # Verificar contenido del XML
            xml_content = zip_file.read(expected_filename).decode('utf-8')
            print(f"         📄 XML en ZIP: {len(xml_content)} chars")
            
            if len(xml_content) < 1000:
                raise Exception(f"XML en ZIP muy corto: {len(xml_content)} chars")
            
            if not xml_content.startswith('<?xml'):
                raise Exception("XML en ZIP sin declaración")
            
            if '<Invoice' not in xml_content:
                raise Exception("XML en ZIP sin elemento Invoice")
        
        print(f"      ✅ ZIP verificado exitosamente")
    
    def _save_ultimate_zip(self, zip_content, filename):
        """Guarda ZIP para análisis"""
        
        try:
            output_dir = Path('temp') / 'ultimate_fix'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            zip_path = output_dir / f"{filename.replace('.xml', '')}_ULTIMATE.zip"
            with open(zip_path, 'wb') as f:
                f.write(zip_content)
            
            print(f"      💾 ZIP guardado: {zip_path}")
            
        except Exception as e:
            print(f"      ⚠️ Error guardando ZIP: {e}")
    
    def _try_multiple_send_methods(self, documento, zip_content):
        """Prueba múltiples métodos de envío"""
        
        methods = [
            self._method_1_chunked_upload,
            self._method_2_minimal_headers,
            self._method_3_raw_soap,
            self._method_4_alternative_encoding
        ]
        
        for i, method in enumerate(methods, 1):
            print(f"\n🎯 MÉTODO {i}: {method.__name__.replace('_method_', '').replace('_', ' ').upper()}")
            
            try:
                result = method(documento, zip_content)
                
                if result.get('success'):
                    print(f"   ✅ MÉTODO {i} EXITOSO!")
                    return True
                else:
                    print(f"   ❌ Método {i} falló: {result.get('error', 'Error desconocido')}")
                    
                    # Si sigue siendo error 0160, mostrar detalles
                    if '0160' in str(result.get('error', '')):
                        print(f"      🔍 Debug info: {result.get('debug_info', {})}")
            
            except Exception as e:
                print(f"   💥 Método {i} excepción: {e}")
        
        print(f"\n❌ TODOS LOS MÉTODOS FALLARON")
        return False
    
    def _method_1_chunked_upload(self, documento, zip_content):
        """Método 1: Upload por chunks"""
        
        print("      🔄 Enviando con Transfer-Encoding chunked...")
        
        # Codificar Base64
        content_base64 = base64.b64encode(zip_content).decode('utf-8')
        filename = f"{self.ruc}-01-{documento.serie}-{documento.numero:08d}.zip"
        
        # Envelope SOAP
        envelope = self._create_soap_envelope(filename, content_base64)
        
        # Headers con chunked transfer
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'urn:sendBill',
            'Transfer-Encoding': 'chunked',
            'User-Agent': 'Python-SUNAT-Ultimate/1.0',
            'Accept': 'text/xml',
            'Connection': 'close'
        }
        
        return self._send_request(envelope, headers, "chunked")
    
    def _method_2_minimal_headers(self, documento, zip_content):
        """Método 2: Headers mínimos"""
        
        print("      🎯 Enviando con headers mínimos...")
        
        content_base64 = base64.b64encode(zip_content).decode('utf-8')
        filename = f"{self.ruc}-01-{documento.serie}-{documento.numero:08d}.zip"
        
        envelope = self._create_soap_envelope(filename, content_base64)
        
        # Headers mínimos
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'urn:sendBill'
        }
        
        return self._send_request(envelope, headers, "minimal")
    
    def _method_3_raw_soap(self, documento, zip_content):
        """Método 3: SOAP raw sin optimizaciones"""
        
        print("      📡 Enviando SOAP raw...")
        
        content_base64 = base64.b64encode(zip_content).decode('utf-8')
        filename = f"{self.ruc}-01-{documento.serie}-{documento.numero:08d}.zip"
        
        # Envelope SOAP simplificado
        envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.sunat.gob.pe">
    <soapenv:Header>
        <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
            <wsse:UsernameToken>
                <wsse:Username>{self.usuario_completo}</wsse:Username>
                <wsse:Password>{self.password}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soapenv:Header>
    <soapenv:Body>
        <ser:sendBill>
            <fileName>{filename}</fileName>
            <contentFile>{content_base64}</contentFile>
        </ser:sendBill>
    </soapenv:Body>
</soapenv:Envelope>'''
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'urn:sendBill',
            'Content-Length': str(len(envelope.encode('utf-8')))
        }
        
        return self._send_request(envelope, headers, "raw_soap")
    
    def _method_4_alternative_encoding(self, documento, zip_content):
        """Método 4: Encoding alternativo"""
        
        print("      🔀 Enviando con encoding alternativo...")
        
        # Probar sin compresión ZIP
        xml_content = documento.xml_firmado.strip()
        if xml_content.startswith('\ufeff'):
            xml_content = xml_content[1:]
        
        # Crear ZIP sin compresión
        zip_buffer = BytesIO()
        xml_filename = f"{self.ruc}-01-{documento.serie}-{documento.numero:08d}.xml"
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zip_file:  # Sin compresión
            zip_file.writestr('dummy/', '')
            zip_file.writestr(xml_filename, xml_content.encode('utf-8'))
        
        alt_zip_content = zip_buffer.getvalue()
        content_base64 = base64.b64encode(alt_zip_content).decode('utf-8')
        
        envelope = self._create_soap_envelope(f"{self.ruc}-01-{documento.serie}-{documento.numero:08d}.zip", content_base64)
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'urn:sendBill',
            'User-Agent': 'Python-SUNAT-NoCompression/1.0'
        }
        
        return self._send_request(envelope, headers, "no_compression")
    
    def _create_soap_envelope(self, filename, content_base64):
        """Crea envelope SOAP optimizado"""
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:ser="http://service.sunat.gob.pe"
               xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
    <soap:Header>
        <wsse:Security>
            <wsse:UsernameToken>
                <wsse:Username>{self.usuario_completo}</wsse:Username>
                <wsse:Password>{self.password}</wsse:Password>
            </wsse:UsernameToken>
        </wsse:Security>
    </soap:Header>
    <soap:Body>
        <ser:sendBill>
            <fileName>{filename}</fileName>
            <contentFile>{content_base64}</contentFile>
        </ser:sendBill>
    </soap:Body>
</soap:Envelope>'''
    
    def _send_request(self, envelope, headers, method_name):
        """Envía request y analiza respuesta"""
        
        try:
            from requests.auth import HTTPBasicAuth
            
            auth = HTTPBasicAuth(self.usuario_completo, self.password)
            
            print(f"         🌐 Enviando a: {self.service_url}")
            print(f"         📦 Envelope size: {len(envelope)} chars")
            print(f"         🔐 Auth: {self.usuario_completo}")
            
            response = requests.post(
                self.service_url,
                data=envelope.encode('utf-8'),
                headers=headers,
                auth=auth,
                timeout=90,
                verify=True
            )
            
            print(f"         📊 Status: {response.status_code}")
            print(f"         📏 Response: {len(response.text)} chars")
            
            # Guardar respuesta para debugging
            self._save_response_debug(response.text, method_name)
            
            if response.status_code == 200:
                if 'Client.0160' in response.text:
                    return {
                        'success': False,
                        'error': f'Error 0160 persiste con método {method_name}',
                        'debug_info': {
                            'method': method_name,
                            'envelope_size': len(envelope),
                            'response_preview': response.text[:500]
                        }
                    }
                else:
                    return {
                        'success': True,
                        'method': method_name,
                        'response': response.text
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text[:500]
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_response_debug(self, response_text, method_name):
        """Guarda respuesta para debugging"""
        
        try:
            debug_dir = Path('temp') / 'ultimate_debug'
            debug_dir.mkdir(parents=True, exist_ok=True)
            
            debug_file = debug_dir / f"response_{method_name}_{self.correlation_id}.xml"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            
            print(f"         💾 Response guardada: {debug_file}")
            
        except Exception as e:
            print(f"         ⚠️ Error guardando response: {e}")

def main():
    print("🔥 SOLUCIÓN DEFINITIVA ERROR 0160 SUNAT")
    print("Probando múltiples métodos de transmisión")
    print()
    
    try:
        fixer = Ultimate0160Fixer()
        success = fixer.run_ultimate_fix()
        
        if success:
            print("\n🎉 SOLUCIÓN DEFINITIVA EXITOSA!")
            print("Error 0160 finalmente corregido")
            return 0
        else:
            print("\n❌ SOLUCIÓN DEFINITIVA FALLÓ")
            print("El problema puede estar en:")
            print("1. Configuración de red/firewall")
            print("2. Certificados SSL")
            print("3. Configuración de SUNAT Beta")
            print("4. Problema en la infraestructura de SUNAT")
            return 1
            
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())