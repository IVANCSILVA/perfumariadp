from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0032_funcionario_cargo_choices'),
    ]

    operations = [
        # Subsídios no Funcionario
        migrations.AddField(
            model_name='funcionario',
            name='subsidio_alimentacao',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10,
                verbose_name='Subsídio de Alimentação (Kz)',
                help_text='Valor mensal do subsídio de alimentação (não sujeito a INSS nem IRT).',
            ),
        ),
        migrations.AddField(
            model_name='funcionario',
            name='subsidio_transporte',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10,
                verbose_name='Subsídio de Transporte (Kz)',
                help_text='Valor mensal do subsídio de transporte (não sujeito a INSS nem IRT).',
            ),
        ),
        # Novos campos no PagamentoSalario
        migrations.AddField(
            model_name='pagamentosalario',
            name='desconto_irt',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=12,
                verbose_name='IRT (Kz)',
                help_text='Imposto sobre o Rendimento do Trabalho, calculado progressivamente (Tabela A).',
            ),
        ),
        migrations.AddField(
            model_name='pagamentosalario',
            name='subsidio_alimentacao',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10,
                verbose_name='Subsídio de Alimentação (Kz)',
                help_text='Snapshot do subsídio de alimentação na altura do processamento.',
            ),
        ),
        migrations.AddField(
            model_name='pagamentosalario',
            name='subsidio_transporte',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10,
                verbose_name='Subsídio de Transporte (Kz)',
                help_text='Snapshot do subsídio de transporte na altura do processamento.',
            ),
        ),
        migrations.AddField(
            model_name='pagamentosalario',
            name='custo_inss_patronal',
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=12,
                verbose_name='INSS Patronal (Kz)',
                help_text='Contribuição da entidade patronal: 8% do bruto. Custo da empresa.',
            ),
        ),
        migrations.AlterField(
            model_name='pagamentosalario',
            name='salario_liquido',
            field=models.DecimalField(
                decimal_places=2, max_digits=12,
                verbose_name='Salário Líquido (Kz)',
                help_text='Bruto − INSS − IRT + Subsídios.',
            ),
        ),
    ]
