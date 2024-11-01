# Generated by Django 5.1.2 on 2024-11-01 18:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0032_alter_cronograma_horario'),
    ]

    operations = [
        migrations.AddField(
            model_name='cronograma',
            name='paciente',
            field=models.ForeignKey(default='1', on_delete=django.db.models.deletion.PROTECT, to='cadastros.paciente'),
            preserve_default=False,
        ),
    ]
