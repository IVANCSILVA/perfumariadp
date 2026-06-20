import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from loja.models import (
    Banner,
    Categoria,
    Cliente,
    ConfigAniversario,
    Encomenda,
    FelicitacaoEnviada,
    Funcionario,
    ItemEncomenda,
    MovimentoCaixa,
    MovimentoStock,
    Newsletter,
    NewsletterInscricao,
    Produto,
    Promocao,
    VisitaSite,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_staff_user(username='staff', **kwargs):
    return User.objects.create_user(
        username, password='testpass123', is_staff=True, **kwargs,
    )


def _create_superuser(username='admin'):
    return User.objects.create_superuser(username, 'admin@test.com', 'testpass123')


def _create_operador(username='operador'):
    user = User.objects.create_user(username, password='testpass123', is_staff=True)
    grupo, _ = Group.objects.get_or_create(name='Operador')
    user.groups.add(grupo)
    return user


def _create_produto(**kwargs):
    defaults = {
        'nome': 'Perfume Test', 'marca': 'Marca',
        'preco_venda': Decimal('10000'), 'preco_compra': Decimal('5000'),
        'stock': 20, 'disponivel': True,
    }
    defaults.update(kwargs)
    p = Produto.objects.create(**defaults)
    # Seed an entrada movement so MovimentoStock.save() recalculations stay positive
    if p.stock > 0:
        MovimentoStock.objects.create(
            produto=p, tipo='entrada',
            quantidade=p.stock, descricao='Stock inicial (test)',
        )
        p.refresh_from_db()
    return p


# ---------------------------------------------------------------------------
# Public views
# ---------------------------------------------------------------------------

class HomeViewTest(TestCase):

    def test_home_status_200(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)

    def test_home_creates_visit(self):
        self.client.get(reverse('home'))
        self.assertEqual(VisitaSite.objects.count(), 1)

    def test_home_no_duplicate_visit_same_session(self):
        self.client.get(reverse('home'))
        self.client.get(reverse('home'))
        self.assertEqual(VisitaSite.objects.count(), 1)


class ColecoesViewTest(TestCase):

    def test_colecoes_status_200(self):
        resp = self.client.get(reverse('colecoes'))
        self.assertEqual(resp.status_code, 200)


class PromocaoPublicaViewTest(TestCase):

    def test_existing_promo(self):
        promo = Promocao.objects.create(
            nome='Test Promo', tipo='dia',
            data_inicio=date.today(), data_fim=date.today(),
            activo=True, slug='test-promo',
        )
        resp = self.client.get(reverse('promocao_publica', args=['test-promo']))
        self.assertEqual(resp.status_code, 200)

    def test_nonexistent_promo_404(self):
        resp = self.client.get(reverse('promocao_publica', args=['nao-existe']))
        self.assertEqual(resp.status_code, 404)

    def test_inactive_promo_404(self):
        Promocao.objects.create(
            nome='Inactive', tipo='dia',
            data_inicio=date.today(), data_fim=date.today(),
            activo=False, slug='inactive',
        )
        resp = self.client.get(reverse('promocao_publica', args=['inactive']))
        self.assertEqual(resp.status_code, 404)


class StaticPublicViewsTest(TestCase):

    def test_galeria(self):
        self.assertEqual(self.client.get(reverse('galeria')).status_code, 200)

    def test_fidelidade(self):
        self.assertEqual(self.client.get(reverse('fidelidade')).status_code, 200)

    def test_contactos(self):
        self.assertEqual(self.client.get(reverse('contactos')).status_code, 200)

    def test_encomenda_sucesso(self):
        self.assertEqual(self.client.get(reverse('encomenda_sucesso')).status_code, 200)


# ---------------------------------------------------------------------------
# Online order (encomendas)
# ---------------------------------------------------------------------------

class EncomendasPublicViewTest(TestCase):

    def test_get_form(self):
        resp = self.client.get(reverse('encomendas'))
        self.assertEqual(resp.status_code, 200)

    def test_post_valid_order(self):
        itens = json.dumps([{'name': 'Perfume X', 'price': 5000, 'qty': 2}])
        resp = self.client.post(reverse('encomendas'), {
            'nome': 'Cliente Test', 'telefone': '923456789',
            'email': 'c@test.com', 'morada': 'Luanda',
            'itens_json': itens,
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Encomenda.objects.count(), 1)
        enc = Encomenda.objects.first()
        self.assertEqual(enc.nome_cliente, 'Cliente Test')
        self.assertEqual(enc.origem, 'online')
        self.assertEqual(enc.itens.count(), 1)

    def test_post_missing_required_fields(self):
        resp = self.client.post(reverse('encomendas'), {
            'nome': '', 'telefone': '',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Encomenda.objects.count(), 0)

    def test_post_invalid_json_still_creates_order(self):
        resp = self.client.post(reverse('encomendas'), {
            'nome': 'Test', 'telefone': '911111111',
            'itens_json': 'invalid-json',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Encomenda.objects.count(), 1)


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------

class NewsletterInscreverViewTest(TestCase):

    def test_post_valid(self):
        resp = self.client.post(
            reverse('newsletter_inscrever'),
            json.dumps({'email': 'new@test.com', 'nome': 'Test'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['ok'])
        self.assertTrue(NewsletterInscricao.objects.filter(email='new@test.com').exists())

    def test_post_duplicate(self):
        NewsletterInscricao.objects.create(email='dup@test.com')
        resp = self.client.post(
            reverse('newsletter_inscrever'),
            json.dumps({'email': 'dup@test.com'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 409)

    def test_post_missing_email(self):
        resp = self.client.post(
            reverse('newsletter_inscrever'),
            json.dumps({'nome': 'Test'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_get_not_allowed(self):
        resp = self.client.get(reverse('newsletter_inscrever'))
        self.assertEqual(resp.status_code, 405)


# ---------------------------------------------------------------------------
# Auth — Login / Logout
# ---------------------------------------------------------------------------

class GestaoLoginViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()

    def test_get_login_page(self):
        resp = self.client.get(reverse('gestao_login'))
        self.assertEqual(resp.status_code, 200)

    def test_valid_login_redirects(self):
        resp = self.client.post(reverse('gestao_login'), {
            'username': 'staff', 'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, reverse('gestao_dashboard'))

    def test_invalid_login(self):
        resp = self.client.post(reverse('gestao_login'), {
            'username': 'staff', 'password': 'wrong',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'inválidos')

    def test_already_authenticated_redirects(self):
        self.client.login(username='staff', password='testpass123')
        resp = self.client.get(reverse('gestao_login'))
        self.assertEqual(resp.status_code, 302)

    def test_non_staff_cannot_login(self):
        User.objects.create_user('normal', password='testpass123', is_staff=False)
        resp = self.client.post(reverse('gestao_login'), {
            'username': 'normal', 'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 200)


class GestaoLogoutViewTest(TestCase):

    def test_logout_redirects(self):
        staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')
        resp = self.client.get(reverse('gestao_logout'))
        self.assertEqual(resp.status_code, 302)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class GestaoDashboardViewTest(TestCase):

    def test_unauthenticated_redirect(self):
        resp = self.client.get(reverse('gestao_dashboard'))
        self.assertEqual(resp.status_code, 302)

    def test_authenticated_staff(self):
        _create_staff_user()
        self.client.login(username='staff', password='testpass123')
        resp = self.client.get(reverse('gestao_dashboard'))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# Vendas (Sales)
# ---------------------------------------------------------------------------

class GestaoVendasViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_list_vendas(self):
        resp = self.client.get(reverse('gestao_vendas'))
        self.assertEqual(resp.status_code, 200)


class GestaoVendaNovaViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')
        self.produto = _create_produto()

    def test_get_form(self):
        resp = self.client.get(reverse('gestao_venda_nova'))
        self.assertEqual(resp.status_code, 200)

    def test_post_valid_sale(self):
        resp = self.client.post(reverse('gestao_venda_nova'), {
            'nome_cliente': 'Cliente Balcão',
            'telefone': '923456789',
            'produto_id': [str(self.produto.pk)],
            'quantidade': ['2'],
            'preco_unitario': [str(self.produto.preco_venda)],
            'forma_pagamento': 'avista',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Encomenda.objects.count(), 1)
        enc = Encomenda.objects.first()
        self.assertEqual(enc.status, 'finalizada')
        self.assertEqual(enc.origem, 'balcao')
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.stock, 18)

    def test_post_no_items(self):
        resp = self.client.post(reverse('gestao_venda_nova'), {
            'nome_cliente': 'Test',
            'forma_pagamento': 'avista',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Encomenda.objects.count(), 0)

    def test_post_insufficient_stock(self):
        self.produto.stock = 1
        self.produto.save()
        resp = self.client.post(reverse('gestao_venda_nova'), {
            'nome_cliente': 'Test',
            'produto_id': [str(self.produto.pk)],
            'quantidade': ['5'],
            'preco_unitario': ['10000'],
            'forma_pagamento': 'avista',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Encomenda.objects.count(), 0)

    def test_post_parcelado_sale(self):
        resp = self.client.post(reverse('gestao_venda_nova'), {
            'nome_cliente': 'Cliente Parcela',
            'telefone': '923456789',
            'produto_id': [str(self.produto.pk)],
            'quantidade': ['1'],
            'preco_unitario': ['10000'],
            'forma_pagamento': 'parcelado',
            'valor_parcela1': '5000',
            'valor_parcela2': '5000',
        })
        self.assertEqual(resp.status_code, 302)
        enc = Encomenda.objects.first()
        self.assertEqual(enc.status, 'em_curso')
        self.assertEqual(enc.forma_pagamento, 'parcelado')
        self.assertTrue(enc.parcela1_paga)
        self.assertFalse(enc.parcela2_paga)


# ---------------------------------------------------------------------------
# Venda Detalhe
# ---------------------------------------------------------------------------

class GestaoVendaDetalheViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')
        self.produto = _create_produto()
        self.encomenda = Encomenda.objects.create(
            nome_cliente='Test', telefone='911111111', status='em_curso',
        )
        ItemEncomenda.objects.create(
            encomenda=self.encomenda, produto=self.produto,
            nome_produto='Perfume', preco_unitario=Decimal('10000'),
            quantidade=1,
        )

    def test_get_detalhe(self):
        resp = self.client.get(reverse('gestao_venda_detalhe', args=[self.encomenda.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_finalizar(self):
        resp = self.client.post(
            reverse('gestao_venda_detalhe', args=[self.encomenda.pk]),
            {'acao': 'finalizar'},
        )
        self.assertEqual(resp.status_code, 302)
        self.encomenda.refresh_from_db()
        self.assertEqual(self.encomenda.status, 'finalizada')

    def test_cancelar_requires_motivo(self):
        resp = self.client.post(
            reverse('gestao_venda_detalhe', args=[self.encomenda.pk]),
            {'acao': 'cancelar', 'motivo_cancelamento': ''},
        )
        self.encomenda.refresh_from_db()
        self.assertEqual(self.encomenda.status, 'em_curso')

    def test_cancelar_with_motivo(self):
        resp = self.client.post(
            reverse('gestao_venda_detalhe', args=[self.encomenda.pk]),
            {'acao': 'cancelar', 'motivo_cancelamento': 'Cliente desistiu'},
        )
        self.encomenda.refresh_from_db()
        self.assertEqual(self.encomenda.status, 'cancelada')
        self.assertEqual(self.encomenda.motivo_cancelamento, 'Cliente desistiu')

    def test_eliminar(self):
        pk = self.encomenda.pk
        resp = self.client.post(
            reverse('gestao_venda_detalhe', args=[pk]),
            {'acao': 'eliminar'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Encomenda.objects.filter(pk=pk).exists())


# ---------------------------------------------------------------------------
# Fatura
# ---------------------------------------------------------------------------

class GestaoFaturaViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_fatura_finalizada(self):
        enc = Encomenda.objects.create(
            nome_cliente='Test', telefone='911111111', status='finalizada',
        )
        ItemEncomenda.objects.create(
            encomenda=enc, nome_produto='P', preco_unitario=100, quantidade=1,
        )
        resp = self.client.get(reverse('gestao_fatura', args=[enc.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_fatura_avista_not_finalizada_redirects(self):
        enc = Encomenda.objects.create(
            nome_cliente='Test', telefone='911111111',
            status='em_curso', forma_pagamento='avista',
        )
        resp = self.client.get(reverse('gestao_fatura', args=[enc.pk]))
        self.assertEqual(resp.status_code, 302)


# ---------------------------------------------------------------------------
# Parcela2 Payment
# ---------------------------------------------------------------------------

class GestaoParcela2ViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')
        self.enc = Encomenda.objects.create(
            nome_cliente='Test', telefone='911111111',
            status='em_curso', forma_pagamento='parcelado',
            parcela1_paga=True, parcela2_paga=False,
        )
        ItemEncomenda.objects.create(
            encomenda=self.enc, nome_produto='P',
            preco_unitario=Decimal('10000'), quantidade=1,
        )

    def test_get_confirmation_page(self):
        resp = self.client.get(
            reverse('gestao_registar_pagamento_parcela2', args=[self.enc.pk]),
        )
        self.assertEqual(resp.status_code, 200)

    def test_post_finalizes_order(self):
        resp = self.client.post(
            reverse('gestao_registar_pagamento_parcela2', args=[self.enc.pk]),
        )
        self.assertEqual(resp.status_code, 302)
        self.enc.refresh_from_db()
        self.assertTrue(self.enc.parcela2_paga)
        self.assertEqual(self.enc.status, 'finalizada')


# ---------------------------------------------------------------------------
# Cancelar Encomenda
# ---------------------------------------------------------------------------

class GestaoCancelarEncomendaViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_cancel_finalizada_order(self):
        produto = _create_produto(stock=10)
        enc = Encomenda.objects.create(
            nome_cliente='Test', telefone='911111111', status='finalizada',
        )
        ItemEncomenda.objects.create(
            encomenda=enc, produto=produto,
            nome_produto='P', preco_unitario=100, quantidade=2,
        )
        stock_before = produto.stock
        resp = self.client.post(reverse('gestao_cancelar_encomenda', args=[enc.pk]))
        self.assertEqual(resp.status_code, 302)
        enc.refresh_from_db()
        self.assertEqual(enc.status, 'cancelada')
        produto.refresh_from_db()
        self.assertGreater(produto.stock, stock_before)

    def test_cancel_non_finalizada_fails(self):
        enc = Encomenda.objects.create(
            nome_cliente='Test', telefone='911111111', status='em_curso',
        )
        resp = self.client.post(reverse('gestao_cancelar_encomenda', args=[enc.pk]))
        self.assertEqual(resp.status_code, 302)
        enc.refresh_from_db()
        self.assertEqual(enc.status, 'em_curso')


# ---------------------------------------------------------------------------
# Produtos CRUD
# ---------------------------------------------------------------------------

class GestaoProdutosViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_list_produtos(self):
        resp = self.client.get(reverse('gestao_produtos'))
        self.assertEqual(resp.status_code, 200)

    def test_create_produto(self):
        resp = self.client.post(reverse('gestao_produto_criar'), {
            'nome': 'Novo Perfume', 'marca': 'NovaMarca',
            'preco_venda': '15000', 'preco_compra': '8000',
            'tipo': 'unissex', 'stock': '10', 'disponivel': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Produto.objects.filter(nome='Novo Perfume').exists())

    def test_create_produto_missing_name(self):
        resp = self.client.post(reverse('gestao_produto_criar'), {
            'nome': '', 'marca': 'X', 'preco_venda': '100',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Produto.objects.count(), 0)

    def test_edit_produto(self):
        p = _create_produto()
        resp = self.client.post(reverse('gestao_produto_editar', args=[p.pk]), {
            'nome': 'Updated', 'marca': 'M',
            'preco_venda': '20000', 'preco_compra': '10000',
            'tipo': 'masculino', 'stock': '5',
        })
        self.assertEqual(resp.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.nome, 'Updated')

    def test_delete_produto(self):
        p = _create_produto()
        resp = self.client.post(reverse('gestao_produto_apagar', args=[p.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Produto.objects.filter(pk=p.pk).exists())

    def test_detalhe_produto(self):
        p = _create_produto()
        resp = self.client.get(reverse('gestao_produto_detalhe', args=[p.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_operador_blocked_from_create(self):
        op = _create_operador()
        self.client.login(username='operador', password='testpass123')
        resp = self.client.get(reverse('gestao_produto_criar'))
        self.assertEqual(resp.status_code, 302)


# ---------------------------------------------------------------------------
# Produto - Entrada de Stock
# ---------------------------------------------------------------------------

class GestaoProdutoEntradaStockViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')
        self.produto = _create_produto(stock=10)

    def test_get_form(self):
        resp = self.client.get(
            reverse('gestao_produto_entrada_stock', args=[self.produto.pk]),
        )
        self.assertEqual(resp.status_code, 200)

    def test_post_valid_entry(self):
        resp = self.client.post(
            reverse('gestao_produto_entrada_stock', args=[self.produto.pk]),
            {'quantidade': '5', 'descricao': 'Recebimento fornecedor'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(MovimentoStock.objects.filter(produto=self.produto).exists())

    def test_post_missing_quantity(self):
        resp = self.client.post(
            reverse('gestao_produto_entrada_stock', args=[self.produto.pk]),
            {'quantidade': '', 'descricao': 'Test'},
        )
        self.assertEqual(resp.status_code, 200)

    def test_post_zero_quantity(self):
        resp = self.client.post(
            reverse('gestao_produto_entrada_stock', args=[self.produto.pk]),
            {'quantidade': '0', 'descricao': 'Test'},
        )
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# Funcionarios CRUD
# ---------------------------------------------------------------------------

class GestaoFuncionariosViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_list_funcionarios(self):
        resp = self.client.get(reverse('gestao_funcionarios'))
        self.assertEqual(resp.status_code, 200)

    def test_create_funcionario(self):
        resp = self.client.post(reverse('gestao_funcionario_criar'), {
            'nome': 'Pedro Silva', 'bi': '003456789LA045',
            'telefone': '923456789', 'cargo': 'vendedor',
            'turno': 'manha', 'data_admissao': '2024-06-01',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Funcionario.objects.filter(nome='Pedro Silva').exists())

    def test_create_funcionario_invalid_bi(self):
        resp = self.client.post(reverse('gestao_funcionario_criar'), {
            'nome': 'Test', 'bi': 'INVALID',
            'telefone': '923456789', 'data_admissao': '2024-01-01',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Funcionario.objects.count(), 0)

    def test_edit_funcionario(self):
        f = Funcionario.objects.create(
            nome='Original', bi='003456789LA045', telefone='923456789',
            data_admissao='2024-01-01',
        )
        resp = self.client.post(reverse('gestao_funcionario_editar', args=[f.pk]), {
            'nome': 'Edited', 'bi': '003456789LA045',
            'telefone': '923456789', 'cargo': 'gerente',
            'turno': 'integral', 'data_admissao': '2024-01-01',
        })
        self.assertEqual(resp.status_code, 302)
        f.refresh_from_db()
        self.assertEqual(f.nome, 'Edited')

    def test_delete_funcionario(self):
        f = Funcionario.objects.create(
            nome='Del', bi='003456789LA045', telefone='923456789',
            data_admissao='2024-01-01',
        )
        resp = self.client.post(reverse('gestao_funcionario_apagar', args=[f.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Funcionario.objects.filter(pk=f.pk).exists())

    def test_detalhe_funcionario(self):
        f = Funcionario.objects.create(
            nome='Det', bi='003456789LA045', telefone='923456789',
            data_admissao='2024-01-01',
        )
        resp = self.client.get(reverse('gestao_funcionario_detalhe', args=[f.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_operador_blocked_from_funcionarios(self):
        _create_operador()
        self.client.login(username='operador', password='testpass123')
        resp = self.client.get(reverse('gestao_funcionarios'))
        self.assertEqual(resp.status_code, 302)


# ---------------------------------------------------------------------------
# Clientes CRUD
# ---------------------------------------------------------------------------

class GestaoClientesViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_list_clientes(self):
        resp = self.client.get(reverse('gestao_clientes'))
        self.assertEqual(resp.status_code, 200)

    def test_create_cliente(self):
        resp = self.client.post(reverse('gestao_cliente_criar'), {
            'nome': 'Maria', 'telefone': '923456789',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Cliente.objects.filter(nome='Maria').exists())

    def test_create_cliente_missing_name(self):
        resp = self.client.post(reverse('gestao_cliente_criar'), {
            'nome': '', 'telefone': '923456789',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Cliente.objects.count(), 0)

    def test_edit_cliente(self):
        c = Cliente.objects.create(nome='Old', telefone='911111111')
        resp = self.client.post(reverse('gestao_cliente_editar', args=[c.pk]), {
            'nome': 'New', 'telefone': '911111111',
        })
        self.assertEqual(resp.status_code, 302)
        c.refresh_from_db()
        self.assertEqual(c.nome, 'New')

    def test_delete_cliente(self):
        c = Cliente.objects.create(nome='Del', telefone='922222222')
        resp = self.client.post(reverse('gestao_cliente_apagar', args=[c.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Cliente.objects.filter(pk=c.pk).exists())

    def test_detalhe_cliente(self):
        c = Cliente.objects.create(nome='Det', telefone='933333333')
        resp = self.client.get(reverse('gestao_cliente_detalhe', args=[c.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_duplicate_phone_rejected(self):
        Cliente.objects.create(nome='First', telefone='944444444')
        resp = self.client.post(reverse('gestao_cliente_criar'), {
            'nome': 'Second', 'telefone': '944444444',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Cliente.objects.count(), 1)


# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------

class GestaoCategoriasViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_list_and_create(self):
        resp = self.client.post(reverse('gestao_categorias'), {'nome': 'Nicho'})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Categoria.objects.filter(nome='Nicho').exists())

    def test_create_empty_name(self):
        resp = self.client.post(reverse('gestao_categorias'), {'nome': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Categoria.objects.count(), 0)

    def test_delete_categoria(self):
        cat = Categoria.objects.create(nome='Del', slug='del')
        resp = self.client.post(reverse('gestao_categoria_apagar', args=[cat.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Categoria.objects.filter(pk=cat.pk).exists())


# ---------------------------------------------------------------------------
# Caixa
# ---------------------------------------------------------------------------

class GestaoCaixaViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_caixa_page(self):
        resp = self.client.get(reverse('gestao_caixa'))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# Financeiro — Entradas / Saídas
# ---------------------------------------------------------------------------

class GestaoFinanceiroViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_entrada_page(self):
        resp = self.client.get(reverse('gestao_caixa_entrada'))
        self.assertEqual(resp.status_code, 200)

    def test_saida_page(self):
        resp = self.client.get(reverse('gestao_caixa_saida'))
        self.assertEqual(resp.status_code, 200)

    def test_create_entrada(self):
        resp = self.client.post(reverse('gestao_caixa_entrada'), {
            'descricao': 'Reforço', 'categoria': 'reforco',
            'valor': '50000',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(MovimentoCaixa.objects.filter(tipo='entrada').exists())

    def test_create_saida(self):
        resp = self.client.post(reverse('gestao_caixa_saida'), {
            'descricao': 'Renda', 'categoria': 'renda',
            'valor': '30000',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(MovimentoCaixa.objects.filter(tipo='saida').exists())

    def test_create_entrada_missing_fields(self):
        resp = self.client.post(reverse('gestao_caixa_entrada'), {
            'descricao': '', 'categoria': 'reforco', 'valor': '0',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(MovimentoCaixa.objects.count(), 0)


# ---------------------------------------------------------------------------
# Relatorio
# ---------------------------------------------------------------------------

class GestaoRelatorioViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_relatorio_default(self):
        resp = self.client.get(reverse('gestao_relatorio'))
        self.assertEqual(resp.status_code, 200)

    def test_relatorio_all_periods(self):
        for p in ['hoje', 'semana', 'mes', 'todos']:
            resp = self.client.get(reverse('gestao_relatorio'), {'periodo': p})
            self.assertEqual(resp.status_code, 200, f'Failed for periodo={p}')


# ---------------------------------------------------------------------------
# Lucro
# ---------------------------------------------------------------------------

class GestaoLucroViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_lucro_page(self):
        resp = self.client.get(reverse('gestao_lucro'))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# Promocoes management
# ---------------------------------------------------------------------------

class GestaoPromocoesViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_list_promocoes(self):
        resp = self.client.get(reverse('gestao_promocoes'))
        self.assertEqual(resp.status_code, 200)

    def test_create_promocao(self):
        resp = self.client.post(reverse('gestao_promocao_criar'), {
            'nome': 'Campanha Test', 'tipo': 'campanha',
            'data_inicio': '2026-07-01', 'data_fim': '2026-07-15',
            'desconto_percentagem': '15', 'cor': 'amber', 'icone': '🎁',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Promocao.objects.filter(nome='Campanha Test').exists())

    def test_edit_promocao(self):
        p = Promocao.objects.create(
            nome='Old', tipo='dia',
            data_inicio=date(2026, 1, 1), data_fim=date(2026, 1, 2),
        )
        resp = self.client.post(reverse('gestao_promocao_editar', args=[p.pk]), {
            'nome': 'New', 'tipo': 'dia',
            'data_inicio': '2026-01-01', 'data_fim': '2026-01-02',
            'desconto_percentagem': '0', 'cor': 'sky', 'icone': '🎁',
        })
        self.assertEqual(resp.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.nome, 'New')

    def test_delete_promocao(self):
        p = Promocao.objects.create(
            nome='Del', tipo='dia',
            data_inicio=date(2026, 1, 1), data_fim=date(2026, 1, 2),
        )
        resp = self.client.post(reverse('gestao_promocao_apagar', args=[p.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Promocao.objects.filter(pk=p.pk).exists())

    def test_toggle_promocao(self):
        p = Promocao.objects.create(
            nome='Toggle', tipo='dia',
            data_inicio=date(2026, 1, 1), data_fim=date(2026, 1, 2),
            activo=True,
        )
        resp = self.client.post(reverse('gestao_promocao_toggle', args=[p.pk]))
        self.assertEqual(resp.status_code, 302)
        p.refresh_from_db()
        self.assertFalse(p.activo)


# ---------------------------------------------------------------------------
# Encomendas (online orders management)
# ---------------------------------------------------------------------------

class GestaoEncomendasViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_list_encomendas(self):
        resp = self.client.get(reverse('gestao_encomendas'))
        self.assertEqual(resp.status_code, 200)

    def test_update_status(self):
        enc = Encomenda.objects.create(
            nome_cliente='Online', telefone='911111111', status='em_curso',
        )
        ItemEncomenda.objects.create(
            encomenda=enc, nome_produto='P', preco_unitario=100, quantidade=1,
        )
        resp = self.client.post(reverse('gestao_encomendas'), {
            'encomenda_id': enc.pk, 'status': 'finalizada',
        })
        self.assertEqual(resp.status_code, 302)
        enc.refresh_from_db()
        self.assertEqual(enc.status, 'finalizada')


# ---------------------------------------------------------------------------
# Barcode API
# ---------------------------------------------------------------------------

class GestaoBarcodeAPIViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_found(self):
        p = _create_produto(codigo_barras='1234567890123')
        resp = self.client.get(reverse('gestao_api_barcode'), {'codigo': '1234567890123'})
        data = resp.json()
        self.assertTrue(data['encontrado'])
        self.assertEqual(data['id'], p.pk)

    def test_not_found(self):
        resp = self.client.get(reverse('gestao_api_barcode'), {'codigo': 'INVALID'})
        data = resp.json()
        self.assertFalse(data['encontrado'])

    def test_missing_code(self):
        resp = self.client.get(reverse('gestao_api_barcode'))
        data = resp.json()
        self.assertFalse(data['encontrado'])


# ---------------------------------------------------------------------------
# Aniversarios Config
# ---------------------------------------------------------------------------

class GestaoAniversariosConfigViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_get_config(self):
        resp = self.client.get(reverse('gestao_aniversarios_config'))
        self.assertEqual(resp.status_code, 200)

    def test_post_update_config(self):
        resp = self.client.post(reverse('gestao_aniversarios_config'), {
            'hora_envio': '11:00', 'janela_inicio': '08:00',
            'janela_fim': '17:00', 'activo': 'on',
            'enviar_email': 'on', 'enviar_sms': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        config = ConfigAniversario.get_solo()
        self.assertTrue(config.activo)


# ---------------------------------------------------------------------------
# Aniversariante Enviar
# ---------------------------------------------------------------------------

class GestaoAniversarianteEnviarViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_send_to_cliente(self):
        c = Cliente.objects.create(
            nome='Birthday Client', telefone='911111111',
            email='bday@test.com',
        )
        ConfigAniversario.get_solo()
        resp = self.client.post(
            reverse('gestao_aniversariante_enviar', args=['cliente', c.pk]),
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(FelicitacaoEnviada.objects.filter(pessoa_id=c.pk).exists())

    def test_send_to_funcionario(self):
        f = Funcionario.objects.create(
            nome='Birthday Emp', bi='003456789LA045',
            telefone='923456789', email='emp@test.com',
            data_admissao='2024-01-01',
        )
        ConfigAniversario.get_solo()
        resp = self.client.post(
            reverse('gestao_aniversariante_enviar', args=['funcionario', f.pk]),
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(FelicitacaoEnviada.objects.filter(pessoa_id=f.pk).exists())

    def test_invalid_tipo_redirects(self):
        resp = self.client.post(
            reverse('gestao_aniversariante_enviar', args=['invalid', 1]),
        )
        self.assertEqual(resp.status_code, 302)

    def test_get_not_post_redirects(self):
        c = Cliente.objects.create(nome='Test', telefone='955555555')
        resp = self.client.get(
            reverse('gestao_aniversariante_enviar', args=['cliente', c.pk]),
        )
        self.assertEqual(resp.status_code, 302)


# ---------------------------------------------------------------------------
# Newsletter Gestao
# ---------------------------------------------------------------------------

class NewsletterGestaoViewTest(TestCase):

    def setUp(self):
        self.staff = _create_staff_user()
        self.client.login(username='staff', password='testpass123')

    def test_list_inscritos(self):
        NewsletterInscricao.objects.create(email='a@test.com')
        resp = self.client.get(reverse('newsletter_gestao'))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# _registar_venda_no_caixa helper
# ---------------------------------------------------------------------------

class RegistarVendaNoCaixaTest(TestCase):

    def test_creates_entry_for_finalizada(self):
        from loja.views import _registar_venda_no_caixa
        enc = Encomenda.objects.create(
            nome_cliente='Test', telefone='911111111', status='finalizada',
        )
        ItemEncomenda.objects.create(
            encomenda=enc, nome_produto='P',
            preco_unitario=Decimal('5000'), quantidade=2,
        )
        result = _registar_venda_no_caixa(enc)
        self.assertIsNotNone(result)
        self.assertEqual(result.tipo, 'entrada')
        self.assertEqual(result.valor, Decimal('10000'))

    def test_ignores_non_finalizada(self):
        from loja.views import _registar_venda_no_caixa
        enc = Encomenda.objects.create(
            nome_cliente='Test', telefone='911111111', status='em_curso',
        )
        result = _registar_venda_no_caixa(enc)
        self.assertIsNone(result)

    def test_idempotent(self):
        from loja.views import _registar_venda_no_caixa
        enc = Encomenda.objects.create(
            nome_cliente='Test', telefone='911111111', status='finalizada',
        )
        ItemEncomenda.objects.create(
            encomenda=enc, nome_produto='P',
            preco_unitario=Decimal('5000'), quantidade=1,
        )
        _registar_venda_no_caixa(enc)
        _registar_venda_no_caixa(enc)
        self.assertEqual(
            MovimentoCaixa.objects.filter(encomenda=enc).count(), 1,
        )

    def test_backfills_preco_custo(self):
        from loja.views import _registar_venda_no_caixa
        produto = _create_produto(preco_compra=Decimal('3000'))
        enc = Encomenda.objects.create(
            nome_cliente='Test', telefone='911111111', status='finalizada',
        )
        item = ItemEncomenda.objects.create(
            encomenda=enc, produto=produto, nome_produto='P',
            preco_unitario=Decimal('5000'), preco_custo_unitario=0,
            quantidade=1,
        )
        _registar_venda_no_caixa(enc)
        item.refresh_from_db()
        self.assertEqual(item.preco_custo_unitario, Decimal('3000'))


# ---------------------------------------------------------------------------
# _is_operador / _block_operador
# ---------------------------------------------------------------------------

class IsOperadorTest(TestCase):

    def test_operador_is_blocked(self):
        op = _create_operador()
        from loja.views import _is_operador
        self.assertTrue(_is_operador(op))

    def test_staff_not_operador(self):
        staff = _create_staff_user('plain_staff')
        from loja.views import _is_operador
        self.assertFalse(_is_operador(staff))

    def test_superuser_not_operador(self):
        admin = _create_superuser()
        from loja.views import _is_operador
        self.assertFalse(_is_operador(admin))

    def test_none_user(self):
        from loja.views import _is_operador
        self.assertFalse(_is_operador(None))


# ---------------------------------------------------------------------------
# Funcionario - criar utilizador
# ---------------------------------------------------------------------------

class GestaoFuncionarioCriarUtilizadorViewTest(TestCase):

    def setUp(self):
        self.admin = _create_superuser('admin')
        self.client.login(username='admin', password='testpass123')
        self.funcionario = Funcionario.objects.create(
            nome='Pedro', bi='003456789LA045', telefone='923456789',
            email='pedro@test.com', data_admissao='2024-01-01',
        )

    def test_get_form(self):
        resp = self.client.get(
            reverse('gestao_funcionario_criar_utilizador', args=[self.funcionario.pk]),
        )
        self.assertEqual(resp.status_code, 200)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_create_user_success(self):
        resp = self.client.post(
            reverse('gestao_funcionario_criar_utilizador', args=[self.funcionario.pk]),
            {
                'username': 'pedro_user', 'password': 'secret123',
                'password2': 'secret123', 'nivel': 'gerente',
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(User.objects.filter(username='pedro_user').exists())
        self.funcionario.refresh_from_db()
        self.assertIsNotNone(self.funcionario.utilizador)

    def test_create_user_password_mismatch(self):
        resp = self.client.post(
            reverse('gestao_funcionario_criar_utilizador', args=[self.funcionario.pk]),
            {
                'username': 'test_user', 'password': 'secret123',
                'password2': 'different', 'nivel': 'gerente',
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='test_user').exists())

    def test_non_superuser_blocked(self):
        staff = _create_staff_user('plain')
        self.client.login(username='plain', password='testpass123')
        resp = self.client.post(
            reverse('gestao_funcionario_criar_utilizador', args=[self.funcionario.pk]),
            {
                'username': 'new', 'password': 'secret123',
                'password2': 'secret123', 'nivel': 'gerente',
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(User.objects.filter(username='new').exists())
