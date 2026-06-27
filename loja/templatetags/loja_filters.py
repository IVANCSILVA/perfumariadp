from django import template

register = template.Library()


@register.filter
def kz(value):
    """Formata um número no estilo angolano/europeu: 15000 -> 15.000,00"""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return value
    s = f'{num:,.2f}'
    # Python usa "," para milhares e "." para decimal
    # Trocamos: "," -> "." e "." -> ","
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    return s
