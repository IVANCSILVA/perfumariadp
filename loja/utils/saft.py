"""
Exportação SAF-T (AO) — ficheiro normalizado de auditoria tributária,
exigido pelo Decreto Presidencial n.º 312/18 (Regime Jurídico de Submissão
Electrónica dos Elementos Contabilísticos dos Contribuintes) para
contribuintes com volume de negócios anual superior a Kz 50.000.000,00.

AVISO IMPORTANTE: este gerador segue a estrutura geral do modelo SAF-T
adoptado por Angola (derivado do modelo português), com base na informação
publicamente disponível sobre os requisitos da AGT. Antes da submissão
formal, o ficheiro produzido deve ser validado contra o esquema XSD oficial
da AGT (disponibilizado apenas no processo de validação do software), pois
poderão existir elementos/atributos específicos da versão XSD-AO que não
constam aqui.
"""
from xml.etree import ElementTree as ET
from xml.dom import minidom

from django.conf import settings

from ..models import Encomenda


NS = 'urn:OECD:StandardAuditFile-Tax:AO_1.01_01'


def _sub(parent, tag, text=None):
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = str(text)
    return el


def _header(root, data_inicio, data_fim):
    header = _sub(root, 'Header')
    _sub(header, 'AuditFileVersion', '1.01_01')
    _sub(header, 'CompanyID', getattr(settings, 'EMPRESA_NIF', ''))
    _sub(header, 'TaxRegistrationNumber', getattr(settings, 'EMPRESA_NIF', ''))
    _sub(header, 'TaxAccountingBasis', 'F')
    _sub(header, 'CompanyName', getattr(settings, 'EMPRESA_NOME', ''))
    endereco = _sub(header, 'CompanyAddress')
    _sub(endereco, 'AddressDetail', getattr(settings, 'EMPRESA_ENDERECO', ''))
    _sub(endereco, 'City', 'Huambo')
    _sub(endereco, 'Country', 'AO')
    _sub(header, 'FiscalYear', data_inicio.year)
    _sub(header, 'StartDate', data_inicio.strftime('%Y-%m-%d'))
    _sub(header, 'EndDate', data_fim.strftime('%Y-%m-%d'))
    _sub(header, 'CurrencyCode', 'AOA')
    from django.utils import timezone
    _sub(header, 'DateCreated', timezone.now().strftime('%Y-%m-%d'))
    _sub(header, 'TaxEntity', 'Global')
    _sub(header, 'ProductCompanyTaxID', getattr(settings, 'EMPRESA_NIF', ''))
    certificado = getattr(settings, 'AGT_NUMERO_CERTIFICADO', '') or '0/AGT (pendente de validação)'
    _sub(header, 'SoftwareCertificateNumber', certificado)
    _sub(header, 'ProductID', 'Décent Privé - Sistema de Gestão/Banild Lda.')
    _sub(header, 'ProductVersion', '1.0')
    return header


def _master_files(root, encomendas):
    master = _sub(root, 'MasterFiles')

    clientes = {}
    for enc in encomendas:
        chave = enc.telefone or enc.nome_cliente
        if chave not in clientes:
            clientes[chave] = enc

    for idx, enc in enumerate(clientes.values(), start=1):
        cust = _sub(master, 'Customer')
        _sub(cust, 'CustomerID', str(idx))
        _sub(cust, 'AccountID', 'Desconhecido')
        _sub(cust, 'CustomerTaxID', enc.nif or '999999999')
        _sub(cust, 'CompanyName', enc.nome_empresa or enc.nome_cliente)
        endereco = _sub(cust, 'BillingAddress')
        _sub(endereco, 'AddressDetail', enc.morada or 'Desconhecido')
        _sub(endereco, 'City', 'Huambo')
        _sub(endereco, 'Country', 'AO')
        _sub(cust, 'Telephone', enc.telefone or '')
        _sub(cust, 'Email', enc.email or '')
        _sub(cust, 'SelfBillingIndicator', '0')

    produtos = {}
    for enc in encomendas:
        for item in enc.itens.all():
            chave = item.produto_id or item.nome_produto
            if chave not in produtos:
                produtos[chave] = item

    tax_table = _sub(master, 'TaxTable')
    tax_entry = _sub(tax_table, 'TaxTableEntry')
    _sub(tax_entry, 'TaxType', 'IVA')
    _sub(tax_entry, 'TaxCountryRegion', 'AO')
    _sub(tax_entry, 'TaxCode', 'ISE')
    _sub(tax_entry, 'Description', 'Isento de IVA')

    for idx, item in enumerate(produtos.values(), start=1):
        prod = _sub(master, 'Product')
        _sub(prod, 'ProductType', 'P')
        _sub(prod, 'ProductCode', str(item.produto_id or f'GEN{idx}'))
        _sub(prod, 'ProductDescription', item.nome_produto)
        _sub(prod, 'ProductNumberCode', str(item.produto_id or f'GEN{idx}'))

    return master, clientes, produtos


def _source_documents(root, encomendas, clientes, produtos):
    src = _sub(root, 'SourceDocuments')
    vendas = _sub(src, 'SalesInvoices')
    _sub(vendas, 'NumberOfEntries', len(encomendas))

    total_credito = sum(float(e.total()) for e in encomendas if e.status == 'finalizada')
    total_debito = sum(float(e.total()) for e in encomendas if e.status == 'cancelada')
    _sub(vendas, 'TotalDebit', round(total_debito, 2))
    _sub(vendas, 'TotalCredit', round(total_credito, 2))

    cliente_por_chave = {chave: idx for idx, chave in enumerate(clientes.keys(), start=1)}
    produto_por_chave = {chave: idx for idx, chave in enumerate(produtos.keys(), start=1)}

    for enc in encomendas:
        inv = _sub(vendas, 'Invoice')
        _sub(inv, 'InvoiceNo', enc.numero_documento or f'FT DESCONHECIDO/{enc.pk}')
        doc_status = _sub(inv, 'DocumentStatus')
        _sub(doc_status, 'InvoiceStatus', 'N' if enc.status == 'finalizada' else 'A')
        _sub(doc_status, 'InvoiceStatusDate', (enc.data_emissao or enc.criado_em).strftime('%Y-%m-%dT%H:%M:%S'))
        _sub(doc_status, 'SourceID', str(enc.vendido_por_id or ''))
        _sub(doc_status, 'SourceBilling', 'P')

        # Enquanto o software não estiver validado/certificado pela AGT, a
        # regulamentação exige explicitamente estes valores fixos nos campos
        # Hash/HashControl (mesmo que exista uma assinatura interna, guardada
        # em enc.hash_atual, usada apenas para a cadeia de integridade
        # própria do sistema — ver loja/utils/fiscal.py).
        certificado = getattr(settings, 'AGT_NUMERO_CERTIFICADO', '')
        if certificado:
            _sub(inv, 'Hash', enc.hash_curto or '0')
            _sub(inv, 'HashControl', '1')
        else:
            _sub(inv, 'Hash', '0')
            _sub(inv, 'HashControl', 'Não Validado pela AGT')
        _sub(inv, 'Period', (enc.data_emissao or enc.criado_em).month)
        _sub(inv, 'InvoiceDate', (enc.data_emissao or enc.criado_em).strftime('%Y-%m-%d'))
        _sub(inv, 'InvoiceType', 'FT')
        special = _sub(inv, 'SpecialRegimes')
        _sub(special, 'SelfBillingIndicator', '0')
        _sub(inv, 'SourceID', str(enc.vendido_por_id or ''))
        _sub(inv, 'SystemEntryDate', enc.criado_em.strftime('%Y-%m-%dT%H:%M:%S'))
        chave_cliente = enc.telefone or enc.nome_cliente
        _sub(inv, 'CustomerID', str(cliente_por_chave.get(chave_cliente, '')))

        total_linhas = 0.0
        for i, item in enumerate(enc.itens.all(), start=1):
            linha = _sub(inv, 'Line')
            _sub(linha, 'LineNumber', i)
            chave_produto = item.produto_id or item.nome_produto
            _sub(linha, 'ProductCode', str(produto_por_chave.get(chave_produto, '')))
            _sub(linha, 'ProductDescription', item.nome_produto)
            _sub(linha, 'Quantity', item.quantidade)
            _sub(linha, 'UnitOfMeasure', 'UN')
            _sub(linha, 'UnitPrice', float(item.preco_unitario))
            _sub(linha, 'TaxPointDate', (enc.data_emissao or enc.criado_em).strftime('%Y-%m-%d'))
            _sub(linha, 'Description', item.nome_produto)
            subtotal = float(item.subtotal())
            _sub(linha, 'CreditAmount', round(subtotal, 2))
            tax = _sub(linha, 'Tax')
            _sub(tax, 'TaxType', 'IVA')
            _sub(tax, 'TaxCountryRegion', 'AO')
            _sub(tax, 'TaxCode', 'ISE')
            _sub(tax, 'TaxPercentage', 0)
            total_linhas += subtotal

        totais = _sub(inv, 'DocumentTotals')
        _sub(totais, 'TaxPayable', 0)
        _sub(totais, 'NetTotal', round(total_linhas, 2))
        _sub(totais, 'GrossTotal', round(total_linhas, 2))

    return src


def gerar_saft_ao(data_inicio, data_fim):
    """Gera o XML SAF-T(AO) para as vendas finalizadas no período
    [data_inicio, data_fim] (inclusive). Retorna bytes UTF-8 formatados."""
    encomendas = list(
        Encomenda.objects
        .filter(
            status__in=['finalizada', 'cancelada'],
            data_emissao__date__gte=data_inicio,
            data_emissao__date__lte=data_fim,
        )
        .prefetch_related('itens__produto')
        .order_by('data_emissao')
    )

    root = ET.Element('AuditFile', xmlns=NS)
    _header(root, data_inicio, data_fim)
    _, clientes, produtos = _master_files(root, encomendas)
    _source_documents(root, encomendas, clientes, produtos)

    xml_bytes = ET.tostring(root, encoding='utf-8')
    pretty = minidom.parseString(xml_bytes).toprettyxml(indent='  ', encoding='utf-8')
    return pretty
