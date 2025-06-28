from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

class TributaryCalculator:
    """Calculadora de impuestos según normativas SUNAT"""
    
    # Tasas impositivas vigentes
    IGV_RATE = Decimal('0.18')  # 18%
    ICBPER_RATE = Decimal('0.20')  # S/ 0.20 por unidad
    
    # Códigos de afectación IGV
    AFECTACION_CODES = {
        '10': 'GRAVADO',
        '11': 'GRAVADO_RETIRO_PREMIO',
        '12': 'GRAVADO_RETIRO_DONACION',
        '13': 'GRAVADO_RETIRO_PUBLICIDAD',
        '14': 'GRAVADO_RETIRO_COMISION',
        '15': 'GRAVADO_RETIRO_TRABAJADOR',
        '16': 'GRAVADO_RETIRO_ACCIONISTA',
        '17': 'GRAVADO_OPERACION_ITINERANTE',
        '20': 'EXONERADO',
        '21': 'EXONERADO_TRANSFERENCIA_GRATUITA',
        '30': 'INAFECTO',
        '31': 'INAFECTO_RETIRO_BONIFICACION',
        '32': 'INAFECTO_RETIRO',
        '33': 'INAFECTO_RETIRO_MUESTRAS_MEDICAS',
        '34': 'INAFECTO_RETIRO_CONVENIO_COLECTIVO',
        '35': 'INAFECTO_RETIRO_PREMIO',
        '36': 'INAFECTO_RETIRO_PUBLICIDAD',
        '40': 'EXPORTACION'
    }
    
    @classmethod
    def calculate_line_totals(cls, cantidad: Decimal, valor_unitario: Decimal, 
                             afectacion_igv: str = '10', aplicar_icbper: bool = False,
                             tasa_isc: Decimal = None) -> Dict[str, Decimal]:
        """
        Calcula totales de una línea de documento
        
        Args:
            cantidad: Cantidad del item
            valor_unitario: Valor unitario sin impuestos
            afectacion_igv: Código de afectación IGV
            aplicar_icbper: Si aplica ICBPER (bolsas plásticas)
            tasa_isc: Tasa de ISC si aplica
        
        Returns:
            Dict con todos los cálculos de la línea
        """
        
        # Valor de venta base
        valor_venta = cls._round_currency(cantidad * valor_unitario)
        
        # Calcular IGV
        igv_monto = cls._calculate_igv(valor_venta, afectacion_igv)
        
        # Calcular ISC
        isc_monto = cls._calculate_isc(valor_venta, tasa_isc) if tasa_isc else Decimal('0.00')
        
        # Calcular ICBPER
        icbper_monto = cls._calculate_icbper(cantidad) if aplicar_icbper else Decimal('0.00')
        
        # Precio de venta incluye todos los impuestos
        precio_venta = valor_venta + igv_monto + isc_monto + icbper_monto
        
        return {
            'cantidad': cantidad,
            'valor_unitario': valor_unitario,
            'valor_venta': valor_venta,
            'igv_monto': igv_monto,
            'isc_monto': isc_monto,
            'icbper_monto': icbper_monto,
            'precio_venta': precio_venta,
            'afectacion_igv': afectacion_igv,
            'igv_tasa': cls.IGV_RATE if afectacion_igv in ['10', '11', '12', '13', '14', '15', '16', '17'] else Decimal('0.00'),
            'gravado_igv': afectacion_igv in ['10', '11', '12', '13', '14', '15', '16', '17']
        }
    
    @classmethod
    def calculate_document_totals(cls, lineas_data: List[Dict]) -> Dict[str, Decimal]:
        """
        Calcula totales del documento completo
        
        Args:
            lineas_data: Lista de diccionarios con datos de líneas
        
        Returns:
            Dict con totales del documento
        """
        
        # Inicializar acumuladores
        subtotal_gravado = Decimal('0.00')
        subtotal_exonerado = Decimal('0.00')
        subtotal_inafecto = Decimal('0.00')
        subtotal_exportacion = Decimal('0.00')
        subtotal_gratuito = Decimal('0.00')
        
        total_igv = Decimal('0.00')
        total_isc = Decimal('0.00')
        total_icbper = Decimal('0.00')
        total_otros_tributos = Decimal('0.00')
        
        # Procesar cada línea
        for linea in lineas_data:
            afectacion = linea.get('afectacion_igv', '10')
            valor_venta = linea.get('valor_venta', Decimal('0.00'))
            
            # Clasificar por tipo de afectación
            if afectacion in ['10']:  # Gravado operación onerosa
                subtotal_gravado += valor_venta
            elif afectacion in ['11', '12', '13', '14', '15', '16', '17']:  # Gravado retiros
                subtotal_gratuito += valor_venta
            elif afectacion in ['20', '21']:  # Exonerado
                subtotal_exonerado += valor_venta
            elif afectacion in ['30', '31', '32', '33', '34', '35', '36']:  # Inafecto
                subtotal_inafecto += valor_venta
            elif afectacion == '40':  # Exportación
                subtotal_exportacion += valor_venta
            
            # Acumular impuestos
            total_igv += linea.get('igv_monto', Decimal('0.00'))
            total_isc += linea.get('isc_monto', Decimal('0.00'))
            total_icbper += linea.get('icbper_monto', Decimal('0.00'))
        
        # Calcular totales finales
        total_valor_venta = subtotal_gravado + subtotal_exonerado + subtotal_inafecto + subtotal_exportacion
        total_precio_venta = total_valor_venta + total_igv + total_isc + total_icbper + total_otros_tributos
        
        return {
            # Subtotales por afectación
            'subtotal_gravado': subtotal_gravado,
            'subtotal_exonerado': subtotal_exonerado,
            'subtotal_inafecto': subtotal_inafecto,
            'subtotal_exportacion': subtotal_exportacion,
            'subtotal_gratuito': subtotal_gratuito,
            
            # Totales principales
            'total_valor_venta': total_valor_venta,
            'total_precio_venta': total_precio_venta,
            
            # Impuestos
            'total_igv': total_igv,
            'total_isc': total_isc,
            'total_icbper': total_icbper,
            'total_otros_tributos': total_otros_tributos,
            
            # Otros conceptos
            'total_descuentos': Decimal('0.00'),
            'total_recargos': Decimal('0.00'),
            'redondeo': Decimal('0.00'),
            
            # Importe total
            'importe_total': total_precio_venta
        }
    
    @classmethod
    def _calculate_igv(cls, valor_venta: Decimal, afectacion_igv: str) -> Decimal:
        """Calcula IGV según afectación"""
        
        if afectacion_igv in ['10', '11', '12', '13', '14', '15', '16', '17']:
            # Gravado - aplicar 18%
            igv = valor_venta * cls.IGV_RATE
            return cls._round_currency(igv)
        else:
            # Exonerado, Inafecto o Exportación - IGV = 0
            return Decimal('0.00')
    
    @classmethod
    def _calculate_isc(cls, valor_venta: Decimal, tasa_isc: Decimal) -> Decimal:
        """Calcula ISC según tasa específica"""
        
        if tasa_isc and tasa_isc > 0:
            # ISC puede ser porcentual o por monto fijo
            if tasa_isc < 1:  # Es porcentaje
                isc = valor_venta * tasa_isc
            else:  # Es monto fijo por unidad
                isc = tasa_isc
            
            return cls._round_currency(isc)
        
        return Decimal('0.00')
    
    @classmethod
    def _calculate_icbper(cls, cantidad: Decimal) -> Decimal:
        """Calcula ICBPER (impuesto a bolsas plásticas)"""
        
        # ICBPER es S/ 0.20 por unidad
        icbper = cantidad * cls.ICBPER_RATE
        return cls._round_currency(icbper)
    
    @classmethod
    def _round_currency(cls, amount: Decimal) -> Decimal:
        """Redondea montos según estándares peruanos (2 decimales)"""
        
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @classmethod
    def validate_ruc(cls, ruc: str) -> Tuple[bool, str]:
        """
        Valida RUC peruano con dígito verificador
        
        Args:
            ruc: RUC a validar
        
        Returns:
            Tuple (es_valido, mensaje)
        """
        
        if not ruc or len(ruc) != 11:
            return False, "RUC debe tener 11 dígitos"
        
        if not ruc.isdigit():
            return False, "RUC debe contener solo números"
        
        # Validar dígito verificador
        try:
            digits = [int(d) for d in ruc[:10]]
            factors = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
            
            suma = sum(d * f for d, f in zip(digits, factors))
            residuo = suma % 11
            
            if residuo < 2:
                digito_verificador = residuo
            else:
                digito_verificador = 11 - residuo
            
            if int(ruc[10]) != digito_verificador:
                return False, "Dígito verificador del RUC es incorrecto"
            
        except (ValueError, IndexError):
            return False, "Error en validación del RUC"
        
        return True, "RUC válido"
    
    @classmethod
    def get_tax_description(cls, afectacion_code: str) -> str:
        """Obtiene descripción de código de afectación"""
        
        return cls.AFECTACION_CODES.get(afectacion_code, f"Código {afectacion_code}")
    
    @classmethod
    def calculate_price_with_igv(cls, precio_sin_igv: Decimal, 
                                afectacion_igv: str = '10') -> Dict[str, Decimal]:
        """
        Calcula precio con IGV incluido
        
        Args:
            precio_sin_igv: Precio base sin IGV
            afectacion_igv: Código de afectación
        
        Returns:
            Dict con precios calculados
        """
        
        igv_monto = cls._calculate_igv(precio_sin_igv, afectacion_igv)
        precio_con_igv = precio_sin_igv + igv_monto
        
        return {
            'precio_sin_igv': precio_sin_igv,
            'igv_monto': igv_monto,
            'precio_con_igv': precio_con_igv,
            'igv_tasa': cls.IGV_RATE if afectacion_igv in ['10', '11', '12', '13', '14', '15', '16', '17'] else Decimal('0.00')
        }