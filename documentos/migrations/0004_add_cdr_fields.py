# Generated migration for CDR fields
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0003_alter_logoperacion_documento'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentoelectronico',
            name='cdr_xml',
            field=models.TextField(blank=True, help_text='XML de Constancia de Recepción de SUNAT', null=True),
        ),
        migrations.AddField(
            model_name='documentoelectronico',
            name='cdr_estado',
            field=models.CharField(blank=True, help_text='Estado del CDR: ACEPTADO, ACEPTADO_CON_OBSERVACIONES, RECHAZADO', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='documentoelectronico',
            name='cdr_codigo_respuesta',
            field=models.CharField(blank=True, help_text='Código de respuesta SUNAT (0=aceptado)', max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='documentoelectronico',
            name='cdr_descripcion',
            field=models.TextField(blank=True, help_text='Descripción de la respuesta SUNAT', null=True),
        ),
        migrations.AddField(
            model_name='documentoelectronico',
            name='cdr_observaciones',
            field=models.JSONField(blank=True, help_text='Observaciones del CDR', null=True),
        ),
        migrations.AddField(
            model_name='documentoelectronico',
            name='cdr_fecha_recepcion',
            field=models.DateTimeField(blank=True, help_text='Fecha de recepción del CDR', null=True),
        ),
        migrations.AddField(
            model_name='documentoelectronico',
            name='ticket_sunat',
            field=models.CharField(blank=True, help_text='Ticket de SUNAT para consultas', max_length=100, null=True),
        ),
    ]
