from django.db import migrations


def sincronizar_stock_inicial(apps, schema_editor):
    Produto = apps.get_model('loja', 'Produto')
    MovimentoStock = apps.get_model('loja', 'MovimentoStock')
    for p in Produto.objects.filter(stock__gt=0):
        if not MovimentoStock.objects.filter(produto=p).exists():
            MovimentoStock.objects.create(
                produto=p,
                tipo='entrada',
                quantidade=p.stock,
                descricao='Saldo inicial (sincronização)',
            )


def reverter_sincronizacao(apps, schema_editor):
    MovimentoStock = apps.get_model('loja', 'MovimentoStock')
    MovimentoStock.objects.filter(descricao='Saldo inicial (sincronização)').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('loja', '0047_paypay_substituir_unitel_money'),
    ]
    operations = [
        migrations.RunPython(sincronizar_stock_inicial, reverter_sincronizacao),
    ]
