from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User


class NewsletterInscricao(models.Model):
    email = models.EmailField(unique=True, verbose_name='E-mail')
    nome = models.CharField(max_length=150, blank=True, verbose_name='Nome (opcional)')
    data_inscricao = models.DateTimeField(auto_now_add=True, verbose_name='Data de inscrição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Inscrição na Newsletter'
        verbose_name_plural = 'Inscrições na Newsletter'
        ordering = ['-data_inscricao']

    def __str__(self):
        return f"{self.email} ({self.nome})" if self.nome else self.email


from .utils.validators import validar_bi_angola, validar_telefone_angola, validar_nib_angola, validar_iban_angola  # noqa: F401, E402
from .utils.slug import gerar_slug_unico  # noqa: F401, E402


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Produto(models.Model):
    GENERO_CHOICES = [
        ('masculino', 'Masculino'),
        ('feminino', 'Feminino'),
        ('unissex', 'Unissex'),
    ]
    CONCENTRACAO_CHOICES = [
        ('pf',        'Parfum / Extrait de Parfum'),
        ('edp',       'Eau de Parfum (EDP)'),
        ('edt',       'Eau de Toilette (EDT)'),
        ('edc',       'Eau de Cologne (EDC)'),
        ('body_mist', 'Body Mist / Splash'),
    ]

    nome = models.CharField(max_length=200)
    marca = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    preco_venda = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Preço de venda ao cliente (Kz)'
    )
    preco_compra = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Preço de custo / compra ao fornecedor (Kz)'
    )
    quantidade = models.CharField(
        max_length=20, blank=True,
        help_text='Volume da embalagem, ex: 50ml, 100ml'
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='produtos',
        help_text='Segmento livre: Nicho, Designer, Lançamentos, etc. (gerido em Categorias)'
    )
    genero = models.CharField(
        max_length=20, choices=GENERO_CHOICES, default='unissex',
        verbose_name='Género',
        help_text='Público-alvo do perfume.'
    )
    concentracao = models.CharField(
        max_length=20, choices=CONCENTRACAO_CHOICES, blank=True,
        verbose_name='Concentração',
        help_text='Tipo de concentração da fragrância (EDP, EDT, Parfum, etc.).'
    )
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)
    codigo_barras = models.CharField(
        max_length=100, blank=True, null=True, unique=True,
        help_text='EAN-13, EAN-8, Code 128, QR Code, etc.'
    )
    essencia = models.TextField(
        blank=True,
        help_text='Notas olfativas: topo, coração e fundo (ex: Bergamota, Jasmim, Sândalo)'
    )
    stock = models.PositiveIntegerField(default=0)
    disponivel = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.nome} — {self.marca}'

    @property
    def preco(self):
        """Retrocompatibilidade: alias para preco_venda."""
        return self.preco_venda

    @property
    def margem(self):
        if self.preco_venda and self.preco_compra is not None:
            return self.preco_venda - self.preco_compra
        return 0

    def calcular_stock_atual(self):
        """
        Calcula o stock actual com base nos movimentos registados.
        Fonte de verdade: MovimentoStock
        """
        from django.db.models import Sum, F
        resultado = self.movimentos_stock.aggregate(
            total=Sum('quantidade')
        )
        return resultado['total'] or 0


class Encomenda(models.Model):
    PAGAMENTO_CHOICES = [
        ('avista', 'À Vista'),
        ('parcelado', 'Parcelado (2x)')
    ]
    ORIGEM_CHOICES = [
        ('balcao', 'Balcão'),
        ('online', 'Online')
    ]

    forma_pagamento = models.CharField(
        max_length=20,
        choices=PAGAMENTO_CHOICES,
        default='avista',
        verbose_name='Forma de Pagamento'
    )
    valor_parcela1 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Valor 1ª Parcela',
        help_text='Primeira parcela (mínimo 50% do total)'
    )
    valor_parcela2 = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name='Valor 2ª Parcela'
    )
    parcela1_paga = models.BooleanField(default=False, verbose_name='1ª Parcela Paga')
    parcela2_paga = models.BooleanField(default=False, verbose_name='2ª Parcela Paga')
    data_proxima_parcela = models.DateField(
        null=True, blank=True,
        verbose_name='Data da Próxima Parcela',
        help_text='Data prevista para o pagamento da próxima parcela'
    )

    STATUS_CHOICES = [
        ('em_curso', 'Em Curso'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]

    nome_cliente = models.CharField(max_length=200)
    telefone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    morada = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_curso')
    origem = models.CharField(
        max_length=20, choices=ORIGEM_CHOICES, default='balcao',
        verbose_name='Origem da Encomenda',
        help_text='Indica se a venda foi feita no balcão ou online'
    )
    vendido_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='vendas', verbose_name='Vendido por'
    )
    notas = models.TextField(blank=True)
    motivo_cancelamento = models.TextField(
        blank=True, null=True,
        verbose_name='Motivo do Cancelamento',
        help_text='Explicação do motivo do cancelamento da venda'
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Encomenda'
        verbose_name_plural = 'Encomendas'
        ordering = ['-criado_em']

    def __str__(self):
        return f'Encomenda #{self.pk} — {self.nome_cliente}'

    def total(self):
        return sum(item.subtotal() for item in self.itens.all())
    total.short_description = 'Total (Kz)'


class ItemEncomenda(models.Model):
    encomenda = models.ForeignKey(Encomenda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True)
    nome_produto = models.CharField(max_length=200)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    preco_custo_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Snapshot do preço de compra na altura da venda (para cálculo de lucro).'
    )
    quantidade = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Item de Encomenda'
        verbose_name_plural = 'Itens de Encomenda'

    def subtotal(self):
        return self.preco_unitario * self.quantidade
    subtotal.short_description = 'Subtotal (Kz)'

    def custo_total(self):
        return (self.preco_custo_unitario or 0) * self.quantidade

    def lucro(self):
        return self.subtotal() - self.custo_total()

    def __str__(self):
        return f'{self.quantidade}× {self.nome_produto}'


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=30, unique=True)
    email = models.EmailField(blank=True)
    data_nascimento = models.DateField(null=True, blank=True, help_text='Data de nascimento do cliente')
    pontos = models.PositiveIntegerField(default=0)
    membro_desde = models.DateField(auto_now_add=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-pontos']

    def __str__(self):
        return f'{self.nome} ({self.telefone})'


class HistoricoFidelidade(models.Model):
    TIPO_CHOICES = [
        ('ganho', 'Pontos Ganhos'),
        ('gasto', 'Pontos Gastos'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='historico')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    pontos = models.IntegerField()
    descricao = models.CharField(max_length=200)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Fidelidade'
        verbose_name_plural = 'Histórico de Fidelidade'
        ordering = ['-data']

    def __str__(self):
        return f'{self.cliente.nome}: {self.tipo} {self.pontos} pts'


class Banner(models.Model):
    titulo = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=300, blank=True)
    texto_botao = models.CharField(max_length=50, default='Ver Colecção')
    link_botao = models.CharField(max_length=200, default='#produtos')
    imagem = models.ImageField(upload_to='banners/', blank=True, null=True)
    cor_fundo = models.CharField(
        max_length=7, default='#1c1917',
        help_text='Cor de fundo em hexadecimal, ex: #1c1917'
    )
    ordem = models.PositiveSmallIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
        ordering = ['ordem']

    def __str__(self):
        return self.titulo


class Newsletter(models.Model):
    email = models.EmailField(unique=True)
    subscrito_em = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Subscrição Newsletter'
        verbose_name_plural = 'Subscrições Newsletter'
        ordering = ['-subscrito_em']

    def __str__(self):
        return self.email


class Funcionario(models.Model):
    CARGO_CHOICES = [
        ('gerente', 'Gerente'),
        ('operador_caixa', 'Operador de Caixa'),
        ('seguranca', 'Segurança'),
        ('limpeza', 'Limpeza'),
    ]
    CARGO_COM_COMISSAO = {'operador_caixa'}

    TURNO_CHOICES = [
        ('manha', 'Manhã'),
        ('tarde', 'Tarde'),
        ('noite', 'Noite'),
        ('integral', 'Integral'),
    ]

    nome = models.CharField(max_length=200)
    foto = models.ImageField(
        upload_to='funcionarios/', null=True, blank=True, verbose_name='Foto'
    )
    bi = models.CharField(
        max_length=20, unique=True, verbose_name='Nº BI',
        help_text='Formato: 9 dígitos + 2 letras + 3 dígitos (ex: 003456789LA045)',
        validators=[validar_bi_angola]
    )
    telefone = models.CharField(
        max_length=20,
        help_text='Formato: 9XX XXX XXX',
        validators=[validar_telefone_angola]
    )
    email = models.EmailField(blank=True)
    cargo = models.CharField(max_length=20, choices=CARGO_CHOICES, default='operador')
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES, default='integral')
    salario = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Salário mensal em Kz'
    )
    percentagem_comissao = models.DecimalField(
        max_digits=5, decimal_places=2, default=2,
        verbose_name='Comissão por Vendas (%)',
        help_text='Percentagem do valor total das vendas do mês, adicionada ao salário base. Default: 2%.'
    )
    subsidio_alimentacao = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Subsídio de Alimentação (Kz)',
        help_text='Valor mensal do subsídio de alimentação (não sujeito a INSS nem IRT).'
    )
    subsidio_transporte = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Subsídio de Transporte (Kz)',
        help_text='Valor mensal do subsídio de transporte (não sujeito a INSS nem IRT).'
    )

    BANCO_CHOICES = [
        ('bai', 'BAI — Banco Angolano de Investimentos'),
        ('bic', 'BIC — Banco BIC'),
        ('bfa', 'BFA — Banco de Fomento Angola'),
        ('atlantico', 'Banco Atlântico'),
        ('bci', 'BCI — Banco de Crédito Investimento'),
        ('millennium', 'Millennium Atlântico'),
        ('sol', 'Banco SOL'),
        ('caixanga', 'Caixa Geral — Angola'),
        ('keve', 'Banco Keve'),
        ('yetu', 'Banco Yetu'),
        ('standard', 'Standard Bank Angola'),
        ('vtb', 'VTB Bank Angola'),
        ('otro', 'Outro'),
    ]

    banco = models.CharField(
        max_length=20, choices=BANCO_CHOICES, blank=True,
        verbose_name='Banco', help_text='Banco onde o funcionário recebe o salário.'
    )
    nib = models.CharField(
        max_length=21, blank=True,
        verbose_name='NIB (21 dígitos)',
        help_text='Número de Identificação Bancária: 21 dígitos (ex: 004400006729503010102).',
        validators=[validar_nib_angola]
    )
    iban = models.CharField(
        max_length=25, blank=True,
        verbose_name='IBAN',
        help_text='IBAN angolano: AO + 23 dígitos, total 25 caracteres (ex: AO06004400006729503010102).',
        validators=[validar_iban_angola]
    )

    data_nascimento = models.DateField(null=True, blank=True, help_text='Data de nascimento do funcionário')
    data_admissao = models.DateField(help_text='Data de entrada na empresa')
    activo = models.BooleanField(default=True)
    utilizador = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='funcionario',
        help_text='Conta de utilizador associada (apenas para funcionários activos)'
    )
    notas = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} — {self.get_cargo_display()}'


class PagamentoSalario(models.Model):
    """Registo mensal do processamento salarial de um funcionário."""

    MESES = [
        (1,'Janeiro'),(2,'Fevereiro'),(3,'Março'),(4,'Abril'),
        (5,'Maio'),(6,'Junho'),(7,'Julho'),(8,'Agosto'),
        (9,'Setembro'),(10,'Outubro'),(11,'Novembro'),(12,'Dezembro'),
    ]

    funcionario = models.ForeignKey(
        Funcionario, on_delete=models.PROTECT,
        related_name='pagamentos_salario', verbose_name='Funcionário'
    )
    mes = models.PositiveSmallIntegerField(choices=MESES, verbose_name='Mês')
    ano = models.PositiveSmallIntegerField(verbose_name='Ano')

    salario_base = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Salário Base (Kz)',
        help_text='Snapshot do salário base na altura do processamento.'
    )
    percentagem_comissao = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='% Comissão (snapshot)'
    )
    total_vendas_mes = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='Total de Vendas no Mês (Kz)'
    )
    comissao_valor = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Valor de Comissão (Kz)'
    )
    salario_bruto = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Salário Bruto (Kz)',
        help_text='Salário base + comissão.'
    )
    taxa_inss = models.DecimalField(
        max_digits=5, decimal_places=2, default=3,
        verbose_name='Taxa INSS Trabalhador (%)',
        help_text='Em Angola, a contribuição do trabalhador para o INSS é 3% do bruto.'
    )
    desconto_inss = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Desconto INSS (Kz)'
    )
    desconto_irt = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='IRT (Kz)',
        help_text='Imposto sobre o Rendimento do Trabalho, calculado progressivamente (Tabela A).'
    )
    subsidio_alimentacao = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Subsídio de Alimentação (Kz)',
        help_text='Snapshot do subsídio de alimentação na altura do processamento.'
    )
    subsidio_transporte = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Subsídio de Transporte (Kz)',
        help_text='Snapshot do subsídio de transporte na altura do processamento.'
    )
    custo_inss_patronal = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='INSS Patronal (Kz)',
        help_text='Contribuição da entidade patronal: 8% do bruto. Custo da empresa, não deduzido do salário.'
    )
    salario_liquido = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Salário Líquido (Kz)',
        help_text='Bruto − INSS − IRT + Subsídios.'
    )
    pago = models.BooleanField(default=False, verbose_name='Pago')
    data_pagamento = models.DateField(
        null=True, blank=True, verbose_name='Data de Pagamento'
    )
    processado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='salarios_processados', verbose_name='Processado por'
    )
    notas = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pagamento de Salário'
        verbose_name_plural = 'Pagamentos de Salários'
        ordering = ['-ano', '-mes', 'funcionario__nome']
        unique_together = [('funcionario', 'mes', 'ano')]

    def __str__(self):
        return f'{self.funcionario.nome} — {self.mes:02d}/{self.ano}'

    def get_mes_display_str(self):
        return dict(self.MESES).get(self.mes, str(self.mes))


class MovimentoCaixa(models.Model):
    """Movimentos financeiros do caixa (entradas e saídas de dinheiro)."""
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    ]

    CATEGORIA_CHOICES = [
        ('venda', 'Venda'),
        ('reforco', 'Reforço de Caixa'),
        ('investimento', 'Investimento'),
        ('outro_ganho', 'Outro Ganho'),
        ('despesa', 'Despesa Operacional'),
        ('salario', 'Salário'),
        ('renda', 'Renda / Aluguer'),
        ('utilidades', 'Água / Luz / Internet'),
        ('fornecedor', 'Pagamento a Fornecedor'),
        ('imposto', 'Imposto / Taxa'),
        ('manutencao', 'Manutenção'),
        ('outro_custo', 'Outro Custo'),
    ]

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    descricao = models.CharField(max_length=255)
    data = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True)
    criado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimentos_caixa'
    )
    encomenda = models.ForeignKey(
        'Encomenda', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimentos_caixa',
        help_text='Venda associada (preenchido automaticamente para entradas de venda).'
    )

    class Meta:
        verbose_name = 'Movimento de Caixa'
        verbose_name_plural = 'Movimentos de Caixa'
        ordering = ['-data']

    def __str__(self):
        sinal = '+' if self.tipo == 'entrada' else '−'
        return f'{sinal}{self.valor} Kz — {self.descricao}'


class VisitaSite(models.Model):
    """Regista cada acesso à página inicial do site."""
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    referer = models.URLField(blank=True)
    sessao = models.CharField(max_length=40, blank=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Visita ao Site'
        verbose_name_plural = 'Visitas ao Site'
        ordering = ['-criado_em']

    def __str__(self):
        return f'Visita {self.pk} — {self.criado_em:%d/%m/%Y %H:%M}'


class Promocao(models.Model):
    """Datas e épocas promocionais (Dia da Mãe, Mês dos Namorados, etc.)."""

    TIPO_CHOICES = [
        ('dia', 'Dia comemorativo'),
        ('semana', 'Semana temática'),
        ('mes', 'Mês temático'),
        ('campanha', 'Campanha pontual'),
    ]

    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='dia')
    descricao = models.TextField(blank=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    desconto_percentagem = models.PositiveIntegerField(
        default=0,
        help_text='Percentagem de desconto associada (0 a 100). 0 = sem desconto automático.',
    )
    cor = models.CharField(
        max_length=20,
        default='amber',
        help_text='Cor de destaque (amber, rose, sky, emerald, violet, stone).',
    )
    icone = models.CharField(
        max_length=10,
        blank=True,
        default='🎁',
        help_text='Emoji ou ícone curto.',
    )
    recorrente_anual = models.BooleanField(
        default=True,
        help_text='Se marcado, repete-se todos os anos nas mesmas datas.',
    )
    activo = models.BooleanField(default=True)

    # Publicação na loja pública
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    produtos = models.ManyToManyField(
        Produto, blank=True, related_name='promocoes',
        help_text='Produtos abrangidos por esta promoção.'
    )
    imagem = models.ImageField(upload_to='promocoes/', blank=True, null=True,
        help_text='Imagem para o carrossel e cabeçalho da promoção.')
    subtitulo = models.CharField(max_length=200, blank=True,
        help_text='Linha curta exibida acima do título no carrossel.')
    texto_botao = models.CharField(max_length=50, default='Ver Promoção')
    link_botao = models.CharField(max_length=200, blank=True,
        help_text='Deixe em branco para usar a página automática da promoção.')
    mostrar_carrossel = models.BooleanField(default=False,
        help_text='Apresentar como slide no carrossel da página inicial.')
    mostrar_landing = models.BooleanField(default=False,
        help_text='Apresentar como secção/colecção na página inicial e em /colecções.')

    criado_em = models.DateTimeField(auto_now_add=True)
    actualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Promoção'
        verbose_name_plural = 'Promoções'
        ordering = ['data_inicio', 'nome']

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = gerar_slug_unico(Promocao, self.nome, instancia=self)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('promocao_publica', args=[self.slug])

    def clean(self):
        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError({'data_fim': 'A data de fim deve ser posterior ou igual à de início.'})

    def esta_decorrer(self, hoje=None):
        from datetime import date
        hoje = hoje or date.today()
        ini, fim = self.data_inicio, self.data_fim
        if self.recorrente_anual:
            ini = ini.replace(year=hoje.year)
            fim = fim.replace(year=hoje.year)
            if fim < ini:
                # campanha que atravessa o ano (ex.: 20 Dez → 5 Jan)
                fim = fim.replace(year=hoje.year + 1)
        return ini <= hoje <= fim

    def proxima_ocorrencia(self, hoje=None):
        """Devolve (data_inicio, data_fim) da próxima ocorrência."""
        from datetime import date
        hoje = hoje or date.today()
        ini, fim = self.data_inicio, self.data_fim
        if not self.recorrente_anual:
            return ini, fim
        ini = ini.replace(year=hoje.year)
        fim = fim.replace(year=hoje.year)
        if fim < hoje:
            ini = ini.replace(year=hoje.year + 1)
            fim = fim.replace(year=hoje.year + 1)
        return ini, fim


# ---------------------------------------------------------------------------
# Aniversariantes — configuração e log
# ---------------------------------------------------------------------------

MENSAGEM_CLIENTE_DEFAULT = (
    "Olá {nome}! 🎉\n\n"
    "A equipa Décent Privé deseja-lhe um feliz aniversário cheio de fragrâncias "
    "e momentos especiais. Que este novo ano lhe traga muita saúde, alegria e perfume!\n\n"
    "{brinde}"
    "Com carinho,\nDécent Privé Perfumaria"
)

MENSAGEM_FUNCIONARIO_DEFAULT = (
    "Parabéns, {nome}! 🥂\n\n"
    "Toda a família Décent Privé deseja-lhe um feliz aniversário. "
    "Obrigado por fazer parte desta equipa e por ajudar a perfumar o dia a dia "
    "dos nossos clientes.\n\n"
    "{brinde}"
    "Um forte abraço,\nDirecção Décent Privé"
)


class ConfigAniversario(models.Model):
    """Configuração singleton para felicitações automáticas."""

    mensagem_cliente = models.TextField(
        default=MENSAGEM_CLIENTE_DEFAULT,
        help_text='Use {nome} e {brinde} como marcadores.'
    )
    mensagem_funcionario = models.TextField(
        default=MENSAGEM_FUNCIONARIO_DEFAULT,
        help_text='Use {nome} e {brinde} como marcadores.'
    )
    hora_envio = models.TimeField(default='10:00', help_text='Hora a que as felicitações são enviadas (modo fixo).')
    horario_aleatorio = models.BooleanField(
        default=False,
        help_text='Se activo, cada pessoa recebe a uma hora aleatória dentro da janela definida.'
    )
    janela_inicio = models.TimeField(default='09:00', help_text='Início da janela de envio (modo aleatório).')
    janela_fim = models.TimeField(default='18:00', help_text='Fim da janela de envio (modo aleatório).')
    enviar_email = models.BooleanField(default=True)
    enviar_sms = models.BooleanField(default=True)
    brinde_activo = models.BooleanField(default=False, help_text='Oferecer brinde no aniversário.')
    brinde_descricao = models.CharField(
        max_length=200, blank=True,
        default='Como presente, oferecemos-lhe 10% de desconto em qualquer compra durante o seu mês de aniversário.',
        help_text='Texto incluído na mensagem quando o brinde estiver activo.'
    )
    activo = models.BooleanField(default=True, help_text='Ligar/desligar todo o sistema de felicitações.')
    actualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração de Aniversários'
        verbose_name_plural = 'Configuração de Aniversários'

    def __str__(self):
        return 'Configuração de Aniversários'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def horario_para(self, pessoa, tipo):
        """Devolve a hora (datetime.time) a que esta pessoa deve receber felicitação hoje.

        - Modo fixo: devolve sempre `hora_envio`.
        - Modo aleatório: hora deterministica por pessoa+ano dentro de [janela_inicio, janela_fim].
        """
        from datetime import time as _time
        if not self.horario_aleatorio:
            return self.hora_envio
        import hashlib
        from datetime import date as _date
        ano = _date.today().year
        chave = f'{tipo}-{pessoa.pk}-{ano}'.encode('utf-8')
        h = int(hashlib.sha256(chave).hexdigest(), 16)
        ini_min = self.janela_inicio.hour * 60 + self.janela_inicio.minute
        fim_min = self.janela_fim.hour * 60 + self.janela_fim.minute
        if fim_min <= ini_min:
            return self.janela_inicio
        minuto = ini_min + (h % (fim_min - ini_min))
        return _time(hour=minuto // 60, minute=minuto % 60)

    def render_mensagem(self, pessoa, tipo):
        """tipo: 'cliente' | 'funcionario'. Substitui {nome} e {brinde}."""
        template = self.mensagem_cliente if tipo == 'cliente' else self.mensagem_funcionario
        primeiro_nome = (pessoa.nome or '').split(' ')[0] if pessoa.nome else ''
        brinde = ''
        if self.brinde_activo and self.brinde_descricao:
            brinde = f'🎁 {self.brinde_descricao}\n\n'
        return template.format(nome=primeiro_nome or pessoa.nome or '', brinde=brinde)


class FelicitacaoEnviada(models.Model):
    """Log de envios para evitar duplicados por ano."""

    TIPO_CHOICES = [('cliente', 'Cliente'), ('funcionario', 'Funcionário')]
    CANAL_CHOICES = [('email', 'Email'), ('sms', 'SMS / WhatsApp'), ('manual', 'Manual')]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    pessoa_id = models.PositiveIntegerField()
    nome = models.CharField(max_length=200)
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES)
    sucesso = models.BooleanField(default=True)
    erro = models.CharField(max_length=300, blank=True)
    ano = models.PositiveIntegerField()
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Felicitação Enviada'
        verbose_name_plural = 'Felicitações Enviadas'
        ordering = ['-enviado_em']
        indexes = [models.Index(fields=['tipo', 'pessoa_id', 'ano'])]

    def __str__(self):
        return f'{self.get_tipo_display()} {self.nome} — {self.ano} ({self.canal})'


class LoteImportacao(models.Model):
    """Lote de compra de produtos no estrangeiro (equivale a uma folha Excel de importação)."""

    STATUS_CHOICES = [
        ('em_preparacao', 'Em Preparação'),
        ('em_transito',   'Em Trânsito'),
        ('recebido',      'Recebido'),
        ('parcial',       'Recebido Parcialmente'),
    ]

    referencia = models.CharField(
        max_length=100,
        help_text='Ex: "Junho 2025 — Portugal", "Wamos #3"'
    )
    data_encomenda = models.DateField(help_text='Data em que a encomenda foi feita ao fornecedor.')
    cambio = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Câmbio EUR → Kzs',
        help_text='Taxa de câmbio do euro para kwanza na data da encomenda (ex: 538,00).'
    )
    custo_transporte_unidade = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Transporte por unidade (Kzs)',
        help_text='Custo fixo de transporte aplicado a cada unidade do lote (ex: 10 000,00 Kzs).'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_preparacao')
    notas = models.TextField(blank=True)
    criado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lotes_importacao'
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Lote de Importação'
        verbose_name_plural = 'Lotes de Importação'
        ordering = ['-data_encomenda']

    def __str__(self):
        return f'{self.referencia} ({self.data_encomenda})'

    @property
    def total_itens(self):
        return self.itens.count()

    @property
    def total_recebidos(self):
        return self.itens.filter(recebido=True).count()

    @property
    def custo_total_kzs(self):
        return sum(item.custo_total_kzs for item in self.itens.all())

    @property
    def venda_total_sugerida_kzs(self):
        return sum(item.preco_venda_sugerido * item.quantidade for item in self.itens.all())


class ItemLoteImportacao(models.Model):
    """Linha de um lote de importação — equivale a uma linha da folha Excel."""

    GENERO_CHOICES = [
        ('masculino', 'M — Masculino'),
        ('feminino',  'F — Feminino'),
        ('unissex',   'U — Unissex'),
    ]

    lote = models.ForeignKey(
        LoteImportacao, on_delete=models.CASCADE, related_name='itens'
    )
    produto = models.ForeignKey(
        Produto, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='itens_importacao',
        help_text='Produto do catálogo a que este item corresponde (opcional).'
    )
    nome_produto = models.CharField(
        max_length=200,
        help_text='Nome do produto tal como consta na factura do fornecedor.'
    )
    marca = models.CharField(max_length=100, blank=True)
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES, default='unissex')
    volume_ml = models.CharField(
        max_length=20, blank=True,
        verbose_name='Volume (ml)',
        help_text='Ex: 100ml, 125ml'
    )
    quantidade = models.PositiveIntegerField(default=1)
    preco_compra_eur = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='Preço de compra (€)',
        help_text='Preço pago ao fornecedor em euros.'
    )
    factor_lucro = models.DecimalField(
        max_digits=5, decimal_places=3,
        verbose_name='Factor de lucro',
        help_text=(
            'Factor de divisão para calcular o PVP. '
            'Ex: 0,58 → PVP = custo ÷ 0,58 (margem bruta ≈ 42%)'
        )
    )
    recebido = models.BooleanField(
        default=False,
        help_text='Marcar quando o produto chegar ao armazém.'
    )
    observacoes = models.CharField(max_length=255, blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Item de Lote de Importação'
        verbose_name_plural = 'Itens de Lote de Importação'
        ordering = ['pk']

    def __str__(self):
        return f'{self.quantidade}× {self.nome_produto} ({self.lote})'

    @property
    def custo_unitario_kzs(self):
        """Custo por unidade = (preço_eur × câmbio) + transporte/unidade."""
        if self.preco_compra_eur is None:
            return 0
        return float(self.preco_compra_eur) * float(self.lote.cambio) + float(self.lote.custo_transporte_unidade)

    @property
    def custo_total_kzs(self):
        """Custo total do lote = custo_unitário × quantidade."""
        return self.custo_unitario_kzs * self.quantidade

    @property
    def preco_venda_sugerido(self):
        """PVP sugerido = custo_unitário ÷ factor_lucro."""
        if not self.factor_lucro or float(self.factor_lucro) == 0:
            return 0
        return self.custo_unitario_kzs / float(self.factor_lucro)

    @property
    def lucro_unitario_kzs(self):
        """Lucro por unidade = PVP − custo_unitário."""
        return self.preco_venda_sugerido - self.custo_unitario_kzs

    @property
    def margem_percentagem(self):
        """Margem em % = lucro / PVP × 100."""
        pvp = self.preco_venda_sugerido
        if not pvp:
            return 0
        return (self.lucro_unitario_kzs / pvp) * 100


class MovimentoStock(models.Model):
    """Registo de todas as movimentações de stock (entrada, saída, ajuste)."""
    
    TIPO_CHOICES = [
        ('entrada', 'Entrada (Compra/Recebimento)'),
        ('saida', 'Saída (Venda)'),
        ('devolucao', 'Devolução'),
        ('ajuste', 'Ajuste Manual'),
    ]
    
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name='movimentos_stock'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantidade = models.IntegerField(help_text='Positivo para entrada, negativo para saída')
    descricao = models.CharField(max_length=255)
    encomenda = models.ForeignKey(
        'Encomenda', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimentos_stock'
    )
    criado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimentos_stock'
    )
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Movimento de Stock'
        verbose_name_plural = 'Movimentos de Stock'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f'{self.get_tipo_display()}: {self.quantidade} × {self.produto.nome}'
    
