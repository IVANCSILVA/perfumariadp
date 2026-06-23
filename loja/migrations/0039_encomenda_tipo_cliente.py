from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0038_merge_20260623_1454'),
    ]

    operations = [
        migrations.AddField(
            model_name='encomenda',
            name='tipo_cliente',
            field=models.CharField(
                choices=[('particular', 'Particular'), ('empresa', 'Empresa')],
                default='particular',
                max_length=10,
                verbose_name='Tipo de Cliente',
            ),
        ),
        migrations.AddField(
            model_name='encomenda',
            name='nome_empresa',
            field=models.CharField(blank=True, max_length=200, verbose_name='Nome da Empresa'),
        ),
        migrations.AddField(
            model_name='encomenda',
            name='nif',
            field=models.CharField(blank=True, max_length=50, verbose_name='NIF'),
        ),
    ]
