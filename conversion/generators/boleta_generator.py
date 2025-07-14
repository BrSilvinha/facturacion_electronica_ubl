# conversion/generators/boleta_generator.py
"""
Generador específico para Boletas UBL 2.1 con soporte completo para todas las afectaciones
Incluye: gravada, exonerada, inafecta, gratuita, bonificación, percepción
"""

from .base_generator import BaseUBLGenerator
from decimal import Decimal

class BoletaGenerator(BaseUBLGenerator):
    """Generador específico para Boletas UBL 2.1"""
    
    def get_template_name(self):
        return 'factura.xml'  # Por ahora usar el mismo template que factura
    
    def get_document_type_code(self):
        return '03'  # Boleta de Venta
    
    def _prepare_context(self, documento):
        """Prepara contexto específico para boletas"""
        
        # Obtener contexto base
        context = super()._prepare_context(documento)
        
        # Agregar datos específicos de boleta
        context.update({
            'document_name': 'BOLETA DE VENTA ELECTRÓNICA',
            'requires_customer_signature': False,
            'payment_terms': self._get_payment_terms_for_boleta(documento),
        })
        
        return context
    
    def _get_payment_terms_for_boleta(self, documento):
        """Obtiene términos de pago para boletas (más simples que facturas)"""
        
        payment_terms = {
            'payment_means_code': '001',  # Efectivo es común en boletas
            'payment_due_date': documento.fecha_emision,  # Boletas generalmente contado
            'payment_amount': documento.total,
            'payment_type': 'Contado'
        }
        
        return payment_terms