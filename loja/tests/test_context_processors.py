from django.contrib.auth.models import Group, User
from django.test import RequestFactory, TestCase

from loja.context_processors import encomendas_online_pendentes, nivel_acesso
from loja.models import Encomenda


class EncomendaOnlinePendentesTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.staff = User.objects.create_user('staff', password='pass', is_staff=True)

    def test_non_gestao_path_returns_empty(self):
        request = self.factory.get('/loja/')
        request.user = self.staff
        self.assertEqual(encomendas_online_pendentes(request), {})

    def test_anonymous_user_returns_empty(self):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get('/gestao/')
        request.user = AnonymousUser()
        self.assertEqual(encomendas_online_pendentes(request), {})

    def test_non_staff_returns_empty(self):
        normal = User.objects.create_user('normal', password='pass', is_staff=False)
        request = self.factory.get('/gestao/')
        request.user = normal
        self.assertEqual(encomendas_online_pendentes(request), {})

    def test_counts_online_pending_orders(self):
        Encomenda.objects.create(
            nome_cliente='Online', telefone='911111111',
            status='em_curso', vendido_por=None,
        )
        Encomenda.objects.create(
            nome_cliente='Balcao', telefone='922222222',
            status='em_curso', vendido_por=self.staff,
        )
        Encomenda.objects.create(
            nome_cliente='Done', telefone='933333333',
            status='finalizada', vendido_por=None,
        )
        request = self.factory.get('/gestao/dashboard/')
        request.user = self.staff
        ctx = encomendas_online_pendentes(request)
        self.assertEqual(ctx['pedidos_online_pendentes'], 1)


class NivelAcessoTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_anonymous_user(self):
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get('/')
        request.user = AnonymousUser()
        ctx = nivel_acesso(request)
        self.assertFalse(ctx['is_operador'])
        self.assertFalse(ctx['is_gerente'])
        self.assertFalse(ctx['is_admin_user'])

    def test_superuser(self):
        admin = User.objects.create_superuser('admin', 'a@b.com', 'pass')
        request = self.factory.get('/')
        request.user = admin
        ctx = nivel_acesso(request)
        self.assertTrue(ctx['is_admin_user'])
        self.assertFalse(ctx['is_operador'])
        self.assertFalse(ctx['is_gerente'])

    def test_operador(self):
        user = User.objects.create_user('op', password='pass', is_staff=True)
        grupo = Group.objects.create(name='Operador')
        user.groups.add(grupo)
        request = self.factory.get('/')
        request.user = user
        ctx = nivel_acesso(request)
        self.assertTrue(ctx['is_operador'])
        self.assertFalse(ctx['is_gerente'])
        self.assertFalse(ctx['is_admin_user'])

    def test_gerente(self):
        user = User.objects.create_user('gerente', password='pass', is_staff=True)
        request = self.factory.get('/')
        request.user = user
        ctx = nivel_acesso(request)
        self.assertFalse(ctx['is_operador'])
        self.assertTrue(ctx['is_gerente'])
        self.assertFalse(ctx['is_admin_user'])

    def test_no_user_attribute(self):
        request = self.factory.get('/')
        request.user = None
        ctx = nivel_acesso(request)
        self.assertFalse(ctx['is_operador'])
        self.assertFalse(ctx['is_gerente'])
        self.assertFalse(ctx['is_admin_user'])
