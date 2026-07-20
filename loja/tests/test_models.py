from datetime import date, time
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from loja.models import (
    Banner,
    Categoria,
    Cliente,
    ConfigAniversario,
    Encomenda,
    FelicitacaoEnviada,
    Funcionario,
    HistoricoFidelidade,
    ItemEncomenda,
    MovimentoCaixa,
    MovimentoStock,
    Newsletter,
    NewsletterInscricao,
    Produto,
    Promocao,
    VisitaSite,
    validar_bi_angola,
    validar_telefone_angola,
)


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

class ValidarBIAngolaTest(TestCase):

    def test_valid_bi(self):
        validar_bi_angola('003456789LA045')

    def test_valid_bi_with_spaces(self):
        validar_bi_angola('003456789 LA 045')

    def test_valid_bi_lowercase(self):
        validar_bi_angola('003456789la045')

    def test_invalid_bi_too_short(self):
        with self.assertRaises(ValidationError):
            validar_bi_angola('12345')

    def test_invalid_bi_wrong_format(self):
        with self.assertRaises(ValidationError):
            validar_bi_angola('ABCDEFGHIJK123')

    def test_invalid_bi_missing_letters(self):
        with self.assertRaises(ValidationError):
            validar_bi_angola('003456789123045')

    def test_invalid_bi_extra_letters(self):
        with self.assertRaises(ValidationError):
            validar_bi_angola('003456789LAB045')


class ValidarTelefoneAngolaTest(TestCase):

    def test_valid_phone_9_digits(self):
        validar_telefone_angola('923456789')

    def test_valid_phone_with_plus244(self):
        validar_telefone_angola('+244923456789')

    def test_valid_phone_with_244(self):
        validar_telefone_angola('244923456789')

    def test_valid_phone_with_spaces(self):
        validar_telefone_angola('923 456 789')

    def test_valid_phone_with_dashes(self):
        validar_telefone_angola('923-456-789')

    def test_invalid_phone_does_not_start_with_9(self):
        with self.assertRaises(ValidationError):
            validar_telefone_angola('823456789')

    def test_invalid_phone_too_short(self):
        with self.assertRaises(ValidationError):
            validar_telefone_angola('92345')

    def test_invalid_phone_too_long(self):
        with self.assertRaises(ValidationError):
            validar_telefone_angola('92345678901')

    def test_invalid_phone_letters(self):
        with self.assertRaises(ValidationError):
            validar_telefone_angola('9ABCDEFGH')


# ---------------------------------------------------------------------------
# Categoria
# ---------------------------------------------------------------------------

class CategoriaModelTest(TestCase):

    def test_str(self):
        cat = Categoria.objects.create(nome='Perfumes', slug='perfumes')
        self.assertEqual(str(cat), 'Perfumes')

    def test_ordering(self):
        Categoria.objects.create(nome='Zulu', slug='zulu')
        Categoria.objects.create(nome='Alpha', slug='alpha')
        cats = list(Categoria.objects.values_list('nome', flat=True))
        self.assertEqual(cats, ['Alpha', 'Zulu'])


# ---------------------------------------------------------------------------
# Produto
# ---------------------------------------------------------------------------

class ProdutoModelTest(TestCase):

    def setUp(self):
        self.cat = Categoria.objects.create(nome='Masculino', slug='masculino')
        self.produto = Produto.objects.create(
            nome='Sauvage',
            marca='Dior',
            preco_venda=Decimal('40000.00'),
            preco_compra=Decimal('22000.00'),
            categoria=self.cat,
            genero='masculino',
            stock=10,
        )

    def test_str(self):
        self.assertEqual(str(self.produto), 'Sauvage — Dior')

    def test_preco_property(self):
        self.assertEqual(self.produto.preco, Decimal('40000.00'))

    def test_margem_property(self):
        self.assertEqual(self.produto.margem, Decimal('18000.00'))

    def test_margem_zero_when_preco_compra_is_zero(self):
        self.produto.preco_compra = Decimal('0')
        self.produto.save()
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.margem, Decimal('40000.00'))

    def test_calcular_stock_atual_empty(self):
        self.assertEqual(self.produto.calcular_stock_atual(), 0)

    def test_calcular_stock_atual_with_movements(self):
        MovimentoStock.objects.create(
            produto=self.produto, tipo='entrada',
            quantidade=20, descricao='Compra',
        )
        MovimentoStock.objects.create(
            produto=self.produto, tipo='saida',
            quantidade=-5, descricao='Venda',
        )
        self.assertEqual(self.produto.calcular_stock_atual(), 15)

    def test_ordering(self):
        p2 = Produto.objects.create(
            nome='Outro', marca='X', preco_venda=100, stock=1,
        )
        ids = list(Produto.objects.values_list('pk', flat=True))
        self.assertEqual(ids[0], p2.pk)


# ---------------------------------------------------------------------------
# Encomenda & ItemEncomenda
# ---------------------------------------------------------------------------

class EncomendaModelTest(TestCase):

    def setUp(self):
        self.encomenda = Encomenda.objects.create(
            nome_cliente='João', telefone='923456789',
        )
        self.produto = Produto.objects.create(
            nome='Perfume A', marca='Marca', preco_venda=Decimal('1000'),
            preco_compra=Decimal('500'), stock=10,
        )

    def test_str(self):
        self.assertIn('João', str(self.encomenda))
        self.assertIn(str(self.encomenda.pk), str(self.encomenda))

    def test_total_empty(self):
        self.assertEqual(self.encomenda.total(), 0)

    def test_total_with_items(self):
        ItemEncomenda.objects.create(
            encomenda=self.encomenda, produto=self.produto,
            nome_produto='Perfume A', preco_unitario=Decimal('1000'),
            quantidade=3,
        )
        ItemEncomenda.objects.create(
            encomenda=self.encomenda,
            nome_produto='Perfume B', preco_unitario=Decimal('500'),
            quantidade=2,
        )
        self.assertEqual(self.encomenda.total(), Decimal('4000'))

    def test_default_status(self):
        self.assertEqual(self.encomenda.status, 'em_curso')


class ItemEncomendaModelTest(TestCase):

    def setUp(self):
        self.encomenda = Encomenda.objects.create(
            nome_cliente='Maria', telefone='912345678',
        )
        self.item = ItemEncomenda.objects.create(
            encomenda=self.encomenda,
            nome_produto='Perfume X',
            preco_unitario=Decimal('2000'),
            preco_custo_unitario=Decimal('800'),
            quantidade=5,
        )

    def test_str(self):
        self.assertEqual(str(self.item), '5× Perfume X')

    def test_subtotal(self):
        self.assertEqual(self.item.subtotal(), Decimal('10000'))

    def test_custo_total(self):
        self.assertEqual(self.item.custo_total(), Decimal('4000'))

    def test_lucro(self):
        self.assertEqual(self.item.lucro(), Decimal('6000'))

    def test_custo_total_none_preco_custo(self):
        self.item.preco_custo_unitario = None
        self.assertEqual(self.item.custo_total(), 0)


# ---------------------------------------------------------------------------
# Cliente & HistoricoFidelidade
# ---------------------------------------------------------------------------

class ClienteModelTest(TestCase):

    def test_str(self):
        c = Cliente.objects.create(nome='Ana', telefone='934567890')
        self.assertEqual(str(c), 'Ana (934567890)')

    def test_ordering_by_pontos_desc(self):
        c1 = Cliente.objects.create(nome='A', telefone='911111111', pontos=10)
        c2 = Cliente.objects.create(nome='B', telefone='922222222', pontos=50)
        first = Cliente.objects.first()
        self.assertEqual(first.pk, c2.pk)


class HistoricoFidelidadeModelTest(TestCase):

    def test_str(self):
        c = Cliente.objects.create(nome='Carlos', telefone='955555555')
        h = HistoricoFidelidade.objects.create(
            cliente=c, tipo='ganho', pontos=100, descricao='Compra',
        )
        self.assertIn('Carlos', str(h))
        self.assertIn('100', str(h))


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

class BannerModelTest(TestCase):

    def test_str(self):
        b = Banner.objects.create(titulo='Verão 2026')
        self.assertEqual(str(b), 'Verão 2026')

    def test_ordering(self):
        Banner.objects.create(titulo='B', ordem=2)
        Banner.objects.create(titulo='A', ordem=1)
        first = Banner.objects.first()
        self.assertEqual(first.titulo, 'A')


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

class NewsletterModelTest(TestCase):

    def test_str(self):
        n = Newsletter.objects.create(email='test@example.com')
        self.assertEqual(str(n), 'test@example.com')


class NewsletterInscricaoModelTest(TestCase):

    def test_str_with_name(self):
        ni = NewsletterInscricao.objects.create(email='a@b.com', nome='Alice')
        self.assertEqual(str(ni), 'a@b.com (Alice)')

    def test_str_without_name(self):
        ni = NewsletterInscricao.objects.create(email='b@c.com')
        self.assertEqual(str(ni), 'b@c.com')

    def test_unique_email(self):
        NewsletterInscricao.objects.create(email='dup@test.com')
        with self.assertRaises(Exception):
            NewsletterInscricao.objects.create(email='dup@test.com')


# ---------------------------------------------------------------------------
# Funcionario
# ---------------------------------------------------------------------------

class FuncionarioModelTest(TestCase):

    def test_str(self):
        f = Funcionario.objects.create(
            nome='Pedro Silva', bi='003456789LA045',
            telefone='923456789', data_admissao='2024-01-01',
        )
        self.assertIn('Pedro Silva', str(f))

    def test_cargo_display(self):
        f = Funcionario.objects.create(
            nome='Ana', bi='003456789AB045', telefone='912345678',
            data_admissao='2024-01-01', cargo='gerente',
        )
        self.assertIn('Gerente', str(f))


# ---------------------------------------------------------------------------
# MovimentoCaixa
# ---------------------------------------------------------------------------

class MovimentoCaixaModelTest(TestCase):

    def test_str_entrada(self):
        m = MovimentoCaixa.objects.create(
            tipo='entrada', categoria='venda',
            valor=Decimal('5000'), descricao='Venda #1',
        )
        self.assertIn('+', str(m))
        self.assertIn('5000', str(m))

    def test_str_saida(self):
        m = MovimentoCaixa.objects.create(
            tipo='saida', categoria='despesa',
            valor=Decimal('2000'), descricao='Renda',
        )
        self.assertNotIn('+', str(m))


# ---------------------------------------------------------------------------
# VisitaSite
# ---------------------------------------------------------------------------

class VisitaSiteModelTest(TestCase):

    def test_str(self):
        v = VisitaSite.objects.create(ip='127.0.0.1')
        self.assertIn(str(v.pk), str(v))


# ---------------------------------------------------------------------------
# Promocao
# ---------------------------------------------------------------------------

class PromocaoModelTest(TestCase):

    def setUp(self):
        self.promo = Promocao.objects.create(
            nome='Dia da Mãe',
            tipo='dia',
            data_inicio=date(2026, 3, 8),
            data_fim=date(2026, 3, 8),
            desconto_percentagem=10,
            recorrente_anual=True,
            activo=True,
        )

    def test_str(self):
        self.assertEqual(str(self.promo), 'Dia da Mãe')

    def test_auto_slug(self):
        self.assertTrue(self.promo.slug)
        self.assertIn('dia-da-mae', self.promo.slug)

    def test_slug_uniqueness(self):
        p2 = Promocao.objects.create(
            nome='Dia da Mãe', tipo='dia',
            data_inicio=date(2026, 3, 8), data_fim=date(2026, 3, 8),
        )
        self.assertNotEqual(self.promo.slug, p2.slug)

    def test_esta_decorrer_same_day(self):
        self.assertTrue(self.promo.esta_decorrer(date(2026, 3, 8)))

    def test_esta_decorrer_outside(self):
        self.assertFalse(self.promo.esta_decorrer(date(2026, 5, 1)))

    def test_esta_decorrer_recorrente(self):
        self.assertTrue(self.promo.esta_decorrer(date(2027, 3, 8)))

    def test_esta_decorrer_range(self):
        promo = Promocao.objects.create(
            nome='Semana', tipo='semana',
            data_inicio=date(2026, 6, 1), data_fim=date(2026, 6, 7),
            recorrente_anual=True,
        )
        self.assertTrue(promo.esta_decorrer(date(2026, 6, 4)))
        self.assertFalse(promo.esta_decorrer(date(2026, 6, 10)))

    def test_esta_decorrer_cross_year(self):
        promo = Promocao.objects.create(
            nome='Natal-Ano Novo', tipo='campanha',
            data_inicio=date(2026, 12, 20), data_fim=date(2026, 1, 5),
            recorrente_anual=True,
        )
        self.assertTrue(promo.esta_decorrer(date(2027, 12, 25)))
        self.assertFalse(promo.esta_decorrer(date(2027, 6, 15)))

    def test_proxima_ocorrencia_non_recorrente(self):
        promo = Promocao.objects.create(
            nome='Unica', tipo='campanha',
            data_inicio=date(2026, 4, 1), data_fim=date(2026, 4, 10),
            recorrente_anual=False,
        )
        ini, fim = promo.proxima_ocorrencia(date(2027, 1, 1))
        self.assertEqual(ini, date(2026, 4, 1))
        self.assertEqual(fim, date(2026, 4, 10))

    def test_proxima_ocorrencia_recorrente_past(self):
        ini, fim = self.promo.proxima_ocorrencia(date(2026, 6, 1))
        self.assertEqual(ini.year, 2027)

    def test_proxima_ocorrencia_recorrente_future(self):
        ini, fim = self.promo.proxima_ocorrencia(date(2026, 1, 1))
        self.assertEqual(ini.month, 3)
        self.assertEqual(ini.year, 2026)

    def test_clean_invalid_dates(self):
        self.promo.data_fim = date(2026, 2, 1)
        with self.assertRaises(ValidationError):
            self.promo.clean()

    def test_clean_valid_dates(self):
        self.promo.data_fim = date(2026, 3, 8)
        self.promo.clean()

    def test_get_absolute_url(self):
        url = self.promo.get_absolute_url()
        self.assertIn(self.promo.slug, url)


# ---------------------------------------------------------------------------
# ConfigAniversario
# ---------------------------------------------------------------------------

class ConfigAniversarioModelTest(TestCase):

    def test_get_solo(self):
        config = ConfigAniversario.get_solo()
        self.assertEqual(config.pk, 1)
        config2 = ConfigAniversario.get_solo()
        self.assertEqual(config.pk, config2.pk)

    def test_str(self):
        config = ConfigAniversario.get_solo()
        self.assertEqual(str(config), 'Configuração de Aniversários')

    def test_horario_para_fixed(self):
        config = ConfigAniversario.get_solo()
        config.horario_aleatorio = False
        config.hora_envio = time(10, 0)
        config.save()
        c = Cliente.objects.create(nome='Test', telefone='911111111')
        self.assertEqual(config.horario_para(c, 'cliente'), time(10, 0))

    def test_horario_para_random(self):
        config = ConfigAniversario.get_solo()
        config.horario_aleatorio = True
        config.janela_inicio = time(9, 0)
        config.janela_fim = time(18, 0)
        config.save()
        c = Cliente.objects.create(nome='Test', telefone='911111111')
        hora = config.horario_para(c, 'cliente')
        self.assertGreaterEqual(hora.hour, 9)
        self.assertLess(hora.hour * 60 + hora.minute, 18 * 60)

    def test_horario_para_random_equal_window(self):
        config = ConfigAniversario.get_solo()
        config.horario_aleatorio = True
        config.janela_inicio = time(10, 0)
        config.janela_fim = time(10, 0)
        config.save()
        c = Cliente.objects.create(nome='Test', telefone='911111111')
        hora = config.horario_para(c, 'cliente')
        self.assertEqual(hora, time(10, 0))

    def test_render_mensagem_cliente(self):
        config = ConfigAniversario.get_solo()
        config.brinde_activo = False
        config.save()
        c = Cliente.objects.create(nome='Maria Silva', telefone='922222222')
        msg = config.render_mensagem(c, 'cliente')
        self.assertIn('Maria', msg)

    def test_render_mensagem_with_brinde(self):
        config = ConfigAniversario.get_solo()
        config.brinde_activo = True
        config.brinde_descricao = '10% desconto'
        config.save()
        c = Cliente.objects.create(nome='Ana', telefone='933333333')
        msg = config.render_mensagem(c, 'cliente')
        self.assertIn('10% desconto', msg)

    def test_render_mensagem_funcionario(self):
        config = ConfigAniversario.get_solo()
        f = Funcionario.objects.create(
            nome='Pedro', bi='003456789LA045', telefone='923456789',
            data_admissao='2024-01-01',
        )
        msg = config.render_mensagem(f, 'funcionario')
        self.assertIn('Pedro', msg)


# ---------------------------------------------------------------------------
# FelicitacaoEnviada
# ---------------------------------------------------------------------------

class FelicitacaoEnviadaModelTest(TestCase):

    def test_str(self):
        fe = FelicitacaoEnviada.objects.create(
            tipo='cliente', pessoa_id=1, nome='Ana',
            canal='email', sucesso=True, ano=2026,
        )
        self.assertIn('Ana', str(fe))
        self.assertIn('2026', str(fe))


# ---------------------------------------------------------------------------
# MovimentoStock
# ---------------------------------------------------------------------------

class MovimentoStockModelTest(TestCase):

    def setUp(self):
        self.produto = Produto.objects.create(
            nome='Perfume', marca='Marca', preco_venda=100, stock=0,
        )

    def test_str(self):
        m = MovimentoStock.objects.create(
            produto=self.produto, tipo='entrada',
            quantidade=10, descricao='Compra',
        )
        self.assertIn('10', str(m))
        self.assertIn('Perfume', str(m))

    def test_save_updates_product_stock(self):
        MovimentoStock.objects.create(
            produto=self.produto, tipo='entrada',
            quantidade=20, descricao='Compra',
        )
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.stock, 20)

    def test_save_updates_stock_after_sale(self):
        MovimentoStock.objects.create(
            produto=self.produto, tipo='entrada',
            quantidade=20, descricao='Compra',
        )
        MovimentoStock.objects.create(
            produto=self.produto, tipo='saida',
            quantidade=-5, descricao='Venda',
        )
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.stock, 15)
