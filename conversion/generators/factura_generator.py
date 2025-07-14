# conversion/generators/factura_generator.py - VERSIÓN CORREGIDA

from .base_generator import BaseUBLGenerator

class FacturaGenerator(BaseUBLGenerator):
    """Generador específico para Facturas UBL 2.1 - CORREGIDO para SUNAT"""
    
    def get_template_name(self):
        return 'factura.xml'
    
    def get_document_type_code(self):
        return '01'
    
    def _prepare_context(self, documento):
        """Prepara contexto específico para facturas - CORREGIDO"""
        
        # Obtener contexto base
        context = super()._prepare_context(documento)
        
        # Agregar datos específicos de factura
        context.update({
            'document_name': 'FACTURA ELECTRÓNICA',
            'requires_customer_signature': False,
            'payment_terms': self._get_payment_terms(documento),
            'delivery_terms': self._get_delivery_terms(documento),
        })
        
        # 🚀 VALIDACIÓN ADICIONAL: Verificar datos críticos para SUNAT
        self._validate_factura_specific_data(context, documento)
        
        return context
    
    def _validate_factura_specific_data(self, context, documento):
        """Validaciones específicas para facturas SUNAT"""
        
        # Validar que el receptor tenga RUC (para facturas)
        if documento.receptor_tipo_doc != '6':
            # Para facturas, generalmente se requiere RUC del cliente
            # Pero permitimos otros tipos de documento
            pass
        
        # Validar que el receptor tenga documento válido
        receptor_doc = documento.receptor_numero_doc
        if documento.receptor_tipo_doc == '6':  # RUC
            if not receptor_doc or len(receptor_doc) != 11 or not receptor_doc.isdigit():
                raise ValueError(f"RUC del receptor inválido para factura: {receptor_doc}")
        elif documento.receptor_tipo_doc == '1':  # DNI
            if not receptor_doc or len(receptor_doc) != 8 or not receptor_doc.isdigit():
                raise ValueError(f"DNI del receptor inválido para factura: {receptor_doc}")
        
        # Validar montos mínimos
        if documento.total <= 0:
            raise ValueError("El total de la factura debe ser mayor a 0")
        
        # Validar que tenga al menos una línea
        if not documento.lineas.exists():
            raise ValueError("La factura debe tener al menos una línea de detalle")
    
    def _get_payment_terms(self, documento):
        """Obtiene términos de pago para la factura - CORREGIDO"""
        
        payment_terms = {
            'payment_means_code': '001',  # Depósito en cuenta
            'payment_due_date': documento.fecha_vencimiento,
            'payment_amount': documento.total
        }
        
        # Si hay fecha de vencimiento, es crédito
        if documento.fecha_vencimiento and documento.fecha_vencimiento != documento.fecha_emision:
            payment_terms.update({
                'payment_type': 'Crédito',
                'payment_means_code': '001'
            })
        else:
            payment_terms.update({
                'payment_type': 'Contado',
                'payment_means_code': '000'
            })
        
        return payment_terms
    
    def _get_delivery_terms(self, documento):
        """Obtiene términos de entrega (opcional para facturas)"""
        
        return {
            'delivery_location': documento.receptor_direccion or '',
            'delivery_date': documento.fecha_emision,
            'delivery_terms_code': '01'  # Entrega en dirección del comprador
        }