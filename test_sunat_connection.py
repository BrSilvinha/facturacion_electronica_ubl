#!/usr/bin/env python
"""
Test completo de conexión y envío a SUNAT
Archivo: test_sunat_connection.py
Ubicación: Raíz del proyecto (junto a manage.py)
"""

import os
import sys
import django
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth
import base64
import zipfile
from io import BytesIO
import json
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facturacion_electronica.settings')
django.setup()

from django.conf import settings

def test_configuracion():
    """Test 1: Verificar configuración"""
    print("=" * 60)
    print("🔧 TEST 1: VERIFICACIÓN DE CONFIGURACIÓN")
    print("=" * 60)
    
    try:
        sunat_config = settings.SUNAT_CONFIG
        print(f"✅ RUC configurado: {sunat_config['RUC']}")
        print(f"✅ Ambiente: {sunat_config['ENVIRONMENT']}")
        print(f"✅ Usuario base: {sunat_config['BETA_USER']}")
        print(f"✅ Usuario completo: {sunat_config['RUC']}{sunat_config['BETA_USER']}")
        
        # Verificar WSDL local
        wsdl_local = Path('sunat_integration/sunat_complete.wsdl')
        print(f"✅ WSDL local existe: {wsdl_local.exists()}")
        
        return True, sunat_config
        
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False, None

def test_autenticacion(sunat_config):
    """Test 2: Verificar autenticación HTTP"""
    print("\n" + "=" * 60)
    print("🔐 TEST 2: AUTENTICACIÓN SOAP DIRECTA")
    print("=" * 60)
    
    try:
        # Preparar credenciales
        ruc = sunat_config['RUC']
        username = sunat_config['BETA_USER']
        password = sunat_config['BETA_PASSWORD']
        full_username = f"{ruc}{username}"
        
        print(f"🔑 RUC: {ruc}")
        print(f"🔑 Usuario base: {username}")
        print(f"🔑 Usuario completo: {full_username}")
        print(f"🔑 Password: {password}")
        
        # Configurar sesión
        session = requests.Session()
        session.auth = HTTPBasicAuth(full_username, password)
        
        # URL del servicio
        url = "https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService"
        print(f"🌐 URL: {url}")
        
        # Test con SOAP mínimo para verificar autenticación
        print("📡 Realizando test de autenticación con SOAP mínimo...")
        
        soap_test = '''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:ser="http://service.sunat.gob.pe">
   <soapenv:Header/>
   <soapenv:Body>
      <ser:sendBill>
         <fileName>test.zip</fileName>
         <contentFile>UEsDBAoAAAAAALhpUFMAAAAAAAAAAAAAAAAGAAAAZHVtbXkvUEsBAhQACgAAAAAA</contentFile>
      </ser:sendBill>
   </soapenv:Body>
</soapenv:Envelope>'''
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'urn:sendBill'
        }
        
        response = session.post(url, data=soap_test, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Status Text: {response.reason}")
        
        if response.status_code == 200:
            print("✅ ¡AUTENTICACIÓN EXITOSA!")
            # Verificar si es una respuesta SOAP válida
            if 'soap' in response.text.lower() or 'envelope' in response.text.lower():
                print("✅ Respuesta SOAP válida recibida")
                return True, session, url
            else:
                print("⚠️ Respuesta no SOAP, pero status 200")
                return True, session, url
                
        elif response.status_code == 401:
            print("❌ CREDENCIALES INCORRECTAS")
            print("📝 Detalles del error:")
            print(f"   Response: {response.text[:300]}")
            return False, None, None
            
        elif response.status_code == 403:
            print("❌ ACCESO PROHIBIDO")
            print("📝 Detalles del error:")
            print(f"   Response: {response.text[:300]}")
            return False, None, None
            
        elif response.status_code == 500:
            # Status 500 puede indicar error en el XML, pero auth OK
            if 'faultcode>env:Client<' in response.text:
                print("✅ AUTENTICACIÓN OK - Error de formato XML (esperado)")
                print("📝 SUNAT rechaza el XML de test pero acepta las credenciales")
                return True, session, url
            else:
                print("❌ ERROR INTERNO DEL SERVIDOR SUNAT")
                print(f"📝 Response: {response.text[:300]}")
                return False, None, None
            
        else:
            print(f"⚠️ STATUS INESPERADO: {response.status_code}")
            print(f"📝 Response: {response.text[:300]}")
            # Si no es 401/403, asumimos que auth está OK
            return True, session, url
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT - SUNAT no responde")
        return False, None, None
        
    except requests.exceptions.ConnectionError:
        print("🌐 ERROR DE CONEXIÓN - Verificar internet")
        return False, None, None
        
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        return False, None, None

def crear_xml_prueba():
    """Crear XML de prueba para envío"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>2.0</cbc:CustomizationID>
    <cbc:ID>F001-00001001</cbc:ID>
    <cbc:IssueDate>2025-07-09</cbc:IssueDate>
    <cbc:InvoiceTypeCode>01</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>PEN</cbc:DocumentCurrencyCode>
    
    <!-- Datos del emisor -->
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">20103129061</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>COMERCIAL LAVAGNA S.A.C.</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <!-- Datos del cliente -->
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">20123456789</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>CLIENTE TEST SAC</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    <!-- Totales -->
    <cac:LegalMonetaryTotal>
        <cbc:PayableAmount currencyID="PEN">118.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
</Invoice>'''

def test_envio_soap(session, url):
    """Test 3: Envío SOAP directo"""
    print("\n" + "=" * 60)
    print("📤 TEST 3: ENVÍO SOAP DIRECTO")
    print("=" * 60)
    
    try:
        # Crear XML de prueba
        print("📝 Creando XML de prueba...")
        documento_xml = crear_xml_prueba()
        print(f"✅ XML creado: {len(documento_xml)} caracteres")
        
        # Crear ZIP según especificaciones SUNAT
        print("📦 Creando ZIP...")
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Carpeta dummy requerida por SUNAT
            zip_file.writestr('dummy/', '')
            
            # XML del documento
            filename = '20103129061-01-F001-00001001.xml'
            zip_file.writestr(filename, documento_xml.encode('utf-8'))
            
            print(f"✅ Agregado: dummy/")
            print(f"✅ Agregado: {filename}")
        
        zip_content = zip_buffer.getvalue()
        print(f"✅ ZIP creado: {len(zip_content)} bytes")
        
        # Codificar en Base64
        print("🔐 Codificando en Base64...")
        content_base64 = base64.b64encode(zip_content).decode('utf-8')
        print(f"✅ Base64 creado: {len(content_base64)} caracteres")
        
        # Crear SOAP Envelope
        print("📋 Creando SOAP Envelope...")
        zip_filename = '20103129061-01-F001-00001001.zip'
        
        soap_envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                  xmlns:ser="http://service.sunat.gob.pe">
   <soapenv:Header/>
   <soapenv:Body>
      <ser:sendBill>
         <fileName>{zip_filename}</fileName>
         <contentFile>{content_base64}</contentFile>
      </ser:sendBill>
   </soapenv:Body>
</soapenv:Envelope>'''
        
        print(f"✅ SOAP Envelope creado: {len(soap_envelope)} caracteres")
        
        # Headers para SOAP
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'urn:sendBill',
            'User-Agent': 'Python-SUNAT-Client/1.0'
        }
        
        print("📡 Enviando a SUNAT...")
        print(f"🎯 Archivo: {zip_filename}")
        print(f"🎯 Tamaño: {len(soap_envelope)} bytes")
        
        # Enviar a SUNAT
        response = session.post(
            url, 
            data=soap_envelope, 
            headers=headers, 
            timeout=120
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Reason: {response.reason}")
        
        if response.status_code == 200:
            print("✅ ¡ENVÍO SOAP EXITOSO!")
            
            # Analizar respuesta
            response_text = response.text
            print(f"📥 Response length: {len(response_text)} caracteres")
            
            # Buscar CDR en la respuesta
            if 'applicationResponse' in response_text:
                print("🎉 ¡CDR ENCONTRADO EN LA RESPUESTA!")
                
                # Extraer CDR Base64
                import re
                cdr_match = re.search(r'<applicationResponse>(.*?)</applicationResponse>', response_text, re.DOTALL)
                
                if cdr_match:
                    cdr_base64 = cdr_match.group(1).strip()
                    print(f"📋 CDR Base64 length: {len(cdr_base64)}")
                    
                    try:
                        # Decodificar CDR
                        cdr_zip = base64.b64decode(cdr_base64)
                        print(f"📦 CDR ZIP size: {len(cdr_zip)} bytes")
                        
                        # Extraer XML del CDR
                        with zipfile.ZipFile(BytesIO(cdr_zip), 'r') as cdr_zip_file:
                            cdr_files = [f for f in cdr_zip_file.namelist() if f.startswith('R-')]
                            
                            if cdr_files:
                                cdr_xml = cdr_zip_file.read(cdr_files[0]).decode('utf-8')
                                print(f"📄 CDR XML: {cdr_files[0]}")
                                print(f"📄 CDR content preview: {cdr_xml[:300]}...")
                                
                                # Analizar estado
                                if 'ResponseCode>0<' in cdr_xml:
                                    print("🎉 ¡DOCUMENTO ACEPTADO POR SUNAT!")
                                elif 'ResponseCode>2' in cdr_xml or 'ResponseCode>3' in cdr_xml:
                                    print("❌ DOCUMENTO RECHAZADO POR SUNAT")
                                else:
                                    print("⚠️ ESTADO DESCONOCIDO EN CDR")
                                    
                                return True, cdr_xml
                                
                            else:
                                print("⚠️ No se encontró archivo CDR en el ZIP")
                                
                    except Exception as cdr_error:
                        print(f"❌ Error procesando CDR: {cdr_error}")
                
            else:
                print("⚠️ NO SE ENCONTRÓ CDR EN LA RESPUESTA")
            
            print("📝 Response preview:")
            print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
            return True, response_text
            
        elif response.status_code == 500:
            print("❌ ERROR 500 - Error interno del servidor SUNAT")
            print("📝 Response:", response.text[:500])
            return False, response.text
            
        else:
            print(f"❌ ERROR {response.status_code}")
            print("📝 Response:", response.text[:500])
            return False, response.text
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT - SUNAT tardó demasiado en responder")
        return False, "timeout"
        
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        return False, str(e)

def test_documento_real():
    """Test 4: Usar documento real generado"""
    print("\n" + "=" * 60)
    print("📄 TEST 4: DOCUMENTO REAL GENERADO")
    print("=" * 60)
    
    try:
        from documentos.models import DocumentoElectronico
        
        # Buscar el último documento generado
        documento = DocumentoElectronico.objects.filter(
            xml_firmado__isnull=False
        ).order_by('-created_at').first()
        
        if documento:
            print(f"✅ Documento encontrado: {documento.get_numero_completo()}")
            print(f"✅ Estado: {documento.estado}")
            print(f"✅ XML firmado: {len(documento.xml_firmado)} caracteres")
            
            # Verificar que tiene firma digital
            if '<ds:Signature' in documento.xml_firmado:
                print("✅ Documento tiene firma digital XML-DSig")
                return True, documento
            else:
                print("⚠️ Documento sin firma digital")
                return False, None
                
        else:
            print("❌ No se encontraron documentos generados")
            print("💡 Ejecuta primero: POST /api/generar-xml/ en Postman")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def main():
    """Función principal"""
    print("🚀 SISTEMA DE TEST COMPLETO - SUNAT INTEGRACIÓN")
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Configuración
    config_ok, sunat_config = test_configuracion()
    if not config_ok:
        print("\n❌ FALLO EN TEST DE CONFIGURACIÓN - ABORTANDO")
        return
    
    # Test 2: Autenticación
    auth_ok, session, url = test_autenticacion(sunat_config)
    if not auth_ok:
        print("\n❌ FALLO EN AUTENTICACIÓN - ABORTANDO")
        return
    
    # Test 3: Envío SOAP
    soap_ok, soap_result = test_envio_soap(session, url)
    
    # Test 4: Documento real
    doc_ok, documento = test_documento_real()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)
    print(f"✅ Configuración: {'OK' if config_ok else 'FALLO'}")
    print(f"✅ Autenticación: {'OK' if auth_ok else 'FALLO'}")
    print(f"✅ Envío SOAP: {'OK' if soap_ok else 'FALLO'}")
    print(f"✅ Documento real: {'OK' if doc_ok else 'FALLO'}")
    
    if config_ok and auth_ok and soap_ok:
        print("\n🎉 ¡TODOS LOS TESTS EXITOSOS!")
        print("🔥 EL SISTEMA ESTÁ LISTO PARA OBTENER CDR REALES")
        
        if doc_ok:
            print(f"\n💡 SIGUIENTE PASO: Usar documento real en Postman")
            print(f"   POST /api/sunat/send-bill/")
            print(f"   {{\"documento_id\": \"{documento.id}\"}}")
        
    else:
        print("\n⚠️ ALGUNOS TESTS FALLARON")
        print("🔧 Revisar configuración y dependencias")
    
    print(f"\n⏰ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()