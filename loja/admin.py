from django.contrib import admin
from .models import (
    Categoria, Produto, Encomenda, ItemEncomenda,
    Cliente, HistoricoFidelidade, Banner, Newsletter,
    Funcionario, VisitaSite, Promocao,
)
from .models import NewsletterInscricao
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django import forms
from django.contrib import messages
from .views import enviar_email_newsletter
# ---------------------------------------------------------------------------
# NewsletterInscricao - Admin com ação de envio de e-mail
# ---------------------------------------------------------------------------
class EnviarNewsletterForm(forms.Form):
    assunto = forms.CharField(max_length=200)
    mensagem = forms.CharField(widget=forms.Textarea)

@admin.register(NewsletterInscricao)
class NewsletterInscricaoAdmin(admin.ModelAdmin):
    list_display = ('email', 'nome', 'data_inscricao', 'ativo')
    actions = ['enviar_email_newsletter_action']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('enviar-newsletter/', self.admin_site.admin_view(self.enviar_newsletter_view), name='enviar-newsletter'),
        ]
        return custom_urls + urls

    def enviar_email_newsletter_action(self, request, queryset):
        return redirect('admin:enviar-newsletter')
    enviar_email_newsletter_action.short_description = 'Enviar e-mail para todos os inscritos ativos'

    def enviar_newsletter_view(self, request):
        if request.method == 'POST':
            form = EnviarNewsletterForm(request.POST)
            if form.is_valid():
                try:
                    enviados = enviar_email_newsletter(
                        form.cleaned_data['assunto'],
                        form.cleaned_data['mensagem']
                    )
                    self.message_user(request, f'E-mails enviados: {enviados}')
                except Exception as exc:
                    self.message_user(
                        request,
                        f'Erro ao enviar newsletter: {exc}',
                        level=messages.ERROR,
                    )
                return redirect('..')
        else:
            form = EnviarNewsletterForm()
        context = dict(
            self.admin_site.each_context(request),
            form=form,
        )
        return render(request, 'admin/enviar_newsletter.html', context)

# ---------------------------------------------------------------------------
# Categorias
# ---------------------------------------------------------------------------
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'marca', 'quantidade', 'categoria', 'tipo', 'preco_venda', 'preco_compra', 'stock', 'disponivel')
    list_filter = ('tipo', 'categoria', 'disponivel')
    search_fields = ('nome', 'marca')
    list_editable = ('preco_venda', 'preco_compra', 'stock', 'disponivel')
    readonly_fields = ('criado_em', 'atualizado_em')
    fieldsets = (
        ('Informações Gerais', {
            'fields': ('nome', 'marca', 'quantidade', 'descricao', 'categoria', 'tipo')
        }),
        ('Preço e Stock', {
            'fields': ('preco_venda', 'preco_compra', 'stock', 'disponivel')
        }),
        ('Imagem', {
            'fields': ('imagem',)
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )


# ---------------------------------------------------------------------------
# Encomendas
# ---------------------------------------------------------------------------
class ItemEncomendaInline(admin.TabularInline):
    model = ItemEncomenda
    extra = 1
    readonly_fields = ('subtotal',)
    fields = ('produto', 'nome_produto', 'preco_unitario', 'quantidade', 'subtotal')


@admin.register(Encomenda)
class EncomendaAdmin(admin.ModelAdmin):
    list_display = ('pk', 'nome_cliente', 'telefone', 'status', 'total', 'criado_em')
    list_filter = ('status',)
    search_fields = ('nome_cliente', 'telefone', 'email')
    list_editable = ('status',)
    readonly_fields = ('criado_em', 'atualizado_em', 'total')
    inlines = [ItemEncomendaInline]
    fieldsets = (
        ('Cliente', {
            'fields': ('nome_cliente', 'telefone', 'email', 'morada')
        }),
        ('Estado', {
            'fields': ('status', 'notas', 'total')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',),
        }),
    )


# ---------------------------------------------------------------------------
# Clientes & Fidelidade
# ---------------------------------------------------------------------------
class HistoricoInline(admin.TabularInline):
    model = HistoricoFidelidade
    extra = 1
    readonly_fields = ('data',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'email', 'pontos', 'membro_desde')
    search_fields = ('nome', 'telefone', 'email')
    readonly_fields = ('membro_desde',)
    inlines = [HistoricoInline]


# ---------------------------------------------------------------------------
# Banners
# ---------------------------------------------------------------------------
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'ordem', 'activo')
    list_editable = ('ordem', 'activo')


# ---------------------------------------------------------------------------
# Newsletter
# ---------------------------------------------------------------------------
@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscrito_em', 'activo')
    list_filter = ('activo',)
    search_fields = ('email',)
    readonly_fields = ('subscrito_em',)


# ---------------------------------------------------------------------------
# Newsletter Inscricao
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Funcionários
# ---------------------------------------------------------------------------
@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'bi', 'telefone', 'cargo', 'turno', 'salario', 'data_nascimento', 'data_admissao', 'activo')
    list_filter = ('cargo', 'turno', 'activo')
    search_fields = ('nome', 'bi', 'telefone', 'email')
    list_editable = ('activo',)
    readonly_fields = ('criado_em',)
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('nome', 'foto', 'bi', 'telefone', 'email', 'data_nascimento')
        }),
        ('Função', {
            'fields': ('cargo', 'turno', 'salario', 'data_admissao', 'activo')
        }),
        ('Acesso ao Sistema', {
            'fields': ('utilizador',),
            'description': 'Associe uma conta de utilizador Django a este funcionário (apenas se estiver activo).',
        }),
        ('Observações', {
            'fields': ('notas',)
        }),
        ('Registo', {
            'fields': ('criado_em',),
            'classes': ('collapse',),
        }),
    )




@admin.register(VisitaSite)
class VisitaSiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'criado_em', 'ip', 'sessao', 'referer')
    list_filter = ('criado_em',)
    search_fields = ('ip', 'sessao', 'user_agent', 'referer')
    readonly_fields = ('ip', 'user_agent', 'referer', 'sessao', 'criado_em')


@admin.register(Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'data_inicio', 'data_fim', 'desconto_percentagem', 'mostrar_carrossel', 'mostrar_landing', 'recorrente_anual', 'activo')
    list_filter = ('tipo', 'activo', 'recorrente_anual', 'mostrar_carrossel', 'mostrar_landing')
    search_fields = ('nome', 'descricao', 'subtitulo')
    list_editable = ('desconto_percentagem', 'activo')
    ordering = ('data_inicio',)
    prepopulated_fields = {'slug': ('nome',)}
    filter_horizontal = ('produtos',)

