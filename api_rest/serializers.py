from rest_framework import serializers
from documentos.models import Empresa, TipoDocumento, DocumentoElectronico

class ReceptorSerializer(serializers.Serializer):
    """Serializer para datos del receptor"""
    tipo_doc = serializers.CharField(max_length=1)
    numero_doc = serializers.CharField(max_length=15)
    razon_social = serializers.CharField(max_length=100)
    direccion = serializers.CharField(required=False, allow_blank=True)

class ItemSerializer(serializers.Serializer):
    """Serializer para items/líneas del documento"""
    codigo_producto = serializers.CharField(required=False, allow_blank=True)
    descripcion = serializers.CharField(max_length=500)
    unidad_medida = serializers.CharField(default='NIU', max_length=3)
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=3)
    valor_unitario = serializers.DecimalField(max_digits=12, decimal_places=10)
    afectacion_igv = serializers.ChoiceField(
        choices=[
            ('10', 'Gravado - Operación Onerosa'),
            ('20', 'Exonerado - Operación Onerosa'),
            ('30', 'Inafecto - Operación Onerosa'),
            ('40', 'Exportación'),
        ],
        default='10'
    )

class GenerarXMLSerializer(serializers.Serializer):
    """Serializer principal para generar XML UBL 2.1"""
    
    # Datos del documento
    tipo_documento = serializers.CharField(max_length=2)
    serie = serializers.CharField(max_length=4)
    numero = serializers.IntegerField()
    fecha_emision = serializers.DateField()
    fecha_vencimiento = serializers.DateField(required=False)
    moneda = serializers.ChoiceField(
        choices=[('PEN', 'Soles'), ('USD', 'Dólares'), ('EUR', 'Euros')],
        default='PEN'
    )
    
    # Empresa emisora
    empresa_id = serializers.UUIDField()
    
    # Certificado digital (opcional por ahora)
    certificado_id = serializers.UUIDField(required=False)
    
    # Receptor
    receptor = ReceptorSerializer()
    
    # Items
    items = ItemSerializer(many=True)
    
    def validate_empresa_id(self, value):
        """Valida que la empresa exista y esté activa"""
        try:
            empresa = Empresa.objects.get(id=value, activo=True)
            return value
        except Empresa.DoesNotExist:
            raise serializers.ValidationError("Empresa no encontrada o inactiva")
    
    def validate_tipo_documento(self, value):
        """Valida que el tipo de documento exista"""
        try:
            tipo = TipoDocumento.objects.get(codigo=value, activo=True)
            return value
        except TipoDocumento.DoesNotExist:
            raise serializers.ValidationError("Tipo de documento no válido")
    
    def validate_items(self, value):
        """Valida que haya al menos un item"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("Debe incluir al menos un item")
        return value
    
    def validate(self, data):
        """Validaciones adicionales a nivel de objeto"""
        
        # Verificar que no exista documento duplicado
        try:
            existing = DocumentoElectronico.objects.get(
                empresa_id=data['empresa_id'],
                tipo_documento_id=data['tipo_documento'],
                serie=data['serie'],
                numero=data['numero']
            )
            raise serializers.ValidationError({
                'numero': f"Ya existe un documento {data['tipo_documento']}-{data['serie']}-{data['numero']:08d}"
            })
        except DocumentoElectronico.DoesNotExist:
            pass  # Está bien, no existe duplicado
        
        return data

class ValidarRUCSerializer(serializers.Serializer):
    """Serializer para validar RUC"""
    ruc = serializers.CharField(max_length=11, min_length=11)
    
    def validate_ruc(self, value):
        """Valida formato de RUC peruano"""
        if not value.isdigit():
            raise serializers.ValidationError("RUC debe contener solo números")
        
        if len(value) != 11:
            raise serializers.ValidationError("RUC debe tener exactamente 11 dígitos")
        
        return value