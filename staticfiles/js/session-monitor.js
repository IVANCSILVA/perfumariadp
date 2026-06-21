/**
 * Session Activity Monitor
 * Monitora a atividade do utilizador e renova a sessão apenas quando há atividade real
 * Envia um ping ao servidor a cada 1 minuto de atividade
 * Redireciona para login se a sessão expirar após 5 minutos de inatividade
 */

class SessionActivityMonitor {
    constructor() {
        this.timeout = 5 * 60 * 1000; // 5 minutos em milisegundos
        this.activityTimeout = null;
        this.checkInterval = null;
        this.lastActivityTime = Date.now();
        this.pingInterval = 1 * 60 * 1000; // Ping a cada 1 minuto
        this.lastPingTime = Date.now();
        
        this.init();
    }
    
    init() {
        // Eventos de atividade do utilizador
        const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
        
        events.forEach(event => {
            document.addEventListener(event, () => this.onUserActivity(), true);
        });
        
        // Verifica periodicamente se a sessão expirou
        this.checkInterval = setInterval(() => this.checkSessionExpiry(), 10000);
    }
    
    onUserActivity() {
        const now = Date.now();
        const timeSinceLastActivity = now - this.lastActivityTime;
        
        // Só registar atividade se tiver passado pelo menos 1 segundo desde a última
        if (timeSinceLastActivity < 1000) {
            return;
        }
        
        this.lastActivityTime = now;
        
        // Limpa o timeout anterior
        if (this.activityTimeout) {
            clearTimeout(this.activityTimeout);
        }
        
        // Envia um ping para renovar a sessão
        this.sendActivityPing();
        
        // Define novo timeout de inatividade
        this.activityTimeout = setTimeout(() => {
            this.handleSessionExpired();
        }, this.timeout);
    }
    
    sendActivityPing() {
        const now = Date.now();
        const timeSinceLastPing = now - this.lastPingTime;
        
        // Só envia ping se tiver passado o intervalo de ping
        if (timeSinceLastPing < this.pingInterval) {
            return;
        }
        
        this.lastPingTime = now;
        
        // Envia um POST simples para renovar a sessão
        fetch('/gestao/api/session-ping/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            credentials: 'include'
        }).catch(error => {
            console.log('Erro ao enviar ping de sessão:', error);
        });
    }
    
    checkSessionExpiry() {
        const now = Date.now();
        const inactivityTime = now - this.lastActivityTime;
        
        // Se passaram mais de 5 minutos sem atividade, força logout
        if (inactivityTime > this.timeout) {
            this.handleSessionExpired();
        }
    }
    
    handleSessionExpired() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }
        if (this.activityTimeout) {
            clearTimeout(this.activityTimeout);
        }
        
        // Mostra aviso e redireciona para login
        alert('Sua sessão expirou por inatividade. Por favor, faça login novamente.');
        window.location.href = '/gestao/login/';
    }
    
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Inicializa o monitor ao carregar a página
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new SessionActivityMonitor();
    });
} else {
    new SessionActivityMonitor();
}
