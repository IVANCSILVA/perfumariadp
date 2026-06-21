from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0031_funcionario_banco_nib_iban'),
    ]

    operations = [
        # Atualizar cargos antigos para os novos valores
        migrations.RunSQL(
            sql="""
                UPDATE loja_funcionario SET cargo = 'operador_caixa' WHERE cargo IN ('operador', 'vendedor');
                UPDATE loja_funcionario SET cargo = 'gerente' WHERE cargo = 'gerente';
                UPDATE loja_funcionario SET cargo = 'gerente' WHERE cargo = 'armazem';
                UPDATE loja_funcionario SET percentagem_comissao = 0
                    WHERE cargo NOT IN ('operador_caixa');
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name='funcionario',
            name='cargo',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('gerente', 'Gerente'),
                    ('operador_caixa', 'Operador de Caixa'),
                    ('seguranca', 'Segurança'),
                    ('limpeza', 'Limpeza'),
                ],
                default='operador_caixa',
            ),
        ),
    ]
