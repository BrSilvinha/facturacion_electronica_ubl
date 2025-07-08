from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
import uuid
import json

from documentos.models import (
    Empresa, TipoDocumento, DocumentoElectronico, 
    DocumentoLinea, CertificadoDigital, LogOperacion
)

# Importar nuevo sistema UBL
from conversion.generators import generate_ubl_xml, UBLGeneratorFactory
from conversion.utils.calculations import TributaryCalculator

# IMPORTAR SISTEMA DE FIRMA REAL
from firma_digital import XMLSigner, certificate_manager
from firma_digital.exceptions import DigitalSignatureError, CertificateError, SignatureError

class TestAPIView(APIView):
    """Endpoint de prueba para verificar que la API funciona"""
    
    def get(self, request):
        return Response({
            'message': 'API de Facturación Electrónica UBL 2.1 funcionando correctamente',
            'version': '2.0 - Professional UBL con Certificado Real',
            'timestamp': timezone.now(),
            'supported_documents': UBLGeneratorFactory.get_supported_document_types(),
            'certificate_status': 'Real SUNAT Certificate Integrated',
            'endpoints': [
                '/api/test/',
                '/api/generar-xml/',
                '/api/tipos-documento/',
                '/api/empresas/',
                '/api/validar-ruc/',
                '/api/certificate-info/',  # Nuevo endpoint
            ]
        })

class TiposDocumentoView(APIView):
    """Lista todos los tipos de documento disponibles"""
    
    def get(self, request):
        tipos = TipoDocumento.objects.filter(activo=True).order_by('codigo')
        supported_types = UBLGeneratorFactory.get_supported_document_types()
        
        data = []
        for tipo in tipos:
            tipo_data = {
                'codigo': tipo.codigo,
                'descripcion': tipo.descripcion,
                'soportado': tipo.codigo in supported_types
            }
            data.append(tipo_data)
        
        return Response({
            'success': True,
            'data': data,
            'supported_count': len(supported_types),
            'total_count': len(data)
        })

class EmpresasView(APIView):
    """Lista todas las empresas activas"""
    
    def get(self, request):
        empresas = Empresa.objects.filter(activo=True).order_by('razon_social')
        data = []
        
        for empresa in empresas:
            # Verificar tipo de certificado
            cert_info = self._get_certificate_info_quick(empresa)
            
            empresa_data = {
                'id': str(empresa.id),
                'ruc': empresa.ruc,
                'razon_social': empresa.razon_social,
                'nombre_comercial': empresa.nombre_comercial,
                'certificate_type': cert_info['certificate_type'],
                'is_real_certificate': cert_info['is_real']
            }
            data.append(empresa_data)
        
        return Response({
            'success': True,
            'data': data,
            'real_certificates': sum(1 for d in data if d['is_real_certificate']),
            'test_certificates': sum(1 for d in data if not d['is_real_certificate'])
        })
    
    def _get_certificate_info_quick(self, empresa):
        """Obtiene información rápida del certificado sin cargarlo"""
        ruc_to_cert = {
            '20103129061': {  # TU RUC REAL
                'certificate_type': 'REAL_PRODUCTION',
                'is_real': True
            },
            '20123456789': {
                'certificate_type': 'TEST',
                'is_real': False
            },
            '20987654321': {
                'certificate_type': 'TEST',
                'is_real': False
            }
        }
        
        return ruc_to_cert.get(empresa.ruc, {
            'certificate_type': 'DEFAULT_TEST',
            'is_real': False
        })

class ValidarRUCView(APIView):
    """Valida un RUC peruano con dígito verificador"""
    
    def post(self, request):
        # Obtener datos del request
        try:
            if hasattr(request, 'data') and request.data:
                data = request.data
            else:
                data = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response({
                'success': False,
                'error': 'JSON inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ruc = data.get('ruc', '').strip()
        
        if not ruc:
            return Response({
                'success': False,
                'error': 'RUC es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validación avanzada con dígito verificador
        is_valid, message = TributaryCalculator.validate_ruc(ruc)
        
        if not is_valid:
            return Response({
                'success': False,
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si existe en la base de datos
        try:
            empresa = Empresa.objects.get(ruc=ruc)
            
            # Verificar tipo de certificado
            cert_info = self._get_certificate_info_quick(empresa)
            
            return Response({
                'success': True,
                'valid': True,
                'exists': True,
                'empresa': {
                    'id': str(empresa.id),
                    'ruc': empresa.ruc,
                    'razon_social': empresa.razon_social,
                    'certificate_type': cert_info['certificate_type'],
                    'has_real_certificate': cert_info['is_real']
                }
            })
        except Empresa.DoesNotExist:
            return Response({
                'success': True,
                'valid': True,
                'exists': False,
                'message': 'RUC válido pero no registrado en el sistema'
            })
    
    def _get_certificate_info_quick(self, empresa):
        """Obtiene información rápida del certificado"""
        return EmpresasView()._get_certificate_info_quick(empresa)

class CertificateInfoView(APIView):
    """Endpoint para verificar información de certificados"""
    
    def get(self, request):
        """Listar información de certificados disponibles"""
        
        try:
            empresas = Empresa.objects.filter(activo=True)
            certificates_info = []
            
            for empresa in empresas:
                cert_info = self._get_certificate_info(empresa)
                certificates_info.append(cert_info)
            
            return Response({
                'success': True,
                'certificates': certificates_info,
                'total_real_certificates': sum(1 for c in certificates_info if c['is_real']),
                'total_test_certificates': sum(1 for c in certificates_info if c['is_test']),
                'timestamp': timezone.now()
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Verificar certificado específico por RUC"""
        
        try:
            ruc = request.data.get('ruc')
            if not ruc:
                return Response({
                    'success': False,
                    'error': 'RUC es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            empresa = Empresa.objects.filter(ruc=ruc, activo=True).first()
            if not empresa:
                return Response({
                    'success': False,
                    'error': f'Empresa con RUC {ruc} no encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
            
            cert_info = self._get_certificate_info(empresa)
            
            # Intentar cargar el certificado para verificar que funciona
            try:
                view = GenerarXMLView()
                real_cert_info = view._get_certificate_for_empresa(empresa)
                cert_info['certificate_valid'] = True
                cert_info['certificate_subject'] = real_cert_info['metadata']['subject_cn']
                cert_info['certificate_expires'] = real_cert_info['metadata']['not_after'].isoformat()
                cert_info['key_size'] = real_cert_info['metadata']['key_size']
            except Exception as e:
                cert_info['certificate_valid'] = False
                cert_info['certificate_error'] = str(e)
            
            return Response({
                'success': True,
                'certificate_info': cert_info,
                'timestamp': timezone.now()
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_certificate_info(self, empresa):
        """Obtiene información detallada del certificado"""
        
        ruc_to_cert = {
            '20103129061': {  # TU CERTIFICADO REAL
                'path': 'certificados/production/cert_20103129061.pfx',
                'type': 'REAL_PRODUCTION',
                'description': 'Certificado digital real de SUNAT',
                'password_protected': True
            },
            '20123456789': {
                'path': 'certificados/test/test_cert_empresa1.pfx',
                'type': 'TEST',
                'description': 'Certificado de prueba autofirmado',
                'password_protected': True
            },
            '20987654321': {
                'path': 'certificados/test/test_cert_empresa2.pfx',
                'type': 'TEST', 
                'description': 'Certificado de prueba autofirmado',
                'password_protected': True
            }
        }
        
        cert_config = ruc_to_cert.get(empresa.ruc)
        
        if cert_config:
            return {
                'ruc': empresa.ruc,
                'empresa': empresa.razon_social,
                'certificate_type': cert_config['type'],
                'certificate_path': cert_config['path'],
                'description': cert_config['description'],
                'is_real': cert_config['type'] == 'REAL_PRODUCTION',
                'is_test': cert_config['type'] == 'TEST',
                'password_protected': cert_config['password_protected']
            }
        else:
            return {
                'ruc': empresa.ruc,
                'empresa': empresa.razon_social,
                'certificate_type': 'DEFAULT_TEST',
                'certificate_path': 'certificados/test/test_cert_empresa1.pfx',
                'description': 'Certificado por defecto (prueba)',
                'is_real': False,
                'is_test': True,
                'password_protected': True
            }

class GenerarXMLView(APIView):
    """
    Endpoint principal del reto: Genera XML UBL 2.1 profesional firmado
    VERSIÓN ACTUALIZADA CON CERTIFICADO REAL
    """
    
    def post(self, request):
        try:
            start_time = timezone.now()
            
            # 1. Validar y obtener datos de entrada
            try:
                if hasattr(request, 'data') and request.data:
                    data = request.data
                else:
                    data = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                return Response({
                    'success': False,
                    'error': f'JSON inválido: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validation_result = self._validate_input_data(data)
            
            if not validation_result['valid']:
                return Response({
                    'success': False,
                    'error': validation_result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Obtener empresa y tipo de documento
            empresa = validation_result['empresa']
            tipo_documento = validation_result['tipo_documento']
            
            # 3. Verificar que el tipo de documento esté soportado
            if not UBLGeneratorFactory.is_supported(tipo_documento.codigo):
                return Response({
                    'success': False,
                    'error': f'Tipo de documento {tipo_documento.codigo} no soportado aún. '
                           f'Tipos disponibles: {UBLGeneratorFactory.get_supported_document_types()}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 4. Calcular totales usando calculadora avanzada
            items_calculated = self._calculate_items_with_taxes(data['items'])
            document_totals = TributaryCalculator.calculate_document_totals(items_calculated)
            
            # 5. Crear documento en base de datos
            documento = DocumentoElectronico.objects.create(
                empresa=empresa,
                tipo_documento=tipo_documento,
                serie=data['serie'],
                numero=int(data['numero']),
                receptor_tipo_doc=data['receptor']['tipo_doc'],
                receptor_numero_doc=data['receptor']['numero_doc'],
                receptor_razon_social=data['receptor']['razon_social'],
                receptor_direccion=data['receptor'].get('direccion', ''),
                fecha_emision=data['fecha_emision'],
                fecha_vencimiento=data.get('fecha_vencimiento'),
                moneda=data.get('moneda', 'PEN'),
                subtotal=document_totals['total_valor_venta'],
                igv=document_totals['total_igv'],
                isc=document_totals['total_isc'],
                icbper=document_totals['total_icbper'],
                total=document_totals['total_precio_venta'],
                estado='PENDIENTE',
                datos_json=data
            )
            
            # 6. Crear líneas del documento con cálculos precisos
            for i, item_calc in enumerate(items_calculated, 1):
                DocumentoLinea.objects.create(
                    documento=documento,
                    numero_linea=i,
                    codigo_producto=item_calc.get('codigo_producto', ''),
                    descripcion=item_calc['descripcion'],
                    unidad_medida=item_calc.get('unidad_medida', 'NIU'),
                    cantidad=item_calc['cantidad'],
                    valor_unitario=item_calc['valor_unitario'],
                    valor_venta=item_calc['valor_venta'],
                    afectacion_igv=item_calc['afectacion_igv'],
                    igv_linea=item_calc['igv_monto'],
                    isc_linea=item_calc['isc_monto'],
                    icbper_linea=item_calc['icbper_monto']
                )
            
            # 7. Generar XML UBL 2.1 profesional
            try:
                xml_content = generate_ubl_xml(documento)
                documento.xml_content = xml_content
            except Exception as xml_error:
                return Response({
                    'success': False,
                    'error': f'Error generando XML UBL 2.1: {str(xml_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 8. FIRMA DIGITAL REAL - VERSIÓN MEJORADA
            try:
                print("🔐 Iniciando firma digital con certificado real...")
                
                # Verificar tipo de certificado
                cert_info_quick = self._get_certificate_info_quick(empresa)
                cert_type = "REAL" if cert_info_quick['is_real'] else "PRUEBA"
                
                print(f"📜 Tipo de certificado: {cert_type}")
                
                # Seleccionar certificado según RUC de empresa
                cert_info = self._get_certificate_for_empresa(empresa)
                
                # Firmar con XML-DSig
                signer = XMLSigner()
                xml_firmado = signer.sign_xml_document(xml_content, cert_info)
                
                # Verificar que la firma es válida
                if '<ds:Signature' in xml_firmado and 'ds:SignatureValue' in xml_firmado:
                    print(f"✅ XML firmado digitalmente con certificado {cert_type}")
                    print(f"📜 Certificado: {cert_info['metadata']['subject_cn']}")
                    
                    documento.estado = 'FIRMADO'
                    
                    # Generar hash real del documento firmado
                    import hashlib
                    hash_content = hashlib.sha256(xml_firmado.encode('utf-8')).hexdigest()
                    documento.hash_digest = f'sha256:{hash_content[:32]}'
                    
                else:
                    raise SignatureError("Error: No se detectó firma digital válida en el XML")
                
            except (CertificateError, SignatureError, DigitalSignatureError) as sig_error:
                print(f"⚠️ Error en firma digital: {sig_error}")
                print("📝 Usando simulación como fallback...")
                
                # Fallback a simulación solo si hay error
                xml_firmado = self._simulate_digital_signature(xml_content)
                documento.estado = 'FIRMADO_SIMULADO'
                documento.hash_digest = 'simulado:' + str(uuid.uuid4())[:32]
                
                # Log del error
                LogOperacion.objects.create(
                    documento=documento,
                    operacion='FIRMA',
                    estado='WARNING',
                    mensaje=f'Firma real falló, usando simulación: {str(sig_error)}',
                    duracion_ms=0
                )
            
            except Exception as unexpected_error:
                print(f"❌ Error inesperado en firma: {unexpected_error}")
                return Response({
                    'success': False,
                    'error': f'Error en firma digital: {str(unexpected_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Guardar XML firmado
            documento.xml_firmado = xml_firmado
            documento.save()
            
            # 9. Log de operación con timing
            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            LogOperacion.objects.create(
                documento=documento,
                operacion='CONVERSION',
                estado='SUCCESS',
                mensaje=f'XML UBL 2.1 generado y firmado con certificado {cert_type}',
                duracion_ms=duration_ms
            )
            
            # 10. Respuesta exitosa mejorada
            return Response({
                'success': True,
                'documento_id': str(documento.id),
                'numero_completo': documento.get_numero_completo(),
                'xml_firmado': xml_firmado,
                'hash': documento.hash_digest,
                'estado': documento.estado,
                'signature_type': cert_type,
                'certificate_info': {
                    'subject': cert_info['metadata']['subject_cn'],
                    'expires': cert_info['metadata']['not_after'].isoformat(),
                    'key_size': cert_info['metadata']['key_size'],
                    'is_real': cert_info_quick['is_real']
                },
                'totales': {
                    'subtotal_gravado': float(document_totals['subtotal_gravado']),
                    'subtotal_exonerado': float(document_totals['subtotal_exonerado']),
                    'subtotal_inafecto': float(document_totals['subtotal_inafecto']),
                    'total_valor_venta': float(document_totals['total_valor_venta']),
                    'total_igv': float(document_totals['total_igv']),
                    'total_isc': float(document_totals['total_isc']),
                    'total_icbper': float(document_totals['total_icbper']),
                    'total_precio_venta': float(document_totals['total_precio_venta'])
                },
                'processing_time_ms': duration_ms,
                'generator_version': '2.0-Professional-Real-Certificate',
                'ubl_version': '2.1'
            })
            
        except Exception as e:
            # Log error detallado
            LogOperacion.objects.create(
                documento=None,
                operacion='CONVERSION',
                estado='ERROR',
                mensaje=f'Error generando XML: {str(e)}',
                duracion_ms=0
            )
            
            return Response({
                'success': False,
                'error': f'Error interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_certificate_for_empresa(self, empresa):
        """
        Obtiene certificado apropiado para la empresa
        VERSIÓN ACTUALIZADA - Incluye certificado real
        """
        
        # Mapeo de RUC a certificados - ACTUALIZADO CON CERTIFICADO REAL
        ruc_to_cert = {
            '20103129061': {  # ⭐ TU CERTIFICADO REAL DE PRODUCCIÓN
                'path': 'certificados/production/cert_20103129061.pfx',
                'password': 'Ch14pp32023'  # Tu contraseña real
            },
            '20123456789': {  # Certificado de prueba 1
                'path': 'certificados/test/test_cert_empresa1.pfx',
                'password': 'test123'
            },
            '20987654321': {  # Certificado de prueba 2
                'path': 'certificados/test/test_cert_empresa2.pfx', 
                'password': 'test456'
            }
        }
        
        # Obtener configuración del certificado
        cert_config = ruc_to_cert.get(empresa.ruc)
        
        if not cert_config:
            # Usar certificado por defecto si no hay mapeo específico
            cert_config = {
                'path': 'certificados/test/test_cert_empresa1.pfx',
                'password': 'test123'
            }
            print(f"⚠️ No hay certificado específico para RUC {empresa.ruc}, usando certificado por defecto")
        else:
            # Verificar si es certificado real
            is_real_cert = 'production' in cert_config['path']
            cert_type = "REAL DE PRODUCCIÓN" if is_real_cert else "PRUEBA"
            print(f"✅ Certificado {cert_type} encontrado para RUC {empresa.ruc}")
        
        # Cargar certificado usando certificate_manager
        try:
            cert_info = certificate_manager.get_certificate(
                cert_config['path'], 
                cert_config['password']
            )
            
            # Verificar validez del certificado
            is_real = 'production' in cert_config['path']
            cert_status = "REAL" if is_real else "PRUEBA"
            
            print(f"📜 Certificado {cert_status} cargado para {empresa.ruc}:")
            print(f"    - Sujeto: {cert_info['metadata']['subject_cn']}")
            print(f"    - Válido hasta: {cert_info['metadata']['not_after']}")
            print(f"    - Tipo: {cert_status}")
            
            return cert_info
            
        except Exception as e:
            raise CertificateError(f"Error cargando certificado para {empresa.ruc}: {e}")
    
    def _get_certificate_info_quick(self, empresa):
        """Obtiene información rápida del certificado sin cargarlo"""
        ruc_to_cert = {
            '20103129061': {  # TU RUC REAL
                'certificate_type': 'REAL_PRODUCTION',
                'is_real': True
            },
            '20123456789': {
                'certificate_type': 'TEST',
                'is_real': False
            },
            '20987654321': {
                'certificate_type': 'TEST',
                'is_real': False
            }
        }
        
        return ruc_to_cert.get(empresa.ruc, {
            'certificate_type': 'DEFAULT_TEST',
            'is_real': False
        })
    
    def _validate_input_data(self, data):
        """Valida datos de entrada de forma robusta"""
        
        required_fields = [
            'tipo_documento', 'serie', 'numero', 'fecha_emision',
            'empresa_id', 'receptor', 'items'
        ]
        
        for field in required_fields:
            if field not in data:
                return {
                    'valid': False,
                    'error': f'Campo requerido: {field}'
                }
        
        # Validar empresa
        try:
            empresa = Empresa.objects.get(id=data['empresa_id'], activo=True)
        except Empresa.DoesNotExist:
            return {
                'valid': False,
                'error': 'Empresa no encontrada o inactiva'
            }
        except ValueError:
            return {
                'valid': False,
                'error': f'UUID de empresa inválido: {data["empresa_id"]}'
            }
        
        # Validar tipo de documento
        try:
            tipo_documento = TipoDocumento.objects.get(
                codigo=data['tipo_documento'], 
                activo=True
            )
        except TipoDocumento.DoesNotExist:
            return {
                'valid': False,
                'error': 'Tipo de documento no válido'
            }
        
        # Validar receptor
        receptor = data['receptor']
        required_receptor_fields = ['tipo_doc', 'numero_doc', 'razon_social']
        
        for field in required_receptor_fields:
            if field not in receptor:
                return {
                    'valid': False,
                    'error': f'Campo requerido en receptor: {field}'
                }
        
        # Validar items
        items = data['items']
        if not items or len(items) == 0:
            return {
                'valid': False,
                'error': 'Debe incluir al menos un item'
            }
        
        return {
            'valid': True,
            'empresa': empresa,
            'tipo_documento': tipo_documento
        }
    
    def _calculate_items_with_taxes(self, items):
        """Calcula impuestos para cada item usando calculadora avanzada"""
        
        items_calculated = []
        
        for item in items:
            # Obtener datos del item
            cantidad = Decimal(str(item.get('cantidad', 0)))
            valor_unitario = Decimal(str(item.get('valor_unitario', 0)))
            afectacion_igv = item.get('afectacion_igv', '10')
            aplicar_icbper = item.get('aplicar_icbper', False)
            tasa_isc = Decimal(str(item.get('tasa_isc', 0))) if item.get('tasa_isc') else None
            
            # Calcular usando la calculadora tributaria
            calculo = TributaryCalculator.calculate_line_totals(
                cantidad=cantidad,
                valor_unitario=valor_unitario,
                afectacion_igv=afectacion_igv,
                aplicar_icbper=aplicar_icbper,
                tasa_isc=tasa_isc
            )
            
            # Agregar datos adicionales del item
            calculo.update({
                'codigo_producto': item.get('codigo_producto', ''),
                'descripcion': item['descripcion'],
                'unidad_medida': item.get('unidad_medida', 'NIU')
            })
            
            items_calculated.append(calculo)
        
        return items_calculated
    
    def _simulate_digital_signature(self, xml_content):
        """Simula la firma digital (FALLBACK - solo usar si firma real falla)"""
        
        signature_id = str(uuid.uuid4())[:16]
        timestamp = timezone.now().isoformat()
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- XML UBL 2.1 CON FIRMA SIMULADA - FALLBACK -->
<!-- ADVERTENCIA: Esta es una firma simulada, no válida para producción -->
<!-- Razón: Error cargando certificado real -->
<!-- Generador: Professional UBL Generator v2.0 con Certificado Real -->
<!-- Timestamp: {timestamp} -->
<!-- Signature ID: {signature_id} -->
<!-- RECOMENDACIÓN: Verificar configuración de certificado real -->
{xml_content[xml_content.find('<Invoice'):] if '<Invoice' in xml_content else xml_content}
<!-- FIRMA DIGITAL SIMULADA - HASH: {signature_id} -->'''