from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0015_movimentocaixa_encomenda'),
    ]

    operations = [
        migrations.RenameField(
            model_name='produto',
            old_name='preco',
            new_name='preco_venda',
        ),
        migrations.AlterField(
            model_name='produto',
            name='preco_venda',
            field=models.DecimalField(
                decimal_places=2, max_digits=10,
                help_text='Preço de venda ao cliente (Kz)',
            ),
        ),
        migrations.AddField(
            model_name='produto',
            name='preco_compra',
            field=models.DecimalField(
                decimal_places=2, max_digits=10, default=0,
                help_text='Preço de custo / compra ao fornecedor (Kz)',
            ),
        ),
        migrations.AddField(
            model_name='itemencomenda',
            name='preco_custo_unitario',
            field=models.DecimalField(
                decimal_places=2, max_digits=10, default=0,
                help_text='Snapshot do preço de compra na altura da venda (para cálculo de lucro).',
            ),
        ),
    ]
