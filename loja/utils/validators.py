import re

from django.core.exceptions import ValidationError


def limpar_bi(value):
    """Strip whitespace and uppercase an Angolan BI string."""
    return value.replace(' ', '').upper()


def limpar_telefone(value):
    """Strip formatting characters and the +244/244 country prefix."""
    limpo = re.sub(r'[\s\-\(\)]', '', value)
    if limpo.startswith('+244'):
        limpo = limpo[4:]
    elif limpo.startswith('244') and len(limpo) == 12:
        limpo = limpo[3:]
    return limpo


BI_REGEX = r'\d{9}[A-Z]{2}\d{3}'
TELEFONE_REGEX = r'9\d{8}'


def validar_bi_angola(value):
    """BI angolano: 9 digitos + 2 letras + 3 digitos (ex: 003456789LA045)"""
    limpo = limpar_bi(value)
    if not re.fullmatch(BI_REGEX, limpo):
        raise ValidationError(
            'BI invalido. Formato esperado: 9 digitos + 2 letras + 3 digitos (ex: 003456789LA045).'
        )


def validar_telefone_angola(value):
    """Telefone angolano: 9 digitos comecando em 9, aceita +244 e espacos"""
    limpo = limpar_telefone(value)
    if not re.fullmatch(TELEFONE_REGEX, limpo):
        raise ValidationError(
            'Telefone invalido. Formato esperado: 9XX XXX XXX (ex: 923 456 789).'
        )
