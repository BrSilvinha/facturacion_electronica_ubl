# conversion/generators/__init__.py - ARCHIVO CORREGIDO SIN IMPORTACIONES CIRCULARES
"""
Factory actualizado para incluir generador de boletas
CORREGIDO: Sin importaciones circulares
"""

from .base_generator import BaseUBLGenerator
from .factura_generator import FacturaGenerator

# Importar BoletaGenerator solo si existe el archivo
try:
    from .boleta_generator import BoletaGenerator
    BOLETA_GENERATOR_AVAILABLE = True
except ImportError:
    BOLETA_GENERATOR_AVAILABLE = False
    print("⚠️ BoletaGenerator no disponible - crear archivo boleta_generator.py")

class UBLGeneratorFactory:
    """Factory para crear generadores UBL según tipo de documento"""
    
    _generators = {
        '01': FacturaGenerator,  # Factura
        # '03': BoletaGenerator,   # Boleta - Se agregará dinámicamente
        # '07': NotaCreditoGenerator,   # Nota de Crédito (implementar después)
        # '08': NotaDebitoGenerator,    # Nota de Débito (implementar después)
    }
    
    # Agregar BoletaGenerator si está disponible
    if BOLETA_GENERATOR_AVAILABLE:
        _generators['03'] = BoletaGenerator
    
    @classmethod
    def create_generator(cls, tipo_documento: str) -> BaseUBLGenerator:
        """
        Crea el generador apropiado según tipo de documento
        
        Args:
            tipo_documento: Código del tipo de documento (01, 03, 07, 08)
        
        Returns:
            Instancia del generador apropiado
        
        Raises:
            ValueError: Si el tipo de documento no está soportado
        """
        
        generator_class = cls._generators.get(tipo_documento)
        
        if not generator_class:
            raise ValueError(f"Tipo de documento '{tipo_documento}' no soportado. "
                           f"Tipos disponibles: {list(cls._generators.keys())}")
        
        return generator_class()
    
    @classmethod
    def get_supported_document_types(cls) -> list:
        """Retorna lista de tipos de documento soportados"""
        return list(cls._generators.keys())
    
    @classmethod
    def is_supported(cls, tipo_documento: str) -> bool:
        """Verifica si un tipo de documento está soportado"""
        return tipo_documento in cls._generators
    
    @classmethod
    def register_generator(cls, tipo_documento: str, generator_class):
        """
        Registra un nuevo generador para un tipo de documento
        
        Args:
            tipo_documento: Código del tipo de documento
            generator_class: Clase del generador que hereda de BaseUBLGenerator
        """
        
        if not issubclass(generator_class, BaseUBLGenerator):
            raise TypeError("Generator class must inherit from BaseUBLGenerator")
        
        cls._generators[tipo_documento] = generator_class

# Funciones de conveniencia
def generate_ubl_xml(documento) -> str:
    """
    Genera XML UBL 2.1 para un documento
    
    Args:
        documento: Instancia de DocumentoElectronico
    
    Returns:
        String con XML UBL 2.1 generado
    
    Raises:
        ValueError: Si el tipo de documento no está soportado
    """
    
    generator = UBLGeneratorFactory.create_generator(documento.tipo_documento.codigo)
    return generator.generate_xml(documento)

def get_available_generators() -> dict:
    """Retorna diccionario con generadores disponibles"""
    return UBLGeneratorFactory._generators.copy()