from django.core.management.base import BaseCommand
from loja.models import Produto, MovimentoStock


class Command(BaseCommand):
    help = 'Cria movimentos de stock iniciais para produtos que têm stock > 0 sem movimentos registados.'

    def handle(self, *args, **options):
        produtos = Produto.objects.filter(stock__gt=0)
        criados = 0
        for p in produtos:
            if not MovimentoStock.objects.filter(produto=p).exists():
                MovimentoStock.objects.create(
                    produto=p,
                    tipo='entrada',
                    quantidade=p.stock,
                    descricao='Saldo inicial (sincronização)',
                )
                self.stdout.write(self.style.SUCCESS(
                    f'Stock inicial criado para: {p.nome} ({p.stock} un.)'
                ))
                criados += 1
        if criados == 0:
            self.stdout.write(self.style.WARNING(
                'Nenhum produto precisou de sincronização.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'{criados} produto(s) sincronizado(s) com sucesso.'
            ))
