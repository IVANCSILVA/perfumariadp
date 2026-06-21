from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Corrige a classificação do modelo Produto:
    - Renomeia 'tipo' para 'genero' (género do público-alvo: masculino/feminino/unissex).
    - Converte os registos 'nicho' (segmento de mercado) para 'unissex' — 'nicho'
      deve ser gerido através da ForeignKey 'categoria' (ex: criar categoria "Nicho").
    - Adiciona 'concentracao' (Parfum, EDP, EDT, EDC, Body Mist).
    """

    dependencies = [
        ('loja', '0033_salarios_irt_subsidios'),
    ]

    operations = [
        # 1. Renomear coluna tipo → genero
        migrations.RenameField(
            model_name='produto',
            old_name='tipo',
            new_name='genero',
        ),

        # 2. Converter valores 'nicho' para 'unissex' antes de alterar choices
        migrations.RunSQL(
            sql="UPDATE loja_produto SET genero = 'unissex' WHERE genero = 'nicho';",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 3. Actualizar choices do campo genero (remove 'nicho')
        migrations.AlterField(
            model_name='produto',
            name='genero',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('masculino', 'Masculino'),
                    ('feminino', 'Feminino'),
                    ('unissex', 'Unissex'),
                ],
                default='unissex',
                verbose_name='Género',
                help_text='Público-alvo do perfume.',
            ),
        ),

        # 4. Adicionar campo concentracao
        migrations.AddField(
            model_name='produto',
            name='concentracao',
            field=models.CharField(
                max_length=20,
                blank=True,
                choices=[
                    ('pf',        'Parfum / Extrait de Parfum'),
                    ('edp',       'Eau de Parfum (EDP)'),
                    ('edt',       'Eau de Toilette (EDT)'),
                    ('edc',       'Eau de Cologne (EDC)'),
                    ('body_mist', 'Body Mist / Splash'),
                ],
                verbose_name='Concentração',
                help_text='Tipo de concentração da fragrância (EDP, EDT, Parfum, etc.).',
            ),
        ),
    ]
