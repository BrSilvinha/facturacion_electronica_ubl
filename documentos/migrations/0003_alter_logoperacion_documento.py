# Generated fix for LogOperacion - documentos/migrations/0003_alter_logoperacion_documento.py

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0002_alter_documentolinea_valor_unitario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logoperacion',
            name='documento',
            field=models.ForeignKey(
                blank=True, 
                null=True, 
                on_delete=django.db.models.deletion.CASCADE, 
                related_name='logs', 
                to='documentos.documentoelectronico'
            ),
        ),
    ]