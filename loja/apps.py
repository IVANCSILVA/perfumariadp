from django.apps import AppConfig
from django.contrib import admin


class LojaConfig(AppConfig):
    name = 'loja'

    def ready(self):
        admin.site.site_header = 'Décent Privé — Gestão'
        admin.site.site_title = 'Décent Privé Admin'
        admin.site.index_title = 'Painel de Gestão da Perfumaria'

