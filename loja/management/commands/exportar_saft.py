"""
Gera o ficheiro SAF-T (AO) mensal, conforme exigido pelo Decreto
Presidencial n.º 312/18 para contribuintes obrigados à submissão
electrónica de elementos contabilísticos.

Uso:
  python manage.py exportar_saft --ano 2026 --mes 7
  python manage.py exportar_saft --ano 2026 --mes 7 --saida caminho/ficheiro.xml

Se --mes não for indicado, exporta o ano completo.
Agendar mensalmente com cron para gerar o ficheiro do mês anterior, ex:
  0 3 1 * *  cd projeto && venv/bin/python manage.py exportar_saft
"""
import calendar
from datetime import date

from django.core.management.base import BaseCommand

from loja.utils.saft import gerar_saft_ao


class Command(BaseCommand):
    help = 'Gera o ficheiro XML SAF-T (AO) para um período (mês ou ano).'

    def add_arguments(self, parser):
        hoje = date.today()
        mes_anterior = hoje.month - 1 or 12
        ano_mes_anterior = hoje.year if hoje.month > 1 else hoje.year - 1
        parser.add_argument('--ano', type=int, default=ano_mes_anterior)
        parser.add_argument('--mes', type=int, default=mes_anterior)
        parser.add_argument('--ano-completo', action='store_true', help='Exporta o ano completo em vez de um único mês.')
        parser.add_argument('--saida', type=str, default=None, help='Caminho do ficheiro de saída.')

    def handle(self, *args, **options):
        ano = options['ano']
        if options['ano_completo']:
            data_inicio = date(ano, 1, 1)
            data_fim = date(ano, 12, 31)
            sufixo = f'{ano}'
        else:
            mes = options['mes']
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            data_inicio = date(ano, mes, 1)
            data_fim = date(ano, mes, ultimo_dia)
            sufixo = f'{ano}-{mes:02d}'

        xml_bytes = gerar_saft_ao(data_inicio, data_fim)

        saida = options['saida'] or f'SAFT_AO_{sufixo}.xml'
        with open(saida, 'wb') as f:
            f.write(xml_bytes)

        self.stdout.write(self.style.SUCCESS(
            f'Ficheiro SAF-T(AO) gerado: {saida} (período: {data_inicio} a {data_fim})'
        ))
