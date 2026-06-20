def contar_por_status(queryset):
    """Count orders by status from *queryset*.

    Returns a dict ``{'em_curso': N, 'finalizada': N, 'cancelada': N}``.
    """
    contadores = {'em_curso': 0, 'finalizada': 0, 'cancelada': 0}
    for e in queryset:
        if e.status in contadores:
            contadores[e.status] += 1
    return contadores
