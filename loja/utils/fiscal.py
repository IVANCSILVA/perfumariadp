"""
Conformidade fiscal AGT (Angola) — Decreto Presidencial n.º 312/18 e Regras e
Requisitos para Validação de Sistemas de Processamento Electrónico de
Facturação (MINFIN).

Este módulo implementa os alicerces técnicos exigidos antes da submissão do
sistema à AGT para validação/certificação:

1. Numeração sequencial e sem falhas por série fiscal e ano
   (ex: "FT 2026/145").
2. Assinatura digital (RSA + SHA-256) de cada documento fiscal, encadeada
   à assinatura do documento anterior (cadeia de hash), impedindo alteração
   retroactiva sem detecção.
3. Extracção do "hash curto" (4 caracteres, posições 1.ª, 11.ª, 21.ª e 31.ª
   da assinatura) para impressão no documento, tal como exigido pela AGT.

IMPORTANTE: enquanto o sistema não for formalmente validado pela AGT e não
lhe for atribuído um número de certificado, a chave privada utilizada é
gerada e mantida internamente (não é a chave "de fabricante" reconhecida
pela AGT). A menção legal "Processado por programa validado n.º XXX/AGT"
só pode ser impressa depois de obtido esse certificado — ver
loja/templates/gestao/fatura.html.
"""
import base64
import logging
import os

from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)

_PRIVATE_KEY_CACHE = None


def _chave_privada_path():
    return getattr(
        settings, 'FISCAL_PRIVATE_KEY_PATH',
        os.path.join(settings.BASE_DIR, 'keys', 'fiscal_private.pem')
    )


def get_private_key():
    """Carrega (ou gera, se ainda não existir) a chave privada RSA usada
    para assinar os documentos fiscais. A chave NUNCA deve ser versionada
    no controlo de código (ver .gitignore)."""
    global _PRIVATE_KEY_CACHE
    if _PRIVATE_KEY_CACHE is not None:
        return _PRIVATE_KEY_CACHE

    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    path = _chave_privada_path()
    if os.path.exists(path):
        with open(path, 'rb') as f:
            _PRIVATE_KEY_CACHE = serialization.load_pem_private_key(f.read(), password=None)
        return _PRIVATE_KEY_CACHE

    logger.warning(
        'Chave privada fiscal não encontrada em %s — a gerar uma nova chave '
        'RSA-2048 interna. Esta chave é temporária, apenas para garantir a '
        'integridade da cadeia de documentos até à validação oficial da AGT.',
        path,
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(path, 'wb') as f:
        f.write(pem)
    os.chmod(path, 0o600)
    _PRIVATE_KEY_CACHE = key
    return key


def _assinar(mensagem: str) -> str:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    chave = get_private_key()
    assinatura = chave.sign(
        mensagem.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(assinatura).decode('ascii')


def extrair_hash_curto(hash_atual: str) -> str:
    """Extrai os caracteres nas posições 1.ª, 11.ª, 21.ª e 31.ª da
    assinatura (convenção AGT), tolerando assinaturas mais curtas."""
    posicoes = [0, 10, 20, 30]
    return ''.join(hash_atual[p] for p in posicoes if p < len(hash_atual))


def gerar_numero_documento(encomenda, serie='FT'):
    """Gera o próximo número sequencial da série fiscal para o ano da
    emissão, sem falhas (nunca reutiliza nem salta números)."""
    from ..models import Encomenda

    ano = encomenda.data_emissao.year
    prefixo = f'{serie} {ano}/'
    ultimo = (
        Encomenda.objects
        .filter(numero_documento__startswith=prefixo)
        .exclude(pk=encomenda.pk)
        .order_by('-pk')
        .select_for_update()
        .first()
    )
    if ultimo and ultimo.numero_documento:
        try:
            ultimo_seq = int(ultimo.numero_documento.rsplit('/', 1)[-1])
        except (ValueError, IndexError):
            ultimo_seq = 0
    else:
        ultimo_seq = 0
    return f'{prefixo}{ultimo_seq + 1}'


def finalizar_documento_fiscal(encomenda, serie='FT'):
    """Atribui número de documento fiscal e assinatura digital encadeada a
    uma encomenda no momento em que esta é finalizada (torna-se um
    documento fiscal emitido). Deve ser chamada dentro de uma transacção
    atómica, uma única vez por documento, e nunca deve ser refeita depois
    de atribuída (o documento é imutável)."""
    from django.utils import timezone
    from ..models import Encomenda

    if encomenda.numero_documento:
        # Já foi finalizado fiscalmente antes — não reatribuir (imutabilidade).
        return encomenda

    with transaction.atomic():
        encomenda.data_emissao = timezone.now()
        encomenda.numero_documento = gerar_numero_documento(encomenda, serie=serie)

        anterior = (
            Encomenda.objects
            .filter(hash_atual__isnull=False)
            .exclude(pk=encomenda.pk)
            .order_by('-data_emissao')
            .select_for_update()
            .first()
        )
        hash_anterior = anterior.hash_atual if anterior else ''
        encomenda.hash_anterior = hash_anterior

        total = encomenda.total()
        mensagem = (
            f'{encomenda.data_emissao.isoformat()};'
            f'{encomenda.numero_documento};'
            f'{total};'
            f'{hash_anterior}'
        )
        encomenda.hash_atual = _assinar(mensagem)
        encomenda.hash_curto = extrair_hash_curto(encomenda.hash_atual)

        encomenda.save(update_fields=[
            'data_emissao', 'numero_documento',
            'hash_anterior', 'hash_atual', 'hash_curto',
        ])

    return encomenda


def verificar_cadeia_hash():
    """Verifica a integridade da cadeia de assinaturas de todos os
    documentos fiscais emitidos. Retorna um dicionário com:
    - 'valida': bool — True se a cadeia está intacta
    - 'total': int — número de documentos verificados
    - 'quebras': list — lista de documentos com quebra de cadeia"""
    from ..models import Encomenda

    docs = list(
        Encomenda.objects
        .filter(hash_atual__isnull=False)
        .order_by('data_emissao')
    )
    quebras = []
    hash_esperado_anterior = ''

    for doc in docs:
        erros = []
        if doc.hash_anterior != hash_esperado_anterior:
            erros.append('hash_anterior não corresponde ao documento anterior')
        hash_esperado_anterior = doc.hash_atual

        total = doc.total()
        mensagem = (
            f'{doc.data_emissao.isoformat()};'
            f'{doc.numero_documento};'
            f'{total};'
            f'{doc.hash_anterior or ""}'
        )
        hash_recalculado = _assinar(mensagem)
        if hash_recalculado != doc.hash_atual:
            erros.append('hash_atual não corresponde à re-assinatura dos dados')

        if erros:
            quebras.append({
                'documento': doc.numero_documento,
                'pk': doc.pk,
                'erros': erros,
            })

    return {
        'valida': len(quebras) == 0,
        'total': len(docs),
        'quebras': quebras,
    }


def emitir_nota_credito(factura, motivo, valor, descricao='', emitido_por=None):
    """Emite uma nota de crédito (documento de rectificação) para uma
    factura emitida. A nota de crédito tem numeração própria (série NC),
    assinatura digital encadeada e é registada no log de auditoria."""
    from django.utils import timezone
    from ..models import NotaCredito, LogAuditoria, Encomenda

    if not factura.numero_documento:
        raise ValueError('A factura original ainda não foi finalizada fiscalmente.')

    with transaction.atomic():
        nc = NotaCredito.objects.create(
            factura_original=factura,
            motivo=motivo,
            descricao=descricao,
            valor=valor,
            emitida_por=emitido_por,
        )
        nc.data_emissao = timezone.now()

        ano = nc.data_emissao.year
        prefixo = f'NC {ano}/'
        ultima_nc = (
            NotaCredito.objects
            .filter(numero_documento__startswith=prefixo)
            .exclude(pk=nc.pk)
            .order_by('-pk')
            .select_for_update()
            .first()
        )
        if ultima_nc and ultima_nc.numero_documento:
            try:
                ultimo_seq = int(ultima_nc.numero_documento.rsplit('/', 1)[-1])
            except (ValueError, IndexError):
                ultimo_seq = 0
        else:
            ultimo_seq = 0
        nc.numero_documento = f'{prefixo}{ultimo_seq + 1}'

        ultimo_doc = (
            Encomenda.objects
            .filter(hash_atual__isnull=False)
            .order_by('-data_emissao')
            .select_for_update()
            .first()
        )
        ultima_nc_doc = (
            NotaCredito.objects
            .filter(hash_atual__isnull=False)
            .exclude(pk=nc.pk)
            .order_by('-data_emissao')
            .select_for_update()
            .first()
        )
        if ultima_nc_doc and (not ultimo_doc or ultima_nc_doc.data_emissao > ultimo_doc.data_emissao):
            hash_anterior = ultima_nc_doc.hash_atual
        elif ultimo_doc:
            hash_anterior = ultimo_doc.hash_atual
        else:
            hash_anterior = ''
        nc.hash_anterior = hash_anterior

        mensagem = (
            f'{nc.data_emissao.isoformat()};'
            f'{nc.numero_documento};'
            f'{valor};'
            f'{hash_anterior}'
        )
        nc.hash_atual = _assinar(mensagem)
        nc.hash_curto = extrair_hash_curto(nc.hash_atual)
        nc.save(update_fields=[
            'data_emissao', 'numero_documento',
            'hash_anterior', 'hash_atual', 'hash_curto',
        ])

        LogAuditoria.objects.create(
            utilizador=emitido_por,
            acao='rectificacao',
            descricao=f'Nota de crédito {nc.numero_documento} emitida para {factura.numero_documento}',
            objeto_tipo='NotaCredito',
            objeto_id=nc.pk,
        )

    return nc
