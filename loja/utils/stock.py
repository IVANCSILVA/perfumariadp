from loja.models import MovimentoStock


def reverter_stock_encomenda(encomenda, user=None, descricao_prefixo='Cancelamento'):
    """Revert stock for all items of a cancelled order and log the movements.

    Restores ``item.produto.stock`` and creates ``MovimentoStock`` entries of
    type ``devolucao`` for each item linked to a product.
    """
    criado_por = user if user and user.is_authenticated else None
    for item in encomenda.itens.select_related('produto').all():
        if item.produto:
            MovimentoStock.objects.create(
                produto=item.produto,
                tipo='devolucao',
                quantidade=item.quantidade,
                descricao=f'{descricao_prefixo} de Venda #{encomenda.pk}',
                encomenda=encomenda,
                criado_por=criado_por,
            )
