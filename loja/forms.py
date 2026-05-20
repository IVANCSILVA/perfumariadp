from django import forms
from .models import NewsletterInscricao

class NewsletterInscricaoForm(forms.ModelForm):
    class Meta:
        model = NewsletterInscricao
        fields = ['email', 'nome']
