"""
Gera um backup da base de dados e regista-o no RegistoBackup para
conformidade com a AGT (Decreto Presidencial n.º 312/18).

Uso:
  python manage.py backup_db
  python manage.py backup_db --saida /backups/backup_2026-07-20.json

Agendar diariamente com cron:
  0 2 * * *  cd projeto && venv/bin/python manage.py backup_db
"""
import os
from datetime import date

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = 'Gera backup da base de dados e regista-o no RegistoBackup.'

    def add_arguments(self, parser):
        parser.add_argument('--saida', type=str, default=None, help='Caminho do ficheiro de saída.')

    def handle(self, *args, **options):
        from loja.models import RegistoBackup

        hoje = date.today().isoformat()
        saida = options['saida'] or os.path.join(
            getattr(settings, 'BASE_DIR', '.'),
            'backups',
            f'backup_{hoje}.json',
        )
        os.makedirs(os.path.dirname(saida), exist_ok=True)

        try:
            with open(saida, 'w', encoding='utf-8') as f:
                call_command('dumpdata', stdout=f, format='json', indent=2)
            tamanho = os.path.getsize(saida)
            RegistoBackup.objects.create(
                resultado='sucesso',
                ficheiro=saida,
                tamanho_bytes=tamanho,
                observacoes=f'Backup automático via management command ({hoje})',
            )
            self.stdout.write(self.style.SUCCESS(
                f'Backup gerado: {saida} ({tamanho} bytes)'
            ))
        except Exception as e:
            RegistoBackup.objects.create(
                resultado='falha',
                ficheiro=saida,
                observacoes=str(e),
            )
            self.stdout.write(self.style.ERROR(
                f'Falha ao gerar backup: {e}'
            ))
