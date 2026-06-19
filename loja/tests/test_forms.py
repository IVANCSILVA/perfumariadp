from django.test import TestCase

from loja.forms import NewsletterInscricaoForm
from loja.models import NewsletterInscricao


class NewsletterInscricaoFormTest(TestCase):

    def test_valid_form(self):
        form = NewsletterInscricaoForm(data={'email': 'test@example.com', 'nome': 'Maria'})
        self.assertTrue(form.is_valid())

    def test_valid_form_without_name(self):
        form = NewsletterInscricaoForm(data={'email': 'test@example.com'})
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        form = NewsletterInscricaoForm(data={'email': 'not-an-email'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_missing_email(self):
        form = NewsletterInscricaoForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_email(self):
        NewsletterInscricao.objects.create(email='dup@example.com')
        form = NewsletterInscricaoForm(data={'email': 'dup@example.com'})
        self.assertFalse(form.is_valid())

    def test_save_creates_object(self):
        form = NewsletterInscricaoForm(data={'email': 'new@example.com', 'nome': 'Ana'})
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.email, 'new@example.com')
        self.assertEqual(obj.nome, 'Ana')
        self.assertTrue(NewsletterInscricao.objects.filter(email='new@example.com').exists())

    def test_fields(self):
        form = NewsletterInscricaoForm()
        self.assertEqual(list(form.fields.keys()), ['email', 'nome'])
