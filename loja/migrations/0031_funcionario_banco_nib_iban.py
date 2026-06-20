from django.db import migrations, models
import loja.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0030_funcionario_percentagem_comissao_pagamentosalario'),
    ]

    operations = [
        migrations.AddField(
            model_name='funcionario',
            name='banco',
            field=models.CharField(
                blank=True, max_length=20,
                verbose_name='Banco',
                help_text='Banco onde o funcionário recebe o salário.',
                choices=[
                    ('bai', 'BAI — Banco Angolano de Investimentos'),
                    ('bic', 'BIC — Banco BIC'),
                    ('bfa', 'BFA — Banco de Fomento Angola'),
                    ('atlantico', 'Banco Atlântico'),
                    ('bci', 'BCI — Banco de Crédito Investimento'),
                    ('millennium', 'Millennium Atlântico'),
                    ('sol', 'Banco SOL'),
                    ('caixanga', 'Caixa Geral — Angola'),
                    ('keve', 'Banco Keve'),
                    ('yetu', 'Banco Yetu'),
                    ('standard', 'Standard Bank Angola'),
                    ('vtb', 'VTB Bank Angola'),
                    ('otro', 'Outro'),
                ],
            ),
        ),
        migrations.AddField(
            model_name='funcionario',
            name='nib',
            field=models.CharField(
                blank=True, max_length=21,
                verbose_name='NIB (21 dígitos)',
                help_text='Número de Identificação Bancária: 21 dígitos (ex: 004400006729503010102).',
                validators=[loja.utils.validators.validar_nib_angola],
            ),
        ),
        migrations.AddField(
            model_name='funcionario',
            name='iban',
            field=models.CharField(
                blank=True, max_length=25,
                verbose_name='IBAN',
                help_text='IBAN angolano: AO + 23 dígitos, total 25 caracteres (ex: AO06004400006729503010102).',
                validators=[loja.utils.validators.validar_iban_angola],
            ),
        ),
    ]
