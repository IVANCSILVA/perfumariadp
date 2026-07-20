"""Testes de conformidade fiscal AGT (Decreto Presidencial n.º 312/18):
numeração sequencial por série/ano e cadeia de assinatura digital."""
import base64

from django.test import TestCase, override_settings

from loja.models import Encomenda
from loja.utils import fiscal


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
