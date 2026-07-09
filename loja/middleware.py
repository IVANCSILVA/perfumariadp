from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import logout
from django.shortcuts import redirect


class GestaoAccessMiddleware:
    """
    Middleware que direciona o subdomínio gestao.decentprive.ao para o
    painel de gestão.

    Fluxo:
    1. gestao.decentprive.ao/ → mostra sempre a página de login
    2. gestao.decentprive.ao/gestao/... → segue normalmente para o painel
    3. Utilizador autenticado como staff → acesso total, sem restrições
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()

        if host == 'gestao.decentprive.ao':
            # Utilizador autenticado com permissão → acesso total
            if request.user.is_authenticated and request.user.is_staff:
                return self.get_response(request)

            path = request.path_info

            # Ficheiros estáticos e media → sempre permitidos
            if path.startswith('/static/') or path.startswith('/media/'):
                return self.get_response(request)

            # Rotas do painel (login, logout, recuperação de senha) → seguem normalmente
            if path.startswith('/gestao/'):
                return self.get_response(request)

            # Raiz do subdomínio → mostra sempre o login
            if path == '/':
                from loja.views import gestao_login
                return gestao_login(request)

            # Tudo o resto → redirecionar para a raiz do subdomínio
            return redirect('https://gestao.decentprive.ao/')

        return self.get_response(request)


class SessionTimeoutMiddleware:
    """
    Middleware que encerra a sessão do utilizador após 5 minutos de inatividade.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout_minutes = 5
    
    def __call__(self, request):
        # Verifica se o utilizador está autenticado
        if request.user.is_authenticated:
            # Obtém o timestamp da última atividade da sessão
            last_activity = request.session.get('_last_activity')
            now = timezone.now()
            
            if last_activity:
                # Converte a string do timestamp para datetime se necessário
                if isinstance(last_activity, str):
                    last_activity = timezone.datetime.fromisoformat(last_activity)
                
                # Calcula o tempo desde a última atividade
                time_delta = now - last_activity
                
                # Se passou mais de 5 minutos, faz logout
                if time_delta > timedelta(minutes=self.timeout_minutes):
                    logout(request)
                    request.session.flush()
            
            # Atualiza o timestamp da última atividade para agora
            request.session['_last_activity'] = now.isoformat()
        
        response = self.get_response(request)
        return response
