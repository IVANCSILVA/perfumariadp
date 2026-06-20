"""
Migração de dados: converte as categorias antigas (que misturavam
género e concentração) para os campos dedicados `genero` e `concentracao`
adicionados na migração 0034.

Lógica:
  - O nome da categoria é analisado de forma insensível a maiúsculas/acentos.
  - Se corresponder a uma concentração conhecida → actualiza `concentracao` nos produtos.
  - Se corresponder a um género conhecido → actualiza `genero` nos produtos.
  - Após a migração, a categoria é desassociada dos produtos que foram migrados
    e eliminada, pois a informação está agora nos campos dedicados.
  - Categorias que não correspondam a nenhum padrão são mantidas intactas
    (segmentos legítimos como "Nicho", "Exclusivos", etc.).
"""

from django.db import migrations
import unicodedata


def _normalizar(texto):
    """Remove acentos e converte para minúsculas para comparação robusta."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )


# ---------------------------------------------------------------------------
# Mapeamentos: (fragmento_normalizado, campo, valor)
# A ordem importa: padrões mais específicos primeiro.
# ---------------------------------------------------------------------------
MAPA_CONCENTRACAO = [
    # Parfum / Extrait — mais específico primeiro
    ('extrait de parfum',  'pf'),
    ('extrait',            'pf'),
    # Eau de Parfum ANTES de 'parfum' sozinho
    ('eau de parfum',      'edp'),
    (' edp',               'edp'),
    ('edp ',               'edp'),
    ('(edp)',              'edp'),
    # Só depois: parfum sozinho (ex: "Parfum", "Parfum Concentrado")
    ('parfum',             'pf'),
    # Toilette
    ('eau de toilette',    'edt'),
    (' edt',               'edt'),
    ('edt ',               'edt'),
    ('(edt)',              'edt'),
    # Cologne / Colónia
    ('eau de cologne',     'edc'),
    ('colonia',            'edc'),   # colônia, colonia
    ('cologne',            'edc'),
    (' edc',               'edc'),
    ('(edc)',              'edc'),
    # Body Mist
    ('body mist',          'body_mist'),
    ('body spray',         'body_mist'),
    ('splash',             'body_mist'),
]

MAPA_GENERO = [
    ('masculin',   'masculino'),   # masculino, masculinos
    ('homem',      'masculino'),
    ('homme',      'masculino'),
    (' men',       'masculino'),
    ('men ',       'masculino'),
    ('(men)',      'masculino'),
    ('feminin',    'feminino'),    # feminino, femininos
    ('mulher',     'feminino'),
    ('femme',      'feminino'),
    ('women',      'feminino'),
    ('woman',      'feminino'),
    ('para ela',   'feminino'),
    ('para ele',   'masculino'),
    ('unissex',    'unissex'),
    ('unisex',     'unissex'),
]


def _detetar(nome_norm):
    """Devolve (concentracao_val, genero_val) detectados no nome, ou None."""
    conc = None
    gen = None
    for fragmento, val in MAPA_CONCENTRACAO:
        if fragmento in nome_norm:
            conc = val
            break
    for fragmento, val in MAPA_GENERO:
        if fragmento in nome_norm:
            gen = val
            break
    return conc, gen


def migrar_categorias(apps, schema_editor):
    Categoria = apps.get_model('loja', 'Categoria')
    Produto = apps.get_model('loja', 'Produto')

    categorias_a_eliminar = []

    for cat in Categoria.objects.all():
        nome_norm = _normalizar(cat.nome)
        conc, gen = _detetar(nome_norm)

        if conc is None and gen is None:
            # Categoria legítima (ex: "Nicho", "Exclusivos") — manter
            continue

        # Actualizar produtos desta categoria
        produtos = Produto.objects.filter(categoria=cat)
        for p in produtos:
            alterado = False
            if conc and not p.concentracao:
                p.concentracao = conc
                alterado = True
            if gen:
                # Género: só substituir se o produto ainda tem o default 'unissex'
                # E se a categoria especifica explicitamente o género
                if p.genero == 'unissex' or not p.genero:
                    p.genero = gen
                    alterado = True
            # Desassociar categoria (a info está agora nos campos dedicados)
            p.categoria = None
            if alterado or True:  # sempre gravar para limpar a categoria
                p.save()

        categorias_a_eliminar.append(cat.pk)

    # Eliminar categorias migradas
    Categoria.objects.filter(pk__in=categorias_a_eliminar).delete()


def reverter(apps, schema_editor):
    # Irreversível de forma segura — não faz nada no reverse
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0034_produto_genero_concentracao'),
    ]

    operations = [
        migrations.RunPython(migrar_categorias, reverter),
    ]
