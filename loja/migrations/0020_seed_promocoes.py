from django.db import migrations


PROMOCOES_PADRAO = [
    # (nome, tipo, ini_mes, ini_dia, fim_mes, fim_dia, desconto, cor, icone, descricao)
    ('Dia da Mulher', 'dia', 3, 8, 3, 8, 15, 'rose', '💐',
     'Celebração do Dia Internacional da Mulher.'),
    ('Dia do Pai', 'dia', 3, 19, 3, 19, 15, 'sky', '👔',
     'Dia do Pai (19 de Março).'),
    ('Páscoa', 'campanha', 3, 25, 4, 5, 10, 'amber', '🐣',
     'Campanha de Páscoa.'),
    ('Dia da Mãe', 'dia', 5, 1, 5, 31, 20, 'rose', '🌷',
     'Mês das Mães — descontos especiais.'),
    ('Dia da Criança', 'dia', 6, 1, 6, 1, 10, 'emerald', '🎈',
     'Dia Internacional da Criança.'),
    ('Mês dos Namorados', 'mes', 6, 1, 6, 30, 20, 'rose', '💕',
     'Junho dos Namorados.'),
    ('Dia dos Namorados', 'dia', 6, 12, 6, 12, 25, 'rose', '❤️',
     'Dia dos Namorados (12 de Junho — Brasil/Angola).'),
    ('Dia dos Avós', 'dia', 7, 26, 7, 26, 15, 'amber', '👵',
     'Dia dos Avós.'),
    ('Independência de Angola', 'dia', 11, 11, 11, 11, 11, 'stone', '🇦🇴',
     'Aniversário da Independência Nacional.'),
    ('Black Friday', 'campanha', 11, 24, 11, 30, 30, 'stone', '🛍️',
     'Última semana de Novembro — descontos elevados.'),
    ('Natal', 'campanha', 12, 1, 12, 24, 20, 'emerald', '🎄',
     'Campanha de Natal.'),
    ('Fim de Ano', 'campanha', 12, 26, 12, 31, 25, 'amber', '🎆',
     'Saldos de fim de ano.'),
]


def criar_promocoes(apps, schema_editor):
    Promocao = apps.get_model('loja', 'Promocao')
    from datetime import date
    ano = date.today().year
    for nome, tipo, im, idia, fm, fdia, desc, cor, icone, descricao in PROMOCOES_PADRAO:
        if Promocao.objects.filter(nome=nome).exists():
            continue
        Promocao.objects.create(
            nome=nome,
            tipo=tipo,
            descricao=descricao,
            data_inicio=date(ano, im, idia),
            data_fim=date(ano, fm, fdia),
            desconto_percentagem=desc,
            cor=cor,
            icone=icone,
            recorrente_anual=True,
            activo=True,
        )


def remover_promocoes(apps, schema_editor):
    Promocao = apps.get_model('loja', 'Promocao')
    nomes = [p[0] for p in PROMOCOES_PADRAO]
    Promocao.objects.filter(nome__in=nomes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0019_promocao'),
    ]

    operations = [
        migrations.RunPython(criar_promocoes, remover_promocoes),
    ]
