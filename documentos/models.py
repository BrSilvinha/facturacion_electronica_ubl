from django.db import models
from django.core.validators import RegexValidator
import uuid

class Empresa(models.Model):
    """Modelo para empresas emisoras de documentos electrónicos"""
    
    # Validador para RUC peruano (11 dígitos)
    ruc_validator = RegexValidator(
        regex=r'^\d{11}$',
        message='El RUC debe tener exactamente 11 dígitos'
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruc = models.CharField(max_length=11, unique=True, validators=[ruc_validator])
    razon_social = models.CharField(max_length=100)
    nombre_comercial = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.TextField()
    ubigeo = models.CharField(max_length=6, blank=True, null=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'empresas'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
    
    def __str__(self):
        return f"{self.ruc} - {self.razon_social}"


class TipoDocumento(models.Model):
    """Catálogo de tipos de documentos según SUNAT"""
    
    codigo = models.CharField(max_length=2, primary_key=True)  # 01, 03, 07, 08
    descripcion = models.CharField(max_length=50)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'tipos_documento'
        verbose_name = 'Tipo de Documento'
        verbose_name_plural = 'Tipos de Documento'
    
    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class DocumentoElectronico(models.Model):
    """Modelo principal para documentos electrónicos"""
    
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('PENDIENTE', 'Pendiente de Firma'),
        ('FIRMADO', 'Firmado'),
        ('FIRMADO_SIMULADO', 'Firmado Simulado'),
        ('ENVIADO', 'Enviado a SUNAT'),
        ('ACEPTADO', 'Aceptado por SUNAT'),
        ('RECHAZADO', 'Rechazado'),
        ('ERROR', 'Error en Procesamiento'),
    ]
    
    MONEDAS = [
        ('PEN', 'Soles'),
        ('USD', 'Dólares'),
        ('EUR', 'Euros'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)
    serie = models.CharField(max_length=4)  # F001, B001, etc.
    numero = models.IntegerField()
    
    # Datos del receptor
    receptor_tipo_doc = models.CharField(max_length=1, default='6')  # 6=RUC, 1=DNI
    receptor_numero_doc = models.CharField(max_length=15)
    receptor_razon_social = models.CharField(max_length=100)
    receptor_direccion = models.TextField(blank=True, null=True)
    
    # Fechas
    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField(blank=True, null=True)
    
    # Montos
    moneda = models.CharField(max_length=3, choices=MONEDAS, default='PEN')
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    igv = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    isc = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    icbper = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # XML y Firma
    xml_content = models.TextField(blank=True, null=True)  # XML UBL 2.1 generado
    xml_firmado = models.TextField(blank=True, null=True)  # XML con firma digital
    hash_digest = models.CharField(max_length=255, blank=True, null=True)
    
    # Estado y auditoría
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    datos_json = models.JSONField(blank=True, null=True)  # Datos originales
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documentos_electronicos'
        verbose_name = 'Documento Electrónico'
        verbose_name_plural = 'Documentos Electrónicos'
        unique_together = ['empresa', 'tipo_documento', 'serie', 'numero']
    
    def __str__(self):
        return f"{self.tipo_documento.codigo}-{self.serie}-{self.numero:08d}"
    
    def get_numero_completo(self):
        """Retorna el número completo del documento"""
        return f"{self.tipo_documento.codigo}-{self.serie}-{self.numero:08d}"


class DocumentoLinea(models.Model):
    """Líneas/items de los documentos electrónicos"""
    
    AFECTACIONES_IGV = [
        ('10', 'Gravado - Operación Onerosa'),
        ('11', 'Gravado - Retiro por premio'),
        ('12', 'Gravado - Retiro por donación'),
        ('20', 'Exonerado - Operación Onerosa'),
        ('30', 'Inafecto - Operación Onerosa'),
        ('40', 'Exportación'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    documento = models.ForeignKey(DocumentoElectronico, on_delete=models.CASCADE, related_name='lineas')
    numero_linea = models.IntegerField()
    
    # Producto/Servicio
    codigo_producto = models.CharField(max_length=30, blank=True, null=True)
    descripcion = models.TextField()
    unidad_medida = models.CharField(max_length=3, default='NIU')  # Catálogo SUNAT 03
    
    # Cantidades y precios
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=2)
    valor_venta = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Impuestos
    afectacion_igv = models.CharField(max_length=2, choices=AFECTACIONES_IGV, default='10')
    igv_linea = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    isc_linea = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    icbper_linea = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documento_lineas'
        verbose_name = 'Línea de Documento'
        verbose_name_plural = 'Líneas de Documento'
        ordering = ['numero_linea']
    
    def __str__(self):
        return f"Línea {self.numero_linea}: {self.descripcion[:50]}"


class CertificadoDigital(models.Model):
    """Certificados digitales para firma electrónica"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='certificados')
    nombre = models.CharField(max_length=100)
    archivo_pfx = models.FileField(upload_to='certificados/')
    password_hash = models.CharField(max_length=255)  # Password encriptado
    fecha_vencimiento = models.DateField()
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'certificados_digitales'
        verbose_name = 'Certificado Digital'
        verbose_name_plural = 'Certificados Digitales'
    
    def __str__(self):
        return f"{self.nombre} - {self.empresa.ruc}"


class LogOperacion(models.Model):
    """Log de operaciones del sistema"""
    
    TIPOS_OPERACION = [
        ('CONVERSION', 'Conversión a UBL'),
        ('FIRMA', 'Firma Digital'),
        ('ENVIO', 'Envío a SUNAT'),
        ('VALIDACION', 'Validación'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    documento = models.ForeignKey(
        DocumentoElectronico, 
        on_delete=models.CASCADE, 
        related_name='logs',
        blank=True,
        null=True
    )
    operacion = models.CharField(max_length=20, choices=TIPOS_OPERACION)
    timestamp = models.DateTimeField(auto_now_add=True)
    duracion_ms = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    mensaje = models.TextField(blank=True, null=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)
    
    class Meta:
        db_table = 'logs_operaciones'
        verbose_name = 'Log de Operación'
        verbose_name_plural = 'Logs de Operaciones'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.operacion} - {self.estado} - {self.timestamp}"