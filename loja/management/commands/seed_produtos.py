from django.core.management.base import BaseCommand
from loja.models import Categoria, Produto
from decimal import Decimal


class Command(BaseCommand):
    help = 'Popula a base de dados com produtos de teste'

    def handle(self, *args, **options):
        # Criar categorias se não existirem
        categorias_dados = {
            'Perfumes Femininos': 'perfumes-femininos',
            'Perfumes Masculinos': 'perfumes-masculinos',
            'Eau de Toilette': 'eau-de-toilette',
            'Colônias': 'colonias',
            'Essências': 'essencias',
        }

        categorias = {}
        for nome, slug in categorias_dados.items():
            cat, created = Categoria.objects.get_or_create(
                slug=slug,
                defaults={'nome': nome}
            )
            categorias[nome] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Categoria criada: {nome}'))

        # Produtos de teste
        produtos_dados = [
            {
                'nome': 'Chanel No. 5',
                'marca': 'Chanel',
                'descricao': 'Um dos perfumes mais icônicos do mundo',
                'preco_venda': Decimal('45000.00'),
                'preco_compra': Decimal('25000.00'),
                'quantidade': '100ml',
                'categoria': categorias['Perfumes Femininos'],
                'tipo': 'feminino',
                'essencia': 'Aldeídos, Jasmim, Rosa, Sândalo',
                'stock': 15,
            },
            {
                'nome': 'Dior Sauvage',
                'marca': 'Dior',
                'descricao': 'Perfume masculino sofisticado e duradouro',
                'preco_venda': Decimal('40000.00'),
                'preco_compra': Decimal('22000.00'),
                'quantidade': '100ml',
                'categoria': categorias['Perfumes Masculinos'],
                'tipo': 'masculino',
                'essencia': 'Ambroxan, Pimenta, Bergamota, Âmbar',
                'stock': 20,
            },
            {
                'nome': 'Dolce & Gabbana Light Blue',
                'marca': 'Dolce & Gabbana',
                'descricao': 'Perfume fresco e descontraído para mulheres',
                'preco_venda': Decimal('35000.00'),
                'preco_compra': Decimal('19000.00'),
                'quantidade': '100ml',
                'categoria': categorias['Perfumes Femininos'],
                'tipo': 'feminino',
                'essencia': 'Bergamota, Pera, Maçã, Almíscar branco',
                'stock': 18,
            },
            {
                'nome': 'Jean Paul Gaultier Le Male',
                'marca': 'Jean Paul Gaultier',
                'descricao': 'Clássico masculino com toque doce',
                'preco_venda': Decimal('42000.00'),
                'preco_compra': Decimal('23000.00'),
                'quantidade': '125ml',
                'categoria': categorias['Perfumes Masculinos'],
                'tipo': 'masculino',
                'essencia': 'Lavanda, Menta, Tonka, Almíscar',
                'stock': 12,
            },
            {
                'nome': 'Lancôme La Vie Est Belle',
                'marca': 'Lancôme',
                'descricao': 'Doce e glamouroso para mulheres sofisticadas',
                'preco_venda': Decimal('48000.00'),
                'preco_compra': Decimal('26000.00'),
                'quantidade': '75ml',
                'categoria': categorias['Perfumes Femininos'],
                'tipo': 'feminino',
                'essencia': 'Íris, Patchouli, Baunilha, Pralinê',
                'stock': 10,
            },
            {
                'nome': 'Acqua di Gioia',
                'marca': 'Giorgio Armani',
                'descricao': 'Eau de toilette fresca unissex',
                'preco_venda': Decimal('38000.00'),
                'preco_compra': Decimal('20000.00'),
                'quantidade': '100ml',
                'categoria': categorias['Eau de Toilette'],
                'tipo': 'unissex',
                'essencia': 'Citros, Limão, Menta, Brisa marinha',
                'stock': 25,
            },
            {
                'nome': 'Prada Luna Rossa',
                'marca': 'Prada',
                'descricao': 'Perfume sofisticado para homem',
                'preco_venda': Decimal('46000.00'),
                'preco_compra': Decimal('25000.00'),
                'quantidade': '100ml',
                'categoria': categorias['Perfumes Masculinos'],
                'tipo': 'masculino',
                'essencia': 'Sálvia, Cumarina, Âmbar, Cedro',
                'stock': 14,
            },
            {
                'nome': 'Guerlain Shalimar',
                'marca': 'Guerlain',
                'descricao': 'Clássico feminino elegante e sensual',
                'preco_venda': Decimal('52000.00'),
                'preco_compra': Decimal('28000.00'),
                'quantidade': '90ml',
                'categoria': categorias['Perfumes Femininos'],
                'tipo': 'feminino',
                'essencia': 'Ylang-ylang, Jasmim, Baunilha, Almíscar',
                'stock': 8,
            },
        ]

        for produto_dados in produtos_dados:
            produto, created = Produto.objects.get_or_create(
                nome=produto_dados['nome'],
                marca=produto_dados['marca'],
                defaults=produto_dados
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Produto criado: {produto.nome} ({produto.marca})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Produto já existe: {produto.nome} ({produto.marca})'
                    )
                )

        self.stdout.write(self.style.SUCCESS('\n✓ Seed de produtos concluído com sucesso!'))
