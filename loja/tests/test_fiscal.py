"""Testes de conformidade fiscal AGT (Decreto Presidencial n.º 312/18):
numeração sequencial por série/ano, cadeia de assinatura digital e
exportação SAF-T (AO)."""
import base64
from datetime import date
from xml.etree import ElementTree as ET

from django.test import TestCase, override_settings

from loja.models import Encomenda, ItemEncomenda, Produto
from loja.utils import fiscal
from loja.utils.saft import gerar_saft_ao


def _criar_encomenda(**kwargs):
    defaults = dict(nome_cliente='Cliente Teste', telefone='900000000', status='em_curso')
    defaults.update(kwargs)
    return Encomenda.objects.create(**defaults)


class FiscalTests(TestCase):

    def setUp(self):
        # Isola a chave privada por teste para não afectar/depender de chaves
        # geradas por outras execuções.
        fiscal._PRIVATE_KEY_CACHE = None

    def tearDown(self):
        fiscal._PRIVATE_KEY_CACHE = None

    def test_finalizar_atribui_numero_e_hash(self):
        enc = _criar_encomenda()
        fiscal.finalizar_documento_fiscal(enc)
        enc.refresh_from_db()

        self.assertTrue(enc.numero_documento.startswith('FT '))
        self.assertIsNotNone(enc.data_emissao)
        self.assertTrue(enc.hash_atual)
        self.assertEqual(enc.hash_anterior, '')
        self.assertEqual(len(enc.hash_curto), 4)

    def test_numeracao_sequencial_sem_falhas(self):
        enc1 = _criar_encomenda()
        fiscal.finalizar_documento_fiscal(enc1)
        enc2 = _criar_encomenda()
        fiscal.finalizar_documento_fiscal(enc2)

        enc1.refresh_from_db()
        enc2.refresh_from_db()

        seq1 = int(enc1.numero_documento.rsplit('/', 1)[-1])
        seq2 = int(enc2.numero_documento.rsplit('/', 1)[-1])
        self.assertEqual(seq2, seq1 + 1)

    def test_cadeia_de_hash_encadeada(self):
        enc1 = _criar_encomenda()
        fiscal.finalizar_documento_fiscal(enc1)
        enc1.refresh_from_db()

        enc2 = _criar_encomenda()
        fiscal.finalizar_documento_fiscal(enc2)
        enc2.refresh_from_db()

        self.assertEqual(enc2.hash_anterior, enc1.hash_atual)
        self.assertNotEqual(enc2.hash_atual, enc1.hash_atual)

    def test_documento_ja_finalizado_nao_e_reatribuido(self):
        """O documento fiscal é imutável: uma segunda chamada não deve
        gerar novo número nem nova assinatura."""
        enc = _criar_encomenda()
        fiscal.finalizar_documento_fiscal(enc)
        enc.refresh_from_db()
        numero_original = enc.numero_documento
        hash_original = enc.hash_atual

        fiscal.finalizar_documento_fiscal(enc)
        enc.refresh_from_db()

        self.assertEqual(enc.numero_documento, numero_original)
        self.assertEqual(enc.hash_atual, hash_original)

    def test_extrair_hash_curto(self):
        # Assinatura fictícia de 40 caracteres (a-j repetido em blocos de 10)
        assinatura = base64.b64encode(b'0123456789' * 4).decode('ascii')
        curto = fiscal.extrair_hash_curto(assinatura)
        esperado = ''.join(assinatura[p] for p in (0, 10, 20, 30))
        self.assertEqual(curto, esperado)
        self.assertEqual(len(curto), 4)


def _criar_item(enc, nome='Produto Teste', qty=1, preco=1000):
    ItemEncomenda.objects.create(
        encomenda=enc, nome_produto=nome,
        preco_unitario=preco, quantidade=qty,
    )


class SaftExportTests(TestCase):

    ns = {'s': 'urn:OECD:StandardAuditFile-Tax:AO_1.01_01'}

    def setUp(self):
        fiscal._PRIVATE_KEY_CACHE = None

    def tearDown(self):
        fiscal._PRIVATE_KEY_CACHE = None

    def test_saft_xml_estrutura_base(self):
        enc = _criar_encomenda()
        _criar_item(enc)
        fiscal.finalizar_documento_fiscal(enc)
        enc.status = 'finalizada'
        enc.save(update_fields=['status'])
        enc.refresh_from_db()

        xml = gerar_saft_ao(date.today().replace(day=1), date.today())
        root = ET.fromstring(xml)

        self.assertEqual(root.tag, '{urn:OECD:StandardAuditFile-Tax:AO_1.01_01}AuditFile')
        self.assertIsNotNone(root.find('s:Header', self.ns))
        self.assertIsNotNone(root.find('s:MasterFiles', self.ns))
        self.assertIsNotNone(root.find('s:SourceDocuments', self.ns))

        vendas = root.find('s:SourceDocuments/s:SalesInvoices', self.ns)
        self.assertIsNotNone(vendas)
        self.assertEqual(vendas.find('s:NumberOfEntries', self.ns).text, '1')

    def test_saft_invoice_status_finalizada(self):
        enc = _criar_encomenda()
        _criar_item(enc)
        fiscal.finalizar_documento_fiscal(enc)
        enc.status = 'finalizada'
        enc.save(update_fields=['status'])
        enc.refresh_from_db()

        xml = gerar_saft_ao(date.today().replace(day=1), date.today())
        root = ET.fromstring(xml)

        status = root.find('s:SourceDocuments/s:SalesInvoices/s:Invoice/s:DocumentStatus/s:InvoiceStatus', self.ns)
        self.assertIsNotNone(status)
        self.assertEqual(status.text, 'N')

    def test_saft_invoice_status_cancelada(self):
        enc = _criar_encomenda(status='cancelada')
        _criar_item(enc)
        fiscal.finalizar_documento_fiscal(enc)
        enc.refresh_from_db()
        enc.status = 'cancelada'
        enc.save(update_fields=['status'])

        xml = gerar_saft_ao(date.today().replace(day=1), date.today())
        root = ET.fromstring(xml)

        status = root.find('s:SourceDocuments/s:SalesInvoices/s:Invoice/s:DocumentStatus/s:InvoiceStatus', self.ns)
        self.assertIsNotNone(status)
        self.assertEqual(status.text, 'A')

    def test_saft_periodo_sem_documentos(self):
        xml = gerar_saft_ao(date(2099, 1, 1), date(2099, 12, 31))
        root = ET.fromstring(xml)

        vendas = root.find('s:SourceDocuments/s:SalesInvoices', self.ns)
        self.assertEqual(vendas.find('s:NumberOfEntries', self.ns).text, '0')

    def test_saft_inclui_finalizadas_e_canceladas(self):
        enc1 = _criar_encomenda()
        _criar_item(enc1)
        fiscal.finalizar_documento_fiscal(enc1)
        enc1.status = 'finalizada'
        enc1.save(update_fields=['status'])
        enc1.refresh_from_db()

        enc2 = _criar_encomenda()
        _criar_item(enc2)
        fiscal.finalizar_documento_fiscal(enc2)
        enc2.status = 'cancelada'
        enc2.save(update_fields=['status'])
        enc2.refresh_from_db()

        xml = gerar_saft_ao(date.today().replace(day=1), date.today())
        root = ET.fromstring(xml)

        vendas = root.find('s:SourceDocuments/s:SalesInvoices', self.ns)
        self.assertEqual(vendas.find('s:NumberOfEntries', self.ns).text, '2')


class CadeiaHashTests(TestCase):

    def setUp(self):
        fiscal._PRIVATE_KEY_CACHE = None

    def tearDown(self):
        fiscal._PRIVATE_KEY_CACHE = None

    def test_cadeia_valida_sem_quebras(self):
        enc1 = _criar_encomenda()
        fiscal.finalizar_documento_fiscal(enc1)
        enc1.refresh_from_db()

        enc2 = _criar_encomenda()
        fiscal.finalizar_documento_fiscal(enc2)
        enc2.refresh_from_db()

        resultado = fiscal.verificar_cadeia_hash()
        self.assertTrue(resultado['valida'])
        self.assertEqual(resultado['total'], 2)
        self.assertEqual(len(resultado['quebras']), 0)

    def test_cadeia_vazia(self):
        resultado = fiscal.verificar_cadeia_hash()
        self.assertTrue(resultado['valida'])
        self.assertEqual(resultado['total'], 0)


class NotaCreditoTests(TestCase):

    def setUp(self):
        fiscal._PRIVATE_KEY_CACHE = None
        from django.contrib.auth.models import User
        self.user = User.objects.create_user('admin', password='pass', is_staff=True)

    def tearDown(self):
        fiscal._PRIVATE_KEY_CACHE = None

    def test_emitir_nota_credito_atribui_numero_e_hash(self):
        from loja.models import NotaCredito
        from decimal import Decimal

        enc = _criar_encomenda()
        _criar_item(enc)
        fiscal.finalizar_documento_fiscal(enc)
        enc.refresh_from_db()

        nc = fiscal.emitir_nota_credito(
            factura=enc, motivo='anulacao',
            valor=enc.total(), emitido_por=self.user,
        )
        self.assertTrue(nc.numero_documento.startswith('NC '))
        self.assertIsNotNone(nc.data_emissao)
        self.assertTrue(nc.hash_atual)
        self.assertEqual(len(nc.hash_curto), 4)

    def test_emitir_nota_credito_regista_log(self):
        from loja.models import NotaCredito, LogAuditoria

        enc = _criar_encomenda()
        _criar_item(enc)
        fiscal.finalizar_documento_fiscal(enc)
        enc.refresh_from_db()

        fiscal.emitir_nota_credito(
            factura=enc, motivo='correcao',
            valor=enc.total(), emitido_por=self.user,
        )
        log = LogAuditoria.objects.filter(acao='rectificacao')
        self.assertEqual(log.count(), 1)

    def test_emitir_nota_credito_sem_factura_finalizada_erro(self):
        enc = _criar_encomenda()
        with self.assertRaises(ValueError):
            fiscal.emitir_nota_credito(enc, 'anulacao', 100)

    def test_numeracao_nota_credito_sequencial(self):
        from loja.models import NotaCredito

        enc = _criar_encomenda()
        _criar_item(enc)
        fiscal.finalizar_documento_fiscal(enc)
        enc.refresh_from_db()

        nc1 = fiscal.emitir_nota_credito(enc, 'anulacao', enc.total())
        nc2 = fiscal.emitir_nota_credito(enc, 'correcao', enc.total())

        seq1 = int(nc1.numero_documento.rsplit('/', 1)[-1])
        seq2 = int(nc2.numero_documento.rsplit('/', 1)[-1])
        self.assertEqual(seq2, seq1 + 1)


class LogAuditoriaTests(TestCase):

    def test_log_criado_correctamente(self):
        from loja.models import LogAuditoria
        from django.contrib.auth.models import User

        user = User.objects.create_user('test', password='pass', is_staff=True)
        log = LogAuditoria.objects.create(
            utilizador=user, acao='login',
            descricao='Login efectuado',
            ip='127.0.0.1',
        )
        self.assertEqual(log.acao, 'login')
        self.assertEqual(log.ip, '127.0.0.1')
        self.assertIn('Login', str(log))

    def test_log_sem_utilizador(self):
        from loja.models import LogAuditoria
        log = LogAuditoria.objects.create(
            acao='backup', descricao='Backup automático',
        )
        self.assertIsNone(log.utilizador)
        self.assertEqual(log.acao, 'backup')


class RegistoBackupTests(TestCase):

    def test_backup_registado(self):
        from loja.models import RegistoBackup
        backup = RegistoBackup.objects.create(
            resultado='sucesso', ficheiro='/tmp/backup.json',
            tamanho_bytes=1024,
        )
        self.assertEqual(backup.resultado, 'sucesso')
        self.assertIn('Sucesso', str(backup))


class SerieDocumentalTests(TestCase):

    def test_serie_criada(self):
        from loja.models import SerieDocumental
        serie = SerieDocumental.objects.create(serie='FT', ano=2026, numero_actual=10)
        self.assertEqual(serie.serie, 'FT')
        self.assertTrue(serie.activa)
        self.assertIn('FT', str(serie))

    def test_serie_ano_unico(self):
        from loja.models import SerieDocumental
        from django.db import IntegrityError

        SerieDocumental.objects.create(serie='FT', ano=2026)
        with self.assertRaises(Exception):
            SerieDocumental.objects.create(serie='FT', ano=2026)
