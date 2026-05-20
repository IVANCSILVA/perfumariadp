from .models import Encomenda


def encomendas_online_pendentes(request):
    """Disponibiliza, em todos os templates de gestão, o número de
    encomendas online (sem operador) que estão em curso."""
    if not request.path.startswith('/gestao/'):
        return {}
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}
    count = Encomenda.objects.filter(
        status='em_curso',
        vendido_por__isnull=True,
    ).count()
    return {'pedidos_online_pendentes': count}


def nivel_acesso(request):
    """Disponibiliza flags de nível de acesso (operador / gerente / administrador)
    em todos os templates."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'is_operador': False, 'is_gerente': False, 'is_admin_user': False}
    is_admin_user = bool(user.is_superuser)
    is_operador = bool(
        not user.is_superuser
        and user.groups.filter(name='Operador').exists()
    )
    is_gerente = bool(
        not user.is_superuser
        and not is_operador
        and user.is_staff
    )
    return {
        'is_operador': is_operador,
        'is_gerente': is_gerente,
        'is_admin_user': is_admin_user,
    }
