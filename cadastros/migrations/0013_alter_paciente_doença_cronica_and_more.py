# Generated by Django 4.2.7 on 2023-11-24 18:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0012_rename_orario_cronograma_horario_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paciente',
            name='doença_cronica',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='doença_cronica'),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='sintomas',
            field=models.CharField(max_length=150, verbose_name='simtomas'),
        ),
    ]
