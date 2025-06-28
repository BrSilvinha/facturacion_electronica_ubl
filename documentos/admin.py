from django.contrib import admin
from .models import (
    Empresa, TipoDocumento, DocumentoElectronico, 
    DocumentoLinea, CertificadoDigital, LogOperacion
)

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descripcion', 'activo']
    list_filter = ['activo']
    search_fields = ['codigo', 'descripcion']
    ordering = ['codigo']

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['ruc', 'razon_social', 'nombre_comercial', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['ruc', 'razon_social', 'nombre_comercial']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Información Básica', {
            'fields': ('ruc', 'razon_social', 'nombre_comercial')
        }),
        ('Ubicación', {
            'fields': ('direccion', 'ubigeo')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

class DocumentoLineaInline(admin.TabularInline):
    model = DocumentoLinea
    extra = 1
    fields = [
        'numero_linea', 'descripcion', 'cantidad', 
        'valor_unitario', 'valor_venta', 'afectacion_igv'
    ]

@admin.register(DocumentoElectronico)
class DocumentoElectronicoAdmin(admin.ModelAdmin):
    list_display = [
        'get_numero_completo', 'empresa', 'receptor_razon_social', 
        'fecha_emision', 'total', 'estado', 'created_at'
    ]
    list_filter = ['tipo_documento', 'estado', 'moneda', 'fecha_emision']
    search_fields = [
        'serie', 'numero', 'receptor_razon_social', 
        'receptor_numero_doc', 'empresa__ruc'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'hash_digest']
    inlines = [DocumentoLineaInline]
    
    fieldsets = (
        ('Documento', {
            'fields': ('empresa', 'tipo_documento', 'serie', 'numero')
        }),
        ('Receptor', {
            'fields': (
                'receptor_tipo_doc', 'receptor_numero_doc', 
                'receptor_razon_social', 'receptor_direccion'
            )
        }),
        ('Fechas', {
            'fields': ('fecha_emision', 'fecha_vencimiento')
        }),
        ('Montos', {
            'fields': ('moneda', 'subtotal', 'igv', 'isc', 'icbper', 'total')
        }),
        ('XML y Firma', {
            'fields': ('xml_content', 'xml_firmado', 'hash_digest'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('estado', 'datos_json')
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_numero_completo(self, obj):
        return obj.get_numero_completo()
    get_numero_completo.short_description = 'Número Documento'

@admin.register(DocumentoLinea)
class DocumentoLineaAdmin(admin.ModelAdmin):
    list_display = [
        'documento', 'numero_linea', 'descripcion', 
        'cantidad', 'valor_unitario', 'valor_venta'
    ]
    list_filter = ['afectacion_igv', 'unidad_medida']
    search_fields = ['descripcion', 'codigo_producto']
    readonly_fields = ['id', 'created_at']

@admin.register(CertificadoDigital)
class CertificadoDigitalAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'empresa', 'fecha_vencimiento', 'activo', 'created_at']
    list_filter = ['activo', 'fecha_vencimiento']
    search_fields = ['nombre', 'empresa__ruc', 'empresa__razon_social']
    readonly_fields = ['id', 'created_at']

@admin.register(LogOperacion)
class LogOperacionAdmin(admin.ModelAdmin):
    list_display = ['documento', 'operacion', 'estado', 'timestamp', 'duracion_ms']
    list_filter = ['operacion', 'estado', 'timestamp']
    search_fields = ['documento__serie', 'documento__numero', 'mensaje']
    readonly_fields = ['id', 'timestamp', 'correlation_id']
    date_hierarchy = 'timestamp'