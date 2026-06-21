from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0029_encomenda_motivo_cancelamento'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='funcionario',
            name='percentagem_comissao',
            field=models.DecimalField(
                decimal_places=2, default=2, max_digits=5,
                verbose_name='Comissão por Vendas (%)',
                help_text='Percentagem do valor total das vendas do mês, adicionada ao salário base. Default: 2%.'
            ),
        ),
        migrations.CreateModel(
            name='PagamentoSalario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mes', models.PositiveSmallIntegerField(
                    choices=[
                        (1,'Janeiro'),(2,'Fevereiro'),(3,'Março'),(4,'Abril'),
                        (5,'Maio'),(6,'Junho'),(7,'Julho'),(8,'Agosto'),
                        (9,'Setembro'),(10,'Outubro'),(11,'Novembro'),(12,'Dezembro'),
                    ],
                    verbose_name='Mês'
                )),
                ('ano', models.PositiveSmallIntegerField(verbose_name='Ano')),
                ('salario_base', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Salário Base (Kz)')),
                ('percentagem_comissao', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='% Comissão (snapshot)')),
                ('total_vendas_mes', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Total de Vendas no Mês (Kz)')),
                ('comissao_valor', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Valor de Comissão (Kz)')),
                ('salario_bruto', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Salário Bruto (Kz)')),
                ('taxa_inss', models.DecimalField(decimal_places=2, default=3, max_digits=5, verbose_name='Taxa INSS Trabalhador (%)')),
                ('desconto_inss', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Desconto INSS (Kz)')),
                ('salario_liquido', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Salário Líquido (Kz)')),
                ('pago', models.BooleanField(default=False, verbose_name='Pago')),
                ('data_pagamento', models.DateField(blank=True, null=True, verbose_name='Data de Pagamento')),
                ('notas', models.TextField(blank=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('funcionario', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='pagamentos_salario',
                    to='loja.funcionario',
                    verbose_name='Funcionário'
                )),
                ('processado_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='salarios_processados',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Processado por'
                )),
            ],
            options={
                'verbose_name': 'Pagamento de Salário',
                'verbose_name_plural': 'Pagamentos de Salários',
                'ordering': ['-ano', '-mes', 'funcionario__nome'],
                'unique_together': {('funcionario', 'mes', 'ano')},
            },
        ),
    ]
