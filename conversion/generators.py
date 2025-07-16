# conversion/generators.py - GENERADORES UBL BÁSICOS

"""
Generadores de XML UBL 2.1 para documentos electrónicos
VERSIÓN BÁSICA - Funcionalidad esencial
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from decimal import Decimal

logger = logging.getLogger('conversion')

def generate_ubl_xml(documento) -> str:
    """
    Función principal para generar XML UBL 2.1
    
    Args:
        documento: Instancia de DocumentoElectronico
        
    Returns:
        XML UBL 2.1 como string
    """
    
    logger.info(f"Generando XML UBL para documento: {documento.get_numero_completo()}")
    
    try:
        # Usar factory para obtener el generador correcto
        generator = UBLGeneratorFactory.get_generator(documento.tipo_documento.codigo)
        
        # Generar XML
        xml_content = generator.generate_xml(documento)
        
        logger.info(f"XML UBL generado exitosamente: {len(xml_content)} caracteres")
        
        return xml_content
        
    except Exception as e:
        logger.error(f"Error generando XML UBL: {e}")
        raise

class UBLGeneratorFactory:
    """Factory para crear generadores UBL según tipo de documento"""
    
    # Tipos de documento soportados
    SUPPORTED_TYPES = {
        '01': 'FacturaGenerator',
        '03': 'BoletaGenerator',
        '07': 'NotaCreditoGenerator',
        '08': 'NotaDebitoGenerator'
    }
    
    @classmethod
    def get_generator(cls, tipo_documento: str):
        """
        Obtiene generador para tipo de documento
        
        Args:
            tipo_documento: Código del tipo de documento
            
        Returns:
            Instancia del generador correspondiente
        """
        
        if tipo_documento not in cls.SUPPORTED_TYPES:
            raise ValueError(f"Tipo de documento no soportado: {tipo_documento}")
        
        generator_class = cls.SUPPORTED_TYPES[tipo_documento]
        
        # Por ahora, todos usan el mismo generador base
        return BaseUBLGenerator()
    
    @classmethod
    def get_supported_document_types(cls) -> List[str]:
        """
        Retorna lista de tipos de documento soportados
        
        Returns:
            Lista de códigos de tipos de documento
        """
        return list(cls.SUPPORTED_TYPES.keys())
    
    @classmethod
    def is_supported(cls, tipo_documento: str) -> bool:
        """
        Verifica si un tipo de documento está soportado
        
        Args:
            tipo_documento: Código del tipo de documento
            
        Returns:
            True si está soportado
        """
        return tipo_documento in cls.SUPPORTED_TYPES

class BaseUBLGenerator:
    """Generador base para documentos UBL 2.1"""
    
    def __init__(self):
        self.ubl_version = "2.1"
        self.customization_id = "2.0"
    
    def generate_xml(self, documento) -> str:
        """
        Genera XML UBL básico
        
        Args:
            documento: Instancia de DocumentoElectronico
            
        Returns:
            XML UBL 2.1 como string
        """
        
        # Determinar tipo de documento
        doc_type = self._get_document_type(documento.tipo_documento.codigo)
        
        # Preparar datos del documento
        document_data = self._prepare_document_data(documento)
        
        # Generar XML según tipo
        if doc_type in ['01', '03']:  # Factura o Boleta
            return self._generate_invoice_xml(document_data)
        elif doc_type == '07':  # Nota de Crédito
            return self._generate_credit_note_xml(document_data)
        elif doc_type == '08':  # Nota de Débito
            return self._generate_debit_note_xml(document_data)
        else:
            raise ValueError(f"Tipo de documento no implementado: {doc_type}")
    
    def _get_document_type(self, codigo: str) -> str:
        """Obtiene tipo de documento"""
        return codigo
    
    def _prepare_document_data(self, documento) -> Dict[str, Any]:
        """
        Prepara datos del documento para el template
        
        Args:
            documento: Instancia de DocumentoElectronico
            
        Returns:
            Dict con datos preparados
        """
        
        # Información básica del documento
        document_id = f"{documento.serie}-{documento.numero:08d}"
        
        # Datos del proveedor (empresa)
        supplier_data = {
            'ruc': documento.empresa.ruc,
            'legal_name': documento.empresa.razon_social,
            'trade_name': documento.empresa.nombre_comercial or documento.empresa.razon_social,
            'address': documento.empresa.direccion,
            'ubigeo': documento.empresa.ubigeo or '150101'
        }
        
        # Datos del cliente
        customer_data = {
            'document_type': documento.receptor_tipo_doc,
            'document_number': documento.receptor_numero_doc,
            'legal_name': documento.receptor_razon_social,
            'address': documento.receptor_direccion or ''
        }
        
        # Líneas del documento
        lines_data = []
        for linea in documento.lineas.all():
            line_data = {
                'id': linea.numero_linea,
                'product_code': linea.codigo_producto or '',
                'description': linea.descripcion,
                'unit_code': linea.unidad_medida,
                'quantity': linea.cantidad,
                'price_amount': linea.valor_unitario,
                'line_extension_amount': linea.valor_venta,
                'base_quantity': linea.cantidad,
                'tax_data': self._prepare_line_tax_data(linea)
            }
            lines_data.append(line_data)
        
        # Totales del documento
        totales_data = {
            'total_valor_venta': documento.subtotal,
            'total_igv': documento.igv,
            'total_isc': documento.isc,
            'total_icbper': documento.icbper,
            'total_precio_venta': documento.total
        }
        
        # Datos de impuestos consolidados
        tax_data = self._prepare_document_tax_data(documento)
        
        return {
            'ubl_version': self.ubl_version,
            'customization_id': self.customization_id,
            'document_id': document_id,
            'document_type_code': documento.tipo_documento.codigo,
            'issue_date': documento.fecha_emision,
            'generation_time': datetime.now(),
            'currency_code': documento.moneda,
            'supplier': supplier_data,
            'customer': customer_data,
            'lines': lines_data,
            'totales': totales_data,
            'tax_data': tax_data,
            'payment_terms': self._prepare_payment_terms(documento)
        }
    
    def _prepare_line_tax_data(self, linea) -> List[Dict[str, Any]]:
        """Prepara datos de impuestos por línea"""
        
        tax_data = []
        
        # IGV
        if linea.igv_linea > 0:
            tax_data.append({
                'tax_id': '1000',
                'tax_name': 'IGV',
                'tax_type_code': 'VAT',
                'tax_category_id': 'S',
                'tax_percentage': 18.00,
                'taxable_amount': linea.valor_venta,
                'tax_amount': linea.igv_linea,
                'exemption_reason_code': linea.afectacion_igv
            })
        else:
            # Sin IGV - determinar razón
            tax_data.append({
                'tax_id': '1000',
                'tax_name': 'IGV',
                'tax_type_code': 'VAT',
                'tax_category_id': 'E' if linea.afectacion_igv == '20' else 'O',
                'tax_percentage': 0.00,
                'taxable_amount': linea.valor_venta,
                'tax_amount': 0.00,
                'exemption_reason_code': linea.afectacion_igv
            })
        
        # ISC (si aplica)
        if linea.isc_linea > 0:
            tax_data.append({
                'tax_id': '2000',
                'tax_name': 'ISC',
                'tax_type_code': 'EXC',
                'tax_category_id': 'S',
                'taxable_amount': linea.valor_venta,
                'tax_amount': linea.isc_linea
            })
        
        # ICBPER (si aplica)
        if linea.icbper_linea > 0:
            tax_data.append({
                'tax_id': '7152',
                'tax_name': 'ICBPER',
                'tax_type_code': 'OTH',
                'tax_category_id': 'S',
                'tax_amount': linea.icbper_linea
            })
        
        return tax_data
    
    def _prepare_document_tax_data(self, documento) -> List[Dict[str, Any]]:
        """Prepara datos de impuestos consolidados del documento"""
        
        tax_data = []
        
        # IGV total
        if documento.igv > 0:
            tax_data.append({
                'tax_id': '1000',
                'tax_name': 'IGV',
                'tax_type_code': 'VAT',
                'tax_amount': documento.igv,
                'taxable_amount': documento.subtotal,
                'tax_percentage': 18.00
            })
        
        # ISC total (si aplica)
        if documento.isc > 0:
            tax_data.append({
                'tax_id': '2000',
                'tax_name': 'ISC',
                'tax_type_code': 'EXC',
                'tax_amount': documento.isc
            })
        
        # ICBPER total (si aplica)
        if documento.icbper > 0:
            tax_data.append({
                'tax_id': '7152',
                'tax_name': 'ICBPER',
                'tax_type_code': 'OTH',
                'tax_amount': documento.icbper
            })
        
        return tax_data
    
    def _prepare_payment_terms(self, documento) -> Dict[str, Any]:
        """Prepara términos de pago"""
        
        payment_terms = {
            'payment_means_code': 'Contado',
            'payment_amount': documento.total
        }
        
        if documento.fecha_vencimiento:
            payment_terms['payment_due_date'] = documento.fecha_vencimiento
        
        return payment_terms
    
    def _generate_invoice_xml(self, data: Dict[str, Any]) -> str:
        """
        Genera XML para factura/boleta básica
        
        Args:
            data: Datos preparados del documento
            
        Returns:
            XML UBL 2.1 como string
        """
        
        # Template básico de factura UBL 2.1
        xml_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
         xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
    
    <ext:UBLExtensions>
        <ext:UBLExtension>
            <ext:ExtensionContent>
            </ext:ExtensionContent>
        </ext:UBLExtension>
    </ext:UBLExtensions>
    
    <cbc:UBLVersionID>{data['ubl_version']}</cbc:UBLVersionID>
    <cbc:CustomizationID>{data['customization_id']}</cbc:CustomizationID>
    <cbc:ProfileID schemeName="SUNAT:Identificador de Tipo de Operación" 
                   schemeAgencyName="PE:SUNAT" 
                   schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo17">0101</cbc:ProfileID>
    <cbc:ID>{data['document_id']}</cbc:ID>
    <cbc:IssueDate>{data['issue_date'].strftime('%Y-%m-%d')}</cbc:IssueDate>
    <cbc:IssueTime>{data['generation_time'].strftime('%H:%M:%S')}</cbc:IssueTime>
    <cbc:InvoiceTypeCode listAgencyName="PE:SUNAT" 
                        listName="SUNAT:Identificador de Tipo de Documento" 
                        listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01">{data['document_type_code']}</cbc:InvoiceTypeCode>
    <cbc:Note languageLocaleID="1000">{self._format_decimal(data['totales']['total_precio_venta'])}</cbc:Note>
    <cbc:DocumentCurrencyCode listID="ISO 4217 Alpha" 
                              listName="Currency" 
                              listAgencyName="United Nations Economic Commission for Europe">{data['currency_code']}</cbc:DocumentCurrencyCode>
    
    <cac:Signature>
        <cbc:ID>SignatureSP</cbc:ID>
        <cac:SignatoryParty>
            <cac:PartyIdentification>
                <cbc:ID>{data['supplier']['ruc']}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name><![CDATA[{data['supplier']['legal_name']}]]></cbc:Name>
            </cac:PartyName>
        </cac:SignatoryParty>
        <cac:DigitalSignatureAttachment>
            <cac:ExternalReference>
                <cbc:URI>#SignatureSP</cbc:URI>
            </cac:ExternalReference>
        </cac:DigitalSignatureAttachment>
    </cac:Signature>
    
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6" 
                        schemeName="Documento de Identidad" 
                        schemeAgencyName="PE:SUNAT" 
                        schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06">{data['supplier']['ruc']}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name><![CDATA[{data['supplier']['trade_name']}]]></cbc:Name>
            </cac:PartyName>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[{data['supplier']['legal_name']}]]></cbc:RegistrationName>
                <cac:RegistrationAddress>
                    <cbc:ID schemeAgencyName="PE:INEI">{data['supplier']['ubigeo']}</cbc:ID>
                    <cbc:AddressTypeCode listAgencyName="PE:SUNAT" 
                                         listName="Establecimientos anexos">0000</cbc:AddressTypeCode>
                    <cbc:CitySubdivisionName>-</cbc:CitySubdivisionName>
                    <cbc:CityName>-</cbc:CityName>
                    <cbc:CountrySubentity>-</cbc:CountrySubentity>
                    <cbc:District>-</cbc:District>
                    <cac:AddressLine>
                        <cbc:Line><![CDATA[{data['supplier']['address']}]]></cbc:Line>
                    </cac:AddressLine>
                    <cac:Country>
                        <cbc:IdentificationCode listAgencyName="United Nations Economic Commission for Europe" 
                                                listName="Country" 
                                                listID="ISO 3166-1">PE</cbc:IdentificationCode>
                    </cac:Country>
                </cac:RegistrationAddress>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
    
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="{data['customer']['document_type']}" 
                        schemeName="Documento de Identidad" 
                        schemeAgencyName="PE:SUNAT" 
                        schemeURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06">{data['customer']['document_number']}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[{data['customer']['legal_name']}]]></cbc:RegistrationName>
                {self._format_customer_address(data['customer'])}
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
    
    {self._format_tax_totals(data['tax_data'], data['currency_code'])}
    
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="{data['currency_code']}">{self._format_decimal(data['totales']['total_valor_venta'])}</cbc:LineExtensionAmount>
        <cbc:TaxInclusiveAmount currencyID="{data['currency_code']}">{self._format_decimal(data['totales']['total_precio_venta'])}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="{data['currency_code']}">{self._format_decimal(data['totales']['total_precio_venta'])}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    
    {self._format_invoice_lines(data['lines'], data['currency_code'])}
    
</Invoice>'''
        
        return xml_template
    
    def _generate_credit_note_xml(self, data: Dict[str, Any]) -> str:
        """Genera XML para nota de crédito (placeholder)"""
        return self._generate_invoice_xml(data).replace('<Invoice', '<CreditNote').replace('</Invoice>', '</CreditNote>')
    
    def _generate_debit_note_xml(self, data: Dict[str, Any]) -> str:
        """Genera XML para nota de débito (placeholder)"""
        return self._generate_invoice_xml(data).replace('<Invoice', '<DebitNote').replace('</Invoice>', '</DebitNote>')
    
    def _format_decimal(self, value) -> str:
        """Formatea valor decimal para XML"""
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        return f"{value:.2f}"
    
    def _format_customer_address(self, customer_data: Dict[str, Any]) -> str:
        """Formatea dirección del cliente"""
        if customer_data.get('address'):
            return f'''<cac:RegistrationAddress>
                    <cac:AddressLine>
                        <cbc:Line><![CDATA[{customer_data['address']}]]></cbc:Line>
                    </cac:AddressLine>
                </cac:RegistrationAddress>'''
        return ''
    
    def _format_tax_totals(self, tax_data: List[Dict], currency_code: str) -> str:
        """Formatea totales de impuestos"""
        tax_xml = ''
        
        for tax in tax_data:
            tax_xml += f'''
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="{currency_code}">{self._format_decimal(tax['tax_amount'])}</cbc:TaxAmount>
        <cac:TaxSubtotal>
            {f'<cbc:TaxableAmount currencyID="{currency_code}">{self._format_decimal(tax.get("taxable_amount", 0))}</cbc:TaxableAmount>' if tax.get('taxable_amount') else ''}
            <cbc:TaxAmount currencyID="{currency_code}">{self._format_decimal(tax['tax_amount'])}</cbc:TaxAmount>
            <cac:TaxCategory>
                <cbc:ID schemeID="UN/ECE 5305" 
                        schemeName="Tax Category Identifier" 
                        schemeAgencyName="United Nations Economic Commission for Europe">S</cbc:ID>
                {f'<cbc:Percent>{self._format_decimal(tax.get("tax_percentage", 0))}</cbc:Percent>' if tax.get('tax_percentage') else ''}
                <cac:TaxScheme>
                    <cbc:ID schemeID="UN/ECE 5153" 
                            schemeAgencyID="6">{tax['tax_id']}</cbc:ID>
                    <cbc:Name>{tax['tax_name']}</cbc:Name>
                    <cbc:TaxTypeCode>{tax['tax_type_code']}</cbc:TaxTypeCode>
                </cac:TaxScheme>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>'''
        
        return tax_xml
    
    def _format_invoice_lines(self, lines_data: List[Dict], currency_code: str) -> str:
        """Formatea líneas del documento"""
        lines_xml = ''
        
        for line in lines_data:
            lines_xml += f'''
    <cac:InvoiceLine>
        <cbc:ID>{line['id']}</cbc:ID>
        <cbc:InvoicedQuantity unitCode="{line['unit_code']}" 
                              unitCodeListID="UN/ECE rec 20" 
                              unitCodeListAgencyName="United Nations Economic Commission for Europe">{self._format_decimal(line['quantity'])}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="{currency_code}">{self._format_decimal(line['line_extension_amount'])}</cbc:LineExtensionAmount>
        
        <cac:PricingReference>
            <cac:AlternativeConditionPrice>
                <cbc:PriceAmount currencyID="{currency_code}">{self._format_decimal(line['line_extension_amount'] + sum(tax.get('tax_amount', 0) for tax in line.get('tax_data', [])))}</cbc:PriceAmount>
                <cbc:PriceTypeCode listName="SUNAT:Indicador de Tipo de Precio" 
                                   listAgencyName="PE:SUNAT" 
                                   listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16">01</cbc:PriceTypeCode>
            </cac:AlternativeConditionPrice>
        </cac:PricingReference>
        
        {self._format_line_tax_data(line.get('tax_data', []), currency_code)}
        
        <cac:Item>
            <cbc:Description><![CDATA[{line['description']}]]></cbc:Description>
            {f'<cac:SellersItemIdentification><cbc:ID>{line["product_code"]}</cbc:ID></cac:SellersItemIdentification>' if line.get('product_code') else ''}
        </cac:Item>
        
        <cac:Price>
            <cbc:PriceAmount currencyID="{currency_code}">{self._format_decimal(line['price_amount'])}</cbc:PriceAmount>
            <cbc:BaseQuantity unitCode="{line['unit_code']}">{self._format_decimal(line['base_quantity'])}</cbc:BaseQuantity>
        </cac:Price>
    </cac:InvoiceLine>'''
        
        return lines_xml
    
    def _format_line_tax_data(self, tax_data: List[Dict], currency_code: str) -> str:
        """Formatea datos de impuestos por línea"""
        tax_xml = ''
        
        for tax in tax_data:
            tax_xml += f'''
        <cac:TaxTotal>
            <cbc:TaxAmount currencyID="{currency_code}">{self._format_decimal(tax['tax_amount'])}</cbc:TaxAmount>
            <cac:TaxSubtotal>
                {f'<cbc:TaxableAmount currencyID="{currency_code}">{self._format_decimal(tax.get("taxable_amount", 0))}</cbc:TaxableAmount>' if tax.get('taxable_amount') else ''}
                <cbc:TaxAmount currencyID="{currency_code}">{self._format_decimal(tax['tax_amount'])}</cbc:TaxAmount>
                <cac:TaxCategory>
                    <cbc:ID schemeID="UN/ECE 5305" 
                            schemeName="Tax Category Identifier" 
                            schemeAgencyName="United Nations Economic Commission for Europe">{tax['tax_category_id']}</cbc:ID>
                    {f'<cbc:Percent>{self._format_decimal(tax.get("tax_percentage", 0))}</cbc:Percent>' if tax.get('tax_percentage') else ''}
                    {f'<cbc:TaxExemptionReasonCode listAgencyName="PE:SUNAT" listName="SUNAT:Codigo de Tipo de Afectación del IGV" listURI="urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07">{tax.get("exemption_reason_code", "")}</cbc:TaxExemptionReasonCode>' if tax.get('exemption_reason_code') else ''}
                    <cac:TaxScheme>
                        <cbc:ID schemeID="UN/ECE 5153" 
                                schemeAgencyID="6">{tax['tax_id']}</cbc:ID>
                        <cbc:Name>{tax['tax_name']}</cbc:Name>
                        <cbc:TaxTypeCode>{tax['tax_type_code']}</cbc:TaxTypeCode>
                    </cac:TaxScheme>
                </cac:TaxCategory>
            </cac:TaxSubtotal>
        </cac:TaxTotal>'''
        
        return tax_xml