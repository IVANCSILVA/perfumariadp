from datetime import date

from loja.models import Promocao


def get_promocoes_activas(hoje=None):
    """Return active promotions currently running, with products prefetched.

    Returns ``(activas, carrossel, landing)`` where *activas* is the full list,
    *carrossel* those flagged for the carousel, and *landing* those flagged for
    the landing/collections page.
    """
    hoje = hoje or date.today()
    todas = Promocao.objects.filter(activo=True).prefetch_related('produtos')
    activas = [p for p in todas if p.esta_decorrer(hoje)]
    carrossel = [p for p in activas if p.mostrar_carrossel]
    landing = [p for p in activas if p.mostrar_landing]
    return activas, carrossel, landing
