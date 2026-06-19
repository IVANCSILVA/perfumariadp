def is_operador(user):
    """Return True if *user* belongs to the Operador group (restricted access)."""
    return bool(
        user
        and user.is_authenticated
        and not user.is_superuser
        and user.groups.filter(name='Operador').exists()
    )
