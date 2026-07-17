from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Produto


class ProdutoSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Produto.objects.filter(disponivel=True).order_by('pk')

    def location(self, obj):
        return reverse('produto_detalhe', args=[obj.pk])

    def lastmod(self, obj):
        return getattr(obj, 'atualizado_em', None)


class StaticViewSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return ['home', 'colecoes', 'encomendas', 'galeria', 'fidelidade', 'contactos']

    def location(self, item):
        return reverse(item)
