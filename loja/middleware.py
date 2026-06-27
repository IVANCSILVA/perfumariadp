from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.conf import settings


class GestaoAccessMiddleware:
    """
    Middleware que restringe o acesso ao subdomínio gestao.decentprive.ao.

    Fluxo:
    1. Admin envia o link: gestao.decentprive.ao/acesso/  (caminho secreto)
    2. Middleware reconhece o caminho, guarda na sessão e serve a página de login
    3. Utilizador vê apenas gestao.decentprive.ao/acesso/ — sem tokens visíveis
    4. Acesso directo a gestao.decentprive.ao → redireciona para www.decentprive.ao
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.secret_path = getattr(settings, 'GESTAO_SECRET_PATH', 'acesso')
        self.redirect_url = 'https://www.decentprive.ao'

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()

        if host == 'gestao.decentprive.ao':
            # Utilizador autenticado com permissão → acesso total
            if request.user.is_authenticated and request.user.is_staff:
                return self.get_response(request)

            # Ficheiros estáticos e media → sempre permitidos
            path = request.path_info
            if path.startswith('/static/') or path.startswith('/media/'):
                return self.get_response(request)

            # Caminho secreto → autorizar sessão e redirecionar para raiz
            if path == f'/{self.secret_path}/':
                request.session['gestao_access'] = True
                return redirect('https://gestao.decentprive.ao/')

            # Sessão autorizada → servir login na raiz (GET e POST)
            if request.session.get('gestao_access'):
                if path == '/':
                    from loja.views import gestao_login
                    return gestao_login(request)
                if path.startswith('/gestao/'):
                    return self.get_response(request)

            # Tudo o resto → redirecionar para a loja
            return redirect(self.redirect_url)

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
