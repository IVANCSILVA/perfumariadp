from django.utils.text import slugify


def gerar_slug_unico(model_class, nome, instancia=None, max_length=130):
    """Generate a unique slug for *model_class* based on *nome*.

    If *instancia* is provided its PK is excluded from the uniqueness check so
    that updating an existing record keeps its slug stable.
    """
    base = slugify(nome)[:max_length] or model_class.__name__.lower()
    slug = base
    n = 2
    while True:
        qs = model_class.objects.filter(slug=slug)
        if instancia and instancia.pk:
            qs = qs.exclude(pk=instancia.pk)
        if not qs.exists():
            return slug
        slug = f'{base}-{n}'
        n += 1
