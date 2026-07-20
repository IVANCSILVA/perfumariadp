"""
Integração com o gateway de pagamento online da EMIS — Multicaixa Express (GPO).

⚠️ IMPORTANTE
-------------
Este módulo implementa a estrutura típica de uma integração GPO (criar
referência de pagamento → redireccionar o cliente → receber notificação de
confirmação), mas os nomes exactos dos campos do pedido/resposta e o URL do
endpoint devem ser confirmados junto da documentação oficial fornecida pela
EMIS quando o comércio for aprovado e as credenciais (Entity ID + Token GPO)
forem emitidas. Ajuste `SANDBOX_URL`/`PRODUCAO_URL` e o payload em
`criar_referencia()` de acordo com essa documentação antes de activar o
gateway em produção.

Fluxo de pagamento
-------------------
1. O cliente escolhe "Multicaixa Express" no checkout (`loja.views.encomendas`).
2. `criar_referencia()` é chamado — cria a referência de pagamento junto da
   EMIS e devolve o URL de redireccionamento para o ecrã seguro de pagamento.
3. O cliente conclui o pagamento no site da EMIS (cartão / Multicaixa Express).
4. A EMIS notifica a loja via callback HTTP, tratado em
   `loja.views.pagamento_emis_callback`, que chama `processar_callback()`.

Enquanto `ConfiguracaoPagamento.gateway_configurado` for `False` (sem
credenciais), este método de pagamento fica automaticamente oculto no
checkout — ver `ConfiguracaoPagamento.metodos_disponiveis()`.
"""
import logging

import requests

logger = logging.getLogger(__name__)

# TODO: confirmar estes URLs com a documentação oficial da EMIS GPO.
SANDBOX_URL = 'https://pagamentonline-hml.emis.co.ao/online-payment-gateway/portal'
PRODUCAO_URL = 'https://pagamentonline.emis.co.ao/online-payment-gateway/portal'

TIMEOUT_SEGUNDOS = 15


class GatewayIndisponivel(Exception):
    """Levantado quando o gateway não está configurado ou falha ao comunicar com a EMIS."""


def _base_url(config):
    return PRODUCAO_URL if config.emis_ambiente == 'producao' else SANDBOX_URL


def criar_referencia(encomenda):
    """Cria uma referência de pagamento GPO para a encomenda e devolve o URL
    de redireccionamento para o ecrã de pagamento da EMIS.

    Levanta `GatewayIndisponivel` se as credenciais não estiverem configuradas
    ou se a chamada à EMIS falhar — nesse caso o chamador deve pedir ao
    cliente para escolher outro método de pagamento.
    """
    from ..models import ConfiguracaoPagamento

    config = ConfiguracaoPagamento.get_solo()
    if not config.gateway_configurado:
        raise GatewayIndisponivel('O gateway Multicaixa Express não está configurado.')

    total = encomenda.total()
    payload = {
        'reference': str(encomenda.pk),
        'amount': f'{total:.2f}',
        'token': config.emis_gpo_token,
        'mobile': 'PAYMENT',
        'card': 'PAYMENT',
        'qrCode': 'PAYMENT',
    }

    try:
        resp = requests.post(
            f'{_base_url(config)}/{config.emis_entity_id}',
            json=payload,
            timeout=TIMEOUT_SEGUNDOS,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 — qualquer falha de rede/formato deve degradar graciosamente
        logger.error(
            'Falha ao criar referência de pagamento EMIS para a encomenda #%s: %s',
            encomenda.pk, exc,
        )
        raise GatewayIndisponivel(
            'Não foi possível iniciar o pagamento online. Escolha outro método de pagamento.'
        ) from exc

    referencia = data.get('id') or data.get('token') or ''
    encomenda.referencia_pagamento_gateway = referencia
    encomenda.status_pagamento_gateway = 'pendente'
    encomenda.save(update_fields=['referencia_pagamento_gateway', 'status_pagamento_gateway'])

    redirect_url = data.get('redirectUrl') or f'{_base_url(config)}/{config.emis_entity_id}/{referencia}'
    return redirect_url


def processar_callback(dados):
    """Processa a notificação (webhook) enviada pela EMIS após o pagamento.

    `dados` é o corpo (JSON) recebido no endpoint de callback. Ajuste os
    nomes dos campos aqui consultados de acordo com o payload real enviado
    pela EMIS, conforme a documentação do GPO.

    Devolve a `Encomenda` actualizada, ou `None` se a referência não for
    reconhecida.
    """
    from ..models import Encomenda

    referencia = dados.get('reference') or dados.get('id')
    estado = (dados.get('status') or '').lower()
    if not referencia:
        return None

    encomenda = Encomenda.objects.filter(referencia_pagamento_gateway=referencia).first()
    if not encomenda:
        logger.warning('Callback EMIS recebido para referência desconhecida: %s', referencia)
        return None

    if estado in ('success', 'paid', 'pago'):
        encomenda.status_pagamento_gateway = 'pago'
    elif estado in ('failed', 'error', 'falhado', 'declined'):
        encomenda.status_pagamento_gateway = 'falhado'
    else:
        encomenda.status_pagamento_gateway = 'pendente'
    encomenda.save(update_fields=['status_pagamento_gateway'])
    return encomenda
