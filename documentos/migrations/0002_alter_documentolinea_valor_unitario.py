# Generated by Django 5.2.1 on 2025-06-28 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentolinea',
            name='valor_unitario',
            field=models.DecimalField(decimal_places=2, max_digits=15),
        ),
    ]
