# Generated migration for missing fields
# Archivo: documentos/migrations/0005_add_missing_fields.py

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0004_add_cdr_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentoelectronico',
            name='numero_ticket',
            field=models.CharField(blank=True, help_text='Ticket de SUNAT para consultas posteriores', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='documentoelectronico',
            name='correlation_id',
            field=models.CharField(blank=True, help_text='ID de correlación para trazabilidad', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='documentoelectronico',
            name='last_sunat_response',
            field=models.TextField(blank=True, help_text='Última respuesta de SUNAT', null=True),
        ),
        migrations.AddField(
            model_name='logoperacion',
            name='resultado',
            field=models.CharField(blank=True, help_text='Resultado de la operación', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='logoperacion',
            name='detalles',
            field=models.TextField(blank=True, help_text='Detalles adicionales de la operación', null=True),
        ),
    ]