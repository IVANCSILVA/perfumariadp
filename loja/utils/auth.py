GRUPO_OPERADOR = 'Operador'
GRUPO_SECRETARIA = 'Secretaria'


def is_operador(user):
    """Return True if *user* belongs to the Operador or Secretaria
    group (restricted access)."""
    return bool(
        user
        and user.is_authenticated
        and not user.is_superuser
        and user.groups.filter(name__in=[GRUPO_OPERADOR, GRUPO_SECRETARIA]).exists()
    )


def pode_criar_produtos(user):
    """Return True if *user* é Secretaria, com permissão extra
    para criar (apenas criar, não editar/eliminar) novos produtos."""
    return bool(
        user
        and user.is_authenticated
        and not user.is_superuser
        and user.groups.filter(name=GRUPO_SECRETARIA).exists()
    )
