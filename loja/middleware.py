from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import logout


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
