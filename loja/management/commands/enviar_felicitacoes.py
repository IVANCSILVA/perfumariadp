"""
Envia felicitações de aniversário diárias.

Modos:
- Fixo: corra uma vez por dia à hora configurada.
- Aleatório: corra de hora a hora (ou de 15 em 15 min); cada pessoa recebe à sua hora deterministica.

Agendar com:
  - Linux/macOS:  cron */15 * * * *  →  cd projeto && venv/bin/python manage.py enviar_felicitacoes
  - Windows:      Agendador de Tarefas → cada 15 minutos
"""
from datetime import date, datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from loja.models import (
    Cliente, Funcionario, ConfigAniversario, FelicitacaoEnviada,
)
from loja.views import _enviar_felicitacao


class Command(BaseCommand):
    help = 'Envia felicitações automáticas a clientes e funcionários que fazem anos hoje.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Mostra mas não envia nem regista.')
        parser.add_argument('--force', action='store_true', help='Reenvia mesmo a quem já recebeu este ano.')
        parser.add_argument('--ignore-time', action='store_true', help='Ignora horário e envia a todos os aniversariantes do dia.')

    def handle(self, *args, **opts):
        agora = timezone.localtime()
        hoje = agora.date()
        config = ConfigAniversario.get_solo()

        if not config.activo:
            self.stdout.write(self.style.WARNING('Sistema de felicitações desactivado nas configurações.'))
            return

        clientes = Cliente.objects.filter(
            data_nascimento__day=hoje.day, data_nascimento__month=hoje.month,
        )
        funcionarios = Funcionario.objects.filter(
            data_nascimento__day=hoje.day, data_nascimento__month=hoje.month, activo=True,
        )

        total_envios = 0
        total_falhas = 0
        total_adiados = 0

        for grupo, tipo in [(clientes, 'cliente'), (funcionarios, 'funcionario')]:
            for pessoa in grupo:
                if not opts['force']:
                    ja_enviado = FelicitacaoEnviada.objects.filter(
                        tipo=tipo, pessoa_id=pessoa.pk, ano=hoje.year, sucesso=True,
                    ).exists()
                    if ja_enviado:
                        self.stdout.write(f'  ⏭  {pessoa.nome} já recebeu felicitação em {hoje.year}.')
                        continue

                # Verificação de horário
                hora_alvo = config.horario_para(pessoa, tipo)
                if not opts['ignore_time'] and agora.time() < hora_alvo:
                    total_adiados += 1
                    self.stdout.write(self.style.NOTICE(
                        f'  ⏰ {pessoa.nome} — agendado para {hora_alvo.strftime("%H:%M")} (ainda não chegou).'
                    ))
                    continue

                if opts['dry_run']:
                    self.stdout.write(self.style.NOTICE(
                        f'  [DRY] {tipo} {pessoa.nome} → {hora_alvo.strftime("%H:%M")} ({pessoa.email or pessoa.telefone or "sem contacto"})'
                    ))
                    continue

                resultados = _enviar_felicitacao(pessoa, tipo, config)
                for r in resultados:
                    if r.sucesso:
                        total_envios += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✓ {tipo} {pessoa.nome} via {r.get_canal_display()} (alvo {hora_alvo.strftime("%H:%M")})'))
                    else:
                        total_falhas += 1
                        self.stdout.write(self.style.ERROR(
                            f'  ✗ {tipo} {pessoa.nome} via {r.get_canal_display()}: {r.erro}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Concluído: {total_envios} envio(s), {total_falhas} falha(s), {total_adiados} adiado(s).'))
