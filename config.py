"""
Configurações centrais do Burocrata de Bolso
"""
import os
from typing import Dict, Any

# Configurações do Banco de Dados
DB_PATH = 'usuarios_burocrata.db'

# Configurações da Aplicação
APP_CONFIG = {
    'title': "Burocrata de Bolso",
    'icon': "⚖️",
    'layout': "wide",
    'initial_sidebar_state': "collapsed"
}

# Configurações de Usuário
USER_CONFIG = {
    'special_account': {
        'email': "pedrohenriquemarques720@gmail.com",
        'password': "Liz1808#",
        'name': "Pedro Henrique (Conta Especial)",
        'plan': 'PRO',
        'credits': 999999
    },
    'default_credits': 0,
    'analysis_cost': 10
}

# Configurações de UI
THEME_CONFIG = {
    'primary_color': '#10263D',
    'secondary_color': '#1a3658',
    'accent_color': '#F8D96D',
    'accent_hover': '#FFE87C',
    'text_color': '#FFFFFF',
    'border_radius': '15px'
}

# Configurações de Análise
ANALYSIS_CONFIG = {
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'supported_formats': ['pdf'],
    'min_text_length': 50,
    'history_limit': 5
}

# Contato e Suporte
CONTACT_CONFIG = {
    'email': "contatoburocrata@outlook.com",
    'instagram': "https://www.instagram.com/burocratadebolso/",
    'support_response_time': "24h"
}

# Mensagens do Sistema
MESSAGES = {
    'success': {
        'login': "✅ Login realizado com sucesso!",
        'account_created': "✅ Usuário criado com sucesso!",
        'analysis_complete': "✅ Análise concluída com sucesso!"
    },
    'error': {
        'invalid_credentials': "❌ E-mail ou senha incorretos",
        'email_exists': "❌ E-mail já cadastrado",
        'insufficient_credits': "❌ Saldo insuficiente!",
        'file_processing_error': "❌ Não foi possível processar o arquivo",
        'database_error': "❌ Erro no banco de dados"
    },
    'warning': {
        'fill_fields': "⚠️ Preencha todos os campos",
        'password_mismatch': "⚠️ As senhas não coincidem",
        'password_length': "⚠️ A senha deve ter no mínimo 6 caracteres"
    },
    'info': {
        'credits_info': "ℹ️ Cada análise custa 10 BuroCreds",
        'special_account': "🔑 Conta Especial Detectada: Use sua senha pessoal para acessar.",
        'new_account_info': "ℹ️ Novas contas começam com 0 BuroCreds. Para adquirir créditos, entre em contato com o suporte."
    }
}

# Configurações de Segurança
SECURITY_CONFIG = {
    'password_hash_algorithm': 'sha256',
    'session_timeout': 3600,  # 1 hora
    'max_login_attempts': 3
}

def get_config(section: str, key: str = None) -> Any:
    """
    Obtém configuração de uma seção específica
    
    Args:
        section: Nome da seção de configuração
        key: Chave específica (opcional)
    
    Returns:
        Valor da configuração ou dicionário completo da seção
    """
    config_map = {
        'app': APP_CONFIG,
        'user': USER_CONFIG,
        'theme': THEME_CONFIG,
        'analysis': ANALYSIS_CONFIG,
        'contact': CONTACT_CONFIG,
        'messages': MESSAGES,
        'security': SECURITY_CONFIG
    }
    
    if section not in config_map:
        raise ValueError(f"Seção de configuração '{section}' não encontrada")
    
    if key:
        return config_map[section].get(key)
    
    return config_map[section]

def get_database_url() -> str:
    """Retorna a URL do banco de dados"""
    return f"sqlite:///{DB_PATH}"

def is_special_account(email: str) -> bool:
    """Verifica se é uma conta especial"""
    return email == USER_CONFIG['special_account']['email']
