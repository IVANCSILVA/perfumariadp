from django.db import migrations, models


def consolidar_status(apps, schema_editor):
    Encomenda = apps.get_model('loja', 'Encomenda')
    # entregue -> finalizada
    Encomenda.objects.filter(status='entregue').update(status='finalizada')
    # cancelada permanece
    # tudo o resto (pendente, confirmada, em_preparacao, enviada) -> em_curso
    Encomenda.objects.filter(
        status__in=['pendente', 'confirmada', 'em_preparacao', 'enviada']
    ).update(status='em_curso')


def reverter_status(apps, schema_editor):
    Encomenda = apps.get_model('loja', 'Encomenda')
    Encomenda.objects.filter(status='finalizada').update(status='entregue')
    Encomenda.objects.filter(status='em_curso').update(status='pendente')


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0010_produto_essencia'),
    ]

    operations = [
        migrations.RunPython(consolidar_status, reverter_status),
        migrations.AlterField(
            model_name='encomenda',
            name='status',
            field=models.CharField(
                choices=[
                    ('em_curso', 'Em Curso'),
                    ('finalizada', 'Finalizada'),
                    ('cancelada', 'Cancelada'),
                ],
                default='em_curso',
                max_length=20,
            ),
        ),
    ]
