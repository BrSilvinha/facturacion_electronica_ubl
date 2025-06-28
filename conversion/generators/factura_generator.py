from .base_generator import BaseUBLGenerator

class FacturaGenerator(BaseUBLGenerator):
    """Generador específico para Facturas UBL 2.1"""
    
    def get_template_name(self):
        return 'factura.xml'
    
    def get_document_type_code(self):
        return '01'
    
    def _prepare_context(self, documento):
        """Prepara contexto específico para facturas"""
        
        # Obtener contexto base
        context = super()._prepare_context(documento)
        
        # Agregar datos específicos de factura
        context.update({
            'document_name': 'FACTURA ELECTRÓNICA',
            'requires_customer_signature': False,
            'payment_terms': self._get_payment_terms(documento),
            'delivery_terms': self._get_delivery_terms(documento),
        })
        
        return context
    
    def _get_payment_terms(self, documento):
        """Obtiene términos de pago para la factura"""
        
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