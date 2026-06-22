from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0035_migrar_categorias_para_campos_dedicados'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LoteImportacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('referencia', models.CharField(help_text='Ex: "Junho 2025 — Portugal", "Wamos #3"', max_length=100)),
                ('data_encomenda', models.DateField(help_text='Data em que a encomenda foi feita ao fornecedor.')),
                ('cambio', models.DecimalField(decimal_places=2, help_text='Taxa de câmbio do euro para kwanza na data da encomenda (ex: 538,00).', max_digits=10, verbose_name='Câmbio EUR → Kzs')),
                ('custo_transporte_unidade', models.DecimalField(decimal_places=2, help_text='Custo fixo de transporte aplicado a cada unidade do lote (ex: 10 000,00 Kzs).', max_digits=10, verbose_name='Transporte por unidade (Kzs)')),
                ('status', models.CharField(choices=[('em_preparacao', 'Em Preparação'), ('em_transito', 'Em Trânsito'), ('recebido', 'Recebido'), ('parcial', 'Recebido Parcialmente')], default='em_preparacao', max_length=20)),
                ('notas', models.TextField(blank=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('criado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lotes_importacao', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Lote de Importação',
                'verbose_name_plural': 'Lotes de Importação',
                'ordering': ['-data_encomenda'],
            },
        ),
        migrations.CreateModel(
            name='ItemLoteImportacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_produto', models.CharField(help_text='Nome do produto tal como consta na factura do fornecedor.', max_length=200)),
                ('marca', models.CharField(blank=True, max_length=100)),
                ('genero', models.CharField(choices=[('masculino', 'M — Masculino'), ('feminino', 'F — Feminino'), ('unissex', 'U — Unissex')], default='unissex', max_length=20)),
                ('volume_ml', models.CharField(blank=True, help_text='Ex: 100ml, 125ml', max_length=20, verbose_name='Volume (ml)')),
                ('quantidade', models.PositiveIntegerField(default=1)),
                ('preco_compra_eur', models.DecimalField(decimal_places=2, help_text='Preço pago ao fornecedor em euros.', max_digits=10, verbose_name='Preço de compra (€)')),
                ('factor_lucro', models.DecimalField(decimal_places=3, help_text='Factor de divisão para calcular o PVP. Ex: 0,58 → PVP = custo ÷ 0,58 (margem bruta ≈ 42%)', max_digits=5, verbose_name='Factor de lucro')),
                ('recebido', models.BooleanField(default=False, help_text='Marcar quando o produto chegar ao armazém.')),
                ('observacoes', models.CharField(blank=True, max_length=255, verbose_name='Observações')),
                ('lote', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='loja.loteimportacao')),
                ('produto', models.ForeignKey(blank=True, help_text='Produto do catálogo a que este item corresponde (opcional).', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='itens_importacao', to='loja.produto')),
            ],
            options={
                'verbose_name': 'Item de Lote de Importação',
                'verbose_name_plural': 'Itens de Lote de Importação',
                'ordering': ['pk'],
            },
        ),
    ]
