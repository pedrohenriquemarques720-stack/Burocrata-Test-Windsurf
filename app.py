import streamlit as st
import pdfplumber
import re
import unicodedata
from datetime import datetime
import pandas as pd
import sqlite3
import hashlib
import time
import random
import os

# --------------------------------------------------
# FUNÇÕES AUXILIARES (definidas primeiro)
# --------------------------------------------------

def hash_senha(senha):
    """Gera hash da senha usando SHA-256"""
    return hashlib.sha256(senha.encode()).hexdigest()

def limpar_texto(texto):
    """Limpa texto removendo caracteres especiais e normalizando"""
    if not texto:
        return ""
    
    # Converter para string se não for
    texto = str(texto)
    
    # Remover caracteres de controle e substituir por espaço
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', texto)
    
    # Normalizar caracteres Unicode
    try:
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    except:
        pass
    
    # Substituir múltiplos espaços por um único espaço
    texto = re.sub(r'\s+', ' ', texto)
    
    return texto.strip()

# --------------------------------------------------
# CONFIGURAÇÃO DO BANCO DE DADOS SQLITE
# --------------------------------------------------
DB_PATH = 'usuarios_burocrata.db'

def init_database():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            plano TEXT DEFAULT 'FREE',
            burocreds INTEGER DEFAULT 0,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'ATIVO'
        )
    ''')
    
    # Tabela de histórico de análises
    c.execute('''
        CREATE TABLE IF NOT EXISTS historico_analises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            nome_arquivo TEXT,
            tipo_documento TEXT,
            problemas_detectados INTEGER,
            score_conformidade REAL,
            data_analise TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    # Criar conta especial com créditos infinitos
    conta_especial_email = "pedrohenriquemarques720@gmail.com"
    senha_especial_hash = hash_senha("Liz1808#")
    
    # Verificar se a conta especial já existe
    c.execute("SELECT COUNT(*) FROM usuarios WHERE email = ?", (conta_especial_email,))
    resultado = c.fetchone()
    
    if resultado and resultado[0] == 0:
        # Criar conta especial com créditos altíssimos
        c.execute('''
            INSERT INTO usuarios (nome, email, senha_hash, plano, burocreds)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Pedro Henrique (Conta Especial)", conta_especial_email, senha_especial_hash, 'PRO', 999999))
        print(f"✅ Conta especial criada: {conta_especial_email}")
    else:
        # Atualizar senha da conta existente
        c.execute('''
            UPDATE usuarios 
            SET senha_hash = ?
            WHERE email = ?
        ''', (senha_especial_hash, conta_especial_email))
        print(f"✅ Senha da conta especial atualizada")
    
    conn.commit()
    conn.close()

# Inicializar banco de dados
init_database()

# --------------------------------------------------
# FUNÇÕES DE AUTENTICAÇÃO
# --------------------------------------------------

def criar_usuario(nome, email, senha):
    """Cria um novo usuário no sistema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Verifica se email já existe
        c.execute("SELECT COUNT(*) FROM usuarios WHERE email = ?", (email,))
        if c.fetchone()[0] > 0:
            conn.close()
            return False, "E-mail já cadastrado"
        
        # Cria usuário com 0 BuroCreds iniciais
        senha_hash = hash_senha(senha)
        burocreds_iniciais = 0
        
        c.execute('''
            INSERT INTO usuarios (nome, email, senha_hash, plano, burocreds)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, email, senha_hash, 'FREE', burocreds_iniciais))
        
        conn.commit()
        conn.close()
        return True, "Usuário criado com sucesso!"
        
    except Exception as e:
        return False, f"Erro ao criar usuário: {str(e)}"

def autenticar_usuario(email, senha):
    """Autentica um usuário pelo email e senha"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        senha_hash = hash_senha(senha)
        
        c.execute('''
            SELECT id, nome, email, plano, burocreds, estado 
            FROM usuarios 
            WHERE email = ? AND senha_hash = ? AND estado = 'ATIVO'
        ''', (email, senha_hash))
        
        resultado = c.fetchone()
        conn.close()
        
        if resultado:
            return True, {
                'id': resultado[0],
                'nome': resultado[1],
                'email': resultado[2],
                'plano': resultado[3],
                'burocreds': resultado[4],
                'estado': resultado[5]
            }
        else:
            return False, "E-mail ou senha incorretos"
            
    except Exception as e:
        return False, f"Erro na autenticação: {str(e)}"

def get_usuario_por_id(usuario_id):
    """Obtém informações do usuário pelo ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, nome, email, plano, burocreds, estado 
            FROM usuarios 
            WHERE id = ?
        ''', (usuario_id,))
        
        resultado = c.fetchone()
        conn.close()
        
        if resultado:
            return {
                'id': resultado[0],
                'nome': resultado[1],
                'email': resultado[2],
                'plano': resultado[3],
                'burocreds': resultado[4],
                'estado': resultado[5]
            }
        else:
            return None
            
    except Exception as e:
        st.error(f"Erro ao obter usuário: {e}")
        return None

def atualizar_burocreds(usuario_id, quantidade):
    """Atualiza os BuroCreds do usuário"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Para conta especial, não debita créditos
        c.execute("SELECT email FROM usuarios WHERE id = ?", (usuario_id,))
        usuario = c.fetchone()
        
        if usuario and usuario[0] == "pedrohenriquemarques720@gmail.com":
            conn.close()
            return True
        
        # Para usuários normais, atualiza normalmente
        c.execute('''
            UPDATE usuarios 
            SET burocreds = burocreds + ? 
            WHERE id = ?
        ''', (quantidade, usuario_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar BuroCreds: {e}")
        return False

# --------------------------------------------------
# FUNÇÕES DO SISTEMA DE ANÁLISE
# --------------------------------------------------

def registrar_analise(usuario_id, nome_arquivo, tipo_documento, problemas, score):
    """Registra uma análise no histórico"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO historico_analises 
            (usuario_id, nome_arquivo, tipo_documento, problemas_detectados, score_conformidade)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario_id, nome_arquivo, tipo_documento, problemas, score))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao registrar análise: {e}")
        return False

def get_historico_usuario(usuario_id, limit=5):
    """Obtém histórico de análises do usuário"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT nome_arquivo, tipo_documento, problemas_detectados, 
                   score_conformidade, data_analise
            FROM historico_analises
            WHERE usuario_id = ?
            ORDER BY data_analise DESC
            LIMIT ?
        ''', (usuario_id, limit))
        
        historico = []
        for row in c.fetchall():
            historico.append({
                'arquivo': row[0],
                'tipo': row[1],
                'problemas': row[2],
                'score': row[3],
                'data': row[4]
            })
        
        conn.close()
        return historico
    except:
        return []

# --------------------------------------------------
# CONFIGURAÇÃO DE PÁGINA
# --------------------------------------------------
st.set_page_config(
    page_title="Burocrata de Bolso",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# CSS PERSONALIZADO - TEMA AZUL ESCURO COM DOURADO
# --------------------------------------------------
st.markdown("""
<style>
    /* Tema principal - Azul escuro com dourado */
    .stApp {
        background: #10263D !important;
        min-height: 100vh;
    }
    
    /* Container principal */
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        background: #10263D;
    }
    
    /* Cabeçalho principal */
    .header-main {
        text-align: center;
        padding: 30px 0;
        margin-bottom: 20px;
    }
    
    .header-main h1 {
        font-family: 'Arial Black', sans-serif;
        font-size: 3em;
        font-weight: 900;
        color: #F8D96D;
        letter-spacing: 1px;
        margin-bottom: 5px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-main p {
        font-family: 'Georgia', serif;
        font-size: 1.2em;
        color: #FFFFFF;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    
    /* Card de autenticação */
    .auth-card {
        background: #1a3658;
        border-radius: 15px;
        padding: 40px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border: 3px solid #F8D96D;
        max-width: 500px;
        margin: 0 auto;
    }
    
    .auth-title {
        color: #F8D96D;
        font-size: 2.2em;
        font-weight: 800;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Perfil do usuário */
    .user-profile {
        background: #1a3658;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border: 2px solid #F8D96D;
        margin-bottom: 30px;
    }
    
    /* Campos de formulário */
    .stTextInput > div > div > input,
    .stTextInput > div > div > input:focus {
        border-radius: 10px !important;
        border: 2px solid #F8D96D !important;
        padding: 12px 15px !important;
        font-size: 1em !important;
        background-color: #2a4a75 !important;
        color: white !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #a0aec0 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #FFE87C !important;
        box-shadow: 0 0 0 3px rgba(248, 217, 109, 0.3) !important;
    }
    
    /* Botões do Streamlit */
    .stButton > button {
        background: linear-gradient(135deg, #F8D96D, #d4b747) !important;
        color: #10263D !important;
        border: none !important;
        padding: 15px 30px !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1.1em !important;
        transition: all 0.3s !important;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 25px rgba(248, 217, 109, 0.4) !important;
        background: linear-gradient(135deg, #FFE87C, #F8D96D) !important;
    }
    
    /* Botão secundário */
    .secondary-button {
        background: linear-gradient(135deg, #2a4a75, #1a3658) !important;
        color: #F8D96D !important;
        border: 2px solid #F8D96D !important;
    }
    
    .secondary-button:hover {
        background: linear-gradient(135deg, #3a5a85, #2a4a75) !important;
        color: #FFE87C !important;
        border-color: #FFE87C !important;
    }
    
    /* Estilos para FAQ */
    .faq-container {
        background: #1a3658;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border: 2px solid #F8D96D;
        margin: 20px 0;
    }
    
    .faq-question {
        color: #F8D96D;
        font-weight: 700;
        margin-bottom: 5px;
        font-size: 1.1em;
    }
    
    .faq-answer {
        color: #FFFFFF;
        margin-bottom: 15px;
        font-size: 1em;
        line-height: 1.5;
    }
    
    /* Estilos para links sociais */
    .social-links {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 15px;
    }
    
    .social-link {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #F8D96D;
        text-decoration: none;
        font-weight: 700;
        padding: 8px 15px;
        border-radius: 20px;
        border: 2px solid #F8D96D;
        background: #1a3658;
        transition: all 0.3s;
    }
    
    .social-link:hover {
        background: rgba(248, 217, 109, 0.1);
        transform: translateY(-2px);
        color: #FFE87C;
        border-color: #FFE87C;
    }
    
    /* Estilos para cards de análise */
    .analise-card {
        background: #1a3658;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border-top: 5px solid #F8D96D;
        height: 100%;
        transition: transform 0.3s;
    }
    
    .analise-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.4);
    }
    
    .analise-icon {
        font-size: 2.5em;
        margin-bottom: 15px;
        color: #F8D96D;
    }
    
    .analise-title {
        color: #F8D96D;
        font-size: 1.5em;
        font-weight: 700;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .analise-item {
        margin-bottom: 15px;
        padding-left: 10px;
        border-left: 3px solid rgba(248, 217, 109, 0.5);
    }
    
    .analise-item-title {
        color: #FFFFFF;
        font-weight: 600;
        margin-bottom: 5px;
        font-size: 1.1em;
    }
    
    .analise-item-desc {
        color: #e2e8f0;
        font-size: 0.95em;
        line-height: 1.4;
    }
    
    /* Cards de métricas */
    .metric-card {
        background: #1a3658;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border-left: 4px solid #F8D96D;
    }
    
    /* Expanders e containers */
    .stExpander {
        background: #1a3658;
        border: 1px solid #F8D96D;
        border-radius: 10px;
    }
    
    .stExpander > div > div {
        background: #1a3658 !important;
    }
    
    /* Mensagens do Streamlit */
    .stAlert {
        background: #2a4a75 !important;
        border: 1px solid #F8D96D !important;
        color: white !important;
    }
    
    /* Estilo para métricas do Streamlit */
    [data-testid="stMetric"] {
        background: #1a3658;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #F8D96D;
    }
    
    [data-testid="stMetricLabel"] {
        color: #F8D96D !important;
    }
    
    [data-testid="stMetricValue"] {
        color: white !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: white !important;
    }
    
    /* Upload de arquivo */
    .stFileUploader > div > div {
        background: #1a3658 !important;
        border: 2px solid #F8D96D !important;
        border-radius: 10px !important;
        color: white !important;
    }
    
    /* Tabs e navegação */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #1a3658;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2a4a75;
        border-radius: 4px 4px 0 0;
        padding: 10px 16px;
        color: white;
        border: 1px solid #F8D96D;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #F8D96D !important;
        color: #10263D !important;
        font-weight: bold;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a3658;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #F8D96D;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #FFE87C;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SISTEMA DE DETECÇÃO ESPECIALIZADO - SUPER ROBUSTO ATUALIZADO
# --------------------------------------------------

class SistemaDetecção:
    """Sistema altamente especializado em detecção de problemas jurídicos"""
    
    def __init__(self):
        # Padrões extremamente específicos para cada tipo de violação - ATUALIZADO
        self.padroes = {
            'CONTRATO_LOCACAO': {
                'nome': 'Contrato de Locação',
                'padroes': [
                    {
                        'regex': r'multa.*correspondente.*12.*meses.*aluguel|multa.*12.*meses|doze.*meses.*aluguel|multa.*integral.*12.*meses',
                        'descricao': '🚨🚨🚨 MULTA DE 12 MESES DE ALUGUEL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 4º: Multa máxima = 2 meses de aluguel',
                        'detalhe': 'A lei do inquilinato PROÍBE multas superiores a 2 meses de aluguel.'
                    },
                    {
                        'regex': r'depósito.*caução.*três.*meses|caução.*3.*meses|três.*meses.*aluguel.*caução|3.*meses.*depósito|caução.*excessiva',
                        'descricao': '🚨🚨 CAUÇÃO DE 3 MESES - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 37: Caução máxima = 1 mês de aluguel',
                        'detalhe': 'Limite legal é apenas 1 mês de aluguel como caução.'
                    },
                    {
                        'regex': r'reajuste.*trimestral|reajuste.*a.*cada.*3.*meses|reajuste.*mensalmente|reajuste.*mensal|aumento.*mensal',
                        'descricao': '🚨 REAJUSTE TRIMESTRAL/MENSAL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º: Reajuste mínimo anual (12 meses)',
                        'detalhe': 'Reajustes só podem ser feitos a cada 12 meses no mínimo.'
                    },
                    {
                        'regex': r'visitas.*qualquer.*tempo.*sem.*aviso|visitas.*sem.*aviso.*prévio|visitas.*a.*qualquer.*momento|entrar.*qualquer.*hora.*sem.*aviso',
                        'descricao': '🚨 VISITAS SEM AVISO - VIOLAÇÃO DE DOMICÍLIO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CDC Art. 51 + Lei 8.245/1991 Art. 23 + Código Penal Art. 150',
                        'detalhe': 'Locador deve avisar com antecedência para visitas ao imóvel. Entrar sem aviso pode configurar crime de violação de domicílio.'
                    },
                    {
                        'regex': r'renúncia.*indenização.*benfeitorias.*necessárias|benfeitorias.*necessárias.*sem.*indenização|renúncia.*retensão.*benfeitorias',
                        'descricao': '🚨 RENÚNCIA A BENFEITORIAS NECESSÁRIAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Civil Art. 35 + Lei 8.245/1991',
                        'detalhe': 'Locatário tem direito à indenização por benfeitorias necessárias. Cláusula é NULA.'
                    },
                    {
                        'regex': r'vedada.*permanência.*animais|proibido.*animais.*estimação|não.*permitido.*animais',
                        'descricao': '⚠️ PROIBIÇÃO DE ANIMAIS - CLAUSULA ABUSIVA',
                        'gravidade': 'ALTA',
                        'lei': 'CDC Art. 51: Cláusulas abusivas são nulas',
                        'detalhe': 'Proibição total de animais pode ser considerada abusiva e nula.'
                    },
                    {
                        'regex': r'contrato.*automaticamente.*resciso.*venda|venda.*imóvel.*contrato.*rescindido|retomada.*48.*horas.*venda',
                        'descricao': '⚠️ RESCISÃO AUTOMÁTICA POR VENDA - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 9º: Contrato segue para novo proprietário',
                        'detalhe': 'Na venda do imóvel, o contrato continua com o novo proprietário. Prazo de desocupação mínimo é de 30 dias.'
                    },
                    {
                        'regex': r'fiadores.*com.*renda.*comprovada',
                        'descricao': '⚠️ EXIGÊNCIA DE FIADORES - PODE SER ABUSIVA',
                        'gravidade': 'MÉDIA',
                        'lei': 'CDC Art. 51 + Jurisprudência',
                        'detalhe': 'Exigência de fiadores pode ser substituída por seguro fiança.'
                    },
                    {
                        'regex': r'locatário.*assume.*responsabilidade.*estrutural|dano.*estrutural.*locatário|reparos.*estruturais.*locatário',
                        'descricao': '🚨 LOCATÁRIO RESPONSÁVEL POR ESTRUTURA - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 22: Despesas com estrutura são do locador',
                        'detalhe': 'Telhado, fundação, fiação central e tubulações são responsabilidade do LOCADOR.'
                    },
                    {
                        'regex': r'pagamento.*antecipado.*mês.*vencer|aluguel.*primeiro.*dia.*mês',
                        'descricao': '⚠️ PAGAMENTO ANTECIPADO OBRIGATÓRIO - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 3º',
                        'detalhe': 'Pagamento antecipado só é permitido em locações SEM garantia.'
                    },
                    {
                        'regex': r'locatário.*pagar.*imposto.*renda.*locador|imposto.*renda.*locatário.*pagar',
                        'descricao': '🚨 LOCATÁRIO PAGANDO IR DO LOCADOR - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991 + Lei Tributária',
                        'detalhe': 'Imposto de Renda é encargo PESSOAL do contribuinte (locador).'
                    },
                    {
                        'regex': r'despejo.*imediato.*atrasar.*1.*dia|trocar.*fechaduras.*atraso',
                        'descricao': '🚨 DESPEJO IMEDIATO POR 1 DIA DE ATRASO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991 + Código de Processo Civil',
                        'detalhe': 'Despejo só pode ser determinado por ORDEM JUDICIAL após processo legal.'
                    },
                    {
                        'regex': r'reajuste.*conforme.*dólar|reajuste.*variação.*dólar',
                        'descricao': '🚨 REAJUSTE PELO DÓLAR - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º',
                        'detalhe': 'Reajustes devem seguir índices oficiais brasileiros (IGPM, INCC, IPCA), NÃO o dólar.'
                    },
                    {
                        'regex': r'cumulação.*modalidades.*garantia|caução.*E.*fiador',
                        'descricao': '⚠️ CUMULAÇÃO DE GARANTIAS - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 37',
                        'detalhe': 'É proibida a cumulação de modalidades de garantia (caução E fiador).'
                    }
                ]
            },
            'CONTRATO_TRABALHO': {
                'nome': 'Contrato de Trabalho',
                'padroes': [
                    {
                        'regex': r'salário.*mensal.*bruto.*R\$\s*900|R\$\s*900[,\.]00|900.*reais|novecentos.*reais|salário.*R\$\s*800|800.*reais',
                        'descricao': '🚨🚨🚨 SALÁRIO ABAIXO DO MÍNIMO - TRABALHO ESCRAVO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Constituição Federal Art. 7º IV',
                        'detalhe': f'Salário mínimo atual (2024): R$ 1.412,00. R$ 900 é 36% ABAIXO! R$ 800 é 43% ABAIXO!'
                    },
                    {
                        'regex': r'jornada.*das\s*08:00.*às\s*20:00|08:00.*20:00|das\s*08.*às\s*20|jornada.*60.*horas.*semanais|60.*horas.*semanais',
                        'descricao': '🚨🚨 JORNADA EXCESSIVA - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 58: Máximo 8h diárias / 44h semanais',
                        'detalhe': '12h diárias = 50% ACIMA do limite! 60h semanais = 36% ACIMA do limite de 44h!'
                    },
                    {
                        'regex': r'não.*haverá.*pagamento.*horas.*extras|sem.*pagamento.*horas.*extras|sem.*direito.*horas.*extras',
                        'descricao': '🚨🚨 SEM PAGAMENTO DE HORAS EXTRAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 59: Horas extras obrigatórias após 8h/dia',
                        'detalhe': 'Horas extras são DIREITO do trabalhador e DEVEM ser pagas!'
                    },
                    {
                        'regex': r'23:00.*retornar.*06:00|encerrar.*23:00.*retornar.*06:00',
                        'descricao': '🚨🚨 INTERVALO INTERJORNADA DE 7 HORAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 66: Mínimo 11 horas entre jornadas',
                        'detalhe': '7 horas entre jornadas = 36% ABAIXO do mínimo de 11h!'
                    },
                    {
                        'regex': r'intervalo.*refeição.*30.*minutos|30.*minutos.*refeição|intervalo.*10.*minutos|10.*minutos.*almoço',
                        'descricao': '🚨 INTERVALO INSUFICIENTE PARA REFEIÇÃO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 71: Mínimo 1 hora para jornada >6h',
                        'detalhe': '30 minutos = 50% ABAIXO do mínimo! 10 minutos = VIOLAÇÃO GRAVÍSSIMA!'
                    },
                    {
                        'regex': r'renúncia.*FGTS|renúncia.*Fundo.*Garantia|Vale.*Cultura.*substituição.*FGTS|FGTS.*descontado.*folha.*pagamento',
                        'descricao': '🚨🚨🚨 RENÚNCIA AO FGTS - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.036/1990 Art. 15: FGTS é OBRIGATÓRIO',
                        'detalhe': 'FGTS é DIREITO IRRENUNCIÁVEL! "Vale Cultura" NÃO substitui FGTS! FGTS é obrigação EXCLUSIVA do empregador.'
                    },
                    {
                        'regex': r'segunda.*sábado.*08:00.*20:00',
                        'descricao': '🚨 JORNADA SEMANAL DE 72 HORAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 58: Máximo 44 horas semanais',
                        'detalhe': '72h semanais = 64% ACIMA do limite de 44h!'
                    },
                    {
                        'regex': r'extensão.*jornada.*inerente.*função',
                        'descricao': '⚠️ JUSTIFICATIVA ILEGAL PARA HORAS EXTRAS',
                        'gravidade': 'ALTA',
                        'lei': 'CLT Art. 59 + Jurisprudência',
                        'detalhe': 'Nenhuma função justifica horas extras não remuneradas!'
                    },
                    {
                        'regex': r'Cláusula.*Abusiva',
                        'descricao': '🚨 CLÁUSULA IDENTIFICADA COMO ABUSIVA PELO PRÓPRIO CONTRATO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CDC Art. 51',
                        'detalhe': 'O próprio contrato reconhece que contém cláusulas abusivas!'
                    },
                    {
                        'regex': r'Cláusula.*Ilegal',
                        'descricao': '🚨🚨 CLÁUSULA IDENTIFICADA COMO ILEGAL PELO PRÓPRIO CONTRATO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação trabalhista',
                        'detalhe': 'O contrato ADMITE conter cláusulas ilegais!'
                    },
                    {
                        'regex': r'Cláusula.*Nula',
                        'descricao': '🚨 CLÁUSULA IDENTIFICADA COMO NULA PELO PRÓPRIO CONTRATO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Legislação aplicável',
                        'detalhe': 'O contrato reconhece que possui cláusulas sem valor jurídico!'
                    },
                    {
                        'regex': r'renúncia.*férias.*remuneradas|renúncia.*férias.*24.*meses',
                        'descricao': '🚨 RENÚNCIA A FÉRIAS REMUNERADAS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 130: Férias são direito irrenunciável',
                        'detalhe': 'Férias remuneradas são DIREITO IRRENUNCIÁVEL do trabalhador!'
                    },
                    {
                        'regex': r'gravidez.*contrato.*rescindido|gravidez.*demissão.*sem.*ônus',
                        'descricao': '🚨🚨 DISCRIMINAÇÃO POR GRAVIDEZ - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 391-A + Lei 9.029/1995',
                        'detalhe': 'Estabilidade provisória da gestante é GARANTIDA. Rescisão por gravidez é DISCRIMINAÇÃO!'
                    },
                    {
                        'regex': r'CTPS.*retida.*empresa|retenção.*CTPS|Carteira.*Trabalho.*retida',
                        'descricao': '🚨 RETENÇÃO DE CTPS - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT Art. 29 + Lei 5.553/1968',
                        'detalhe': 'Retenção de CTPS é CRIME e contravenção penal!'
                    },
                    {
                        'regex': r'custo.*manutenção.*descontado.*salário|equipamentos.*descontado.*salário',
                        'descricao': '⚠️ DESCONTO ILEGAL POR EQUIPAMENTOS',
                        'gravidade': 'ALTA',
                        'lei': 'CLT Art. 462',
                        'detalhe': 'Risco do negócio é do empregador. Custo de equipamentos não pode ser descontado do salário.'
                    },
                    {
                        'regex': r'erro.*técnico.*justa.*causa|justa.*causa.*imediata.*erro',
                        'descricao': '⚠️ JUSTA CAUSA ABUSIVA',
                        'gravidade': 'ALTA',
                        'lei': 'CLT Art. 482',
                        'detalhe': 'Rigor excessivo e falta de gradação de pena. Erro técnico não configura justa causa automaticamente.'
                    },
                    {
                        'regex': r'funcionário.*responde.*patrimônio.*pessoal|responsabilidade.*civil.*patrimônio.*pessoal',
                        'descricao': '🚨 RESPONSABILIDADE CIVIL ABUSIVA',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Civil + Jurisprudência trabalhista',
                        'detalhe': 'Responsabilidade civil objetiva abusiva. Empregado não responde com patrimônio pessoal por prejuízos sem dolo.'
                    },
                    {
                        'regex': r'Viol.*\d+.*:',
                        'descricao': '🚨 VIOLAÇÃO EXPLÍCITA À CLT!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CLT diversos artigos',
                        'detalhe': 'O próprio contrato lista violações à legislação trabalhista!'
                    }
                ]
            },
            'CONTRATO_LOCACAO_TESTE': {
                'nome': 'Contrato de Locação (Versão Teste)',
                'padroes': [
                    {
                        'regex': r'reajuste.*unilateral|índice.*reajuste.*livre|maior.*alta.*mercado',
                        'descricao': '🚨🚨 REAJUSTE UNILATERAL DO LOCADOR - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º',
                        'detalhe': 'Índices de reajuste devem ser oficiais (IGPM, INCC, IPCA)'
                    },
                    {
                        'regex': r'aumento.*fixo.*20%.*ano|20%.*ao.*ano.*fixo',
                        'descricao': '🚨 AUMENTO FIXO DE 20% AO ANO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 7º',
                        'detalhe': 'Reajustes devem seguir índices oficiais, não percentuais fixos'
                    },
                    {
                        'regex': r'independentemente.*inflação.*oficial',
                        'descricao': '⚠️ DESCONSIDERAÇÃO DA INFLAÇÃO OFICIAL - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 7º',
                        'detalhe': 'Reajustes devem considerar índices oficiais de inflação'
                    },
                    {
                        'regex': r'locatário.*assume.*responsabilidade.*estrutural|dano.*estrutural.*imóvel',
                        'descricao': '🚨 LOCATÁRIO RESPONSÁVEL POR DANOS ESTRUTURAIS - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 22',
                        'detalhe': 'Despesas com estrutura (telhado, fundação) são do LOCADOR'
                    },
                    {
                        'regex': r'desgaste.*natural|vício.*oculto.*anterior.*locação',
                        'descricao': '⚠️ LOCATÁRIO RESPONSÁVEL POR DESGASTE NATURAL - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 22',
                        'detalhe': 'Desgaste natural do imóvel é responsabilidade do LOCADOR'
                    },
                    {
                        'regex': r'renúncia.*abatimento.*aluguel',
                        'descricao': '🚨 RENÚNCIA AO ABATIMENTO DO ALUGUEL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Código Civil + Lei 8.245/1991',
                        'detalhe': 'Locatário tem direito a abatimento do aluguel em caso de problemas no imóvel'
                    },
                    {
                        'regex': r'ingressar.*imóvel.*qualquer.*momento.*sem.*aviso',
                        'descricao': '🚨 INGRESSO SEM AVISO NO IMÓVEL - CRIME!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'CDC Art. 51 + Código Penal Art. 150',
                        'detalhe': 'Violação de domicílio é crime! Avanço sem aviso = violação de privacidade'
                    },
                    {
                        'regex': r'visitação.*surpresa|vistorias.*sem.*aviso',
                        'descricao': '⚠️ VISTORIAS SURPRESA - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'CDC Art. 51 + Lei 8.245/1991',
                        'detalhe': 'Vistorias exigem aviso prévio ao locatário'
                    },
                    {
                        'regex': r'mostrar.*imóvel.*terceiros.*sem.*autorização',
                        'descricao': '⚠️ MOSTRAR IMÓVEL A TERCEIROS SEM AUTORIZAÇÃO - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'CDC Art. 51 + Direito à Privacidade',
                        'detalhe': 'Locatário tem direito à privacidade e tranquilidade no imóvel'
                    },
                    {
                        'regex': r'multa.*rescisória.*integral|total.*meses.*restantes.*contrato',
                        'descricao': '🚨🚨🚨 MULTA INTEGRAL PELO PERÍODO RESTANTE - ESCRAVIDÃO!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 4º + CDC Art. 51',
                        'detalhe': 'Multa rescisória máxima = 2 meses de aluguel. Multa integral é ESCRAVIDÃO MODERNA!'
                    },
                    {
                        'regex': r'sem.*direito.*proporcionalidade',
                        'descricao': '⚠️ ELIMINAÇÃO DA PROPORCIONALIDADE - ILEGAL',
                        'gravidade': 'ALTA',
                        'lei': 'Lei 8.245/1991, Art. 4º',
                        'detalhe': 'Multas devem ser proporcionais ao tempo de contrato cumprido'
                    }
                ]
            },
            'NOTA_FISCAL': {
                'nome': 'Nota Fiscal',
                'padroes': [
                    {
                        'regex': r'Nota.*Fiscal|NFSe|NF-e|NFS-e',
                        'descricao': '📄 NOTA FISCAL IDENTIFICADA',
                        'gravidade': 'INFO',
                        'lei': 'Legislação tributária',
                        'detalhe': 'Documento fiscal para prestação de serviços'
                    }
                ]
            }
        }
        
        # Termos para detecção rápida de tipo - ATUALIZADO
        self.indicadores_tipo = {
            'CONTRATO_LOCACAO': [
                'locação', 'aluguel', 'locador', 'locatário', 'imóvel residencial',
                'caução', 'fiador', 'benfeitorias', 'multa rescisória', 'inquilino',
                'proprietário', 'Lei 8.245/1991', 'Lei do Inquilinato'
            ],
            'CONTRATO_TRABALHO': [
                'empregador', 'empregado', 'CLT', 'salário', 'jornada',
                'horas extras', 'FGTS', 'férias', '13º salário', 'funcionário',
                'trabalhador', 'contrato de trabalho', 'carteira de trabalho'
            ],
            'CONTRATO_LOCACAO_TESTE': [
                'versão de teste', 'cláusula de risco', 'para auditoria',
                'reajuste unilateral', 'imobiliária vigilante'
            ],
            'NOTA_FISCAL': [
                'nota fiscal', 'nfse', 'nfe', 'prefeitura municipal',
                'prestador de serviços', 'tomador de serviços', 'iss', 'imposto'
            ]
        }
        
        # Detecção especial para violações numeradas
        self.violacoes_numeradas = [
            (r'Viol.*1.*:', 'VIOLACAO_1', '🚨 VIOLAÇÃO 1 À CLT', 'CRÍTICA'),
            (r'Viol.*2.*:', 'VIOLACAO_2', '🚨 VIOLAÇÃO 2 À CLT', 'CRÍTICA'),
            (r'Viol.*3.*:', 'VIOLACAO_3', '🚨 VIOLAÇÃO 3 À CLT', 'CRÍTICA'),
            (r'Viol.*4.*:', 'VIOLACAO_4', '🚨 VIOLAÇÃO 4 À CLT', 'CRÍTICA'),
            (r'Viol.*5.*:', 'VIOLACAO_5', '🚨 VIOLAÇÃO 5 À CLT', 'CRÍTICA'),
            (r'Viol.*6.*:', 'VIOLACAO_6', '🚨 VIOLAÇÃO 6 À CLT', 'CRÍTICA'),
            (r'Viol.*7.*:', 'VIOLACAO_7', '🚨 VIOLAÇÃO 7 À CLT', 'CRÍTICA'),
            (r'Viol.*8.*:', 'VIOLACAO_8', '🚨 VIOLAÇÃO 8 À CLT', 'CRÍTICA'),
            (r'Viol.*9.*:', 'VIOLACAO_9', '🚨 VIOLAÇÃO 9 À CLT', 'CRÍTICA'),
            (r'Viol.*10.*:', 'VIOLACAO_10', '🚨 VIOLAÇÃO 10 À CLT', 'CRÍTICA'),
            (r'Viol.*1\b', 'VIOLACAO_INQUILINATO_1', '🚨 VIOLAÇÃO 1 À LEI DO INQUILINATO', 'CRÍTICA'),
            (r'Viol.*2\b', 'VIOLACAO_INQUILINATO_2', '🚨 VIOLAÇÃO 2 À LEI DO INQUILINATO', 'CRÍTICA'),
            (r'Viol.*3\b', 'VIOLACAO_INQUILINATO_3', '🚨 VIOLAÇÃO 3 À LEI DO INQUILINATO', 'CRÍTICA'),
            (r'Viol.*4\b', 'VIOLACAO_INQUILINATO_4', '🚨 VIOLAÇÃO 4 À LEI DO INQUILINATO', 'CRÍTICA'),
            (r'Viol.*5\b', 'VIOLACAO_INQUILINATO_5', '🚨 VIOLAÇÃO 5 À LEI DO INQUILINATO', 'CRÍTICA'),
            (r'Viol.*6\b', 'VIOLACAO_INQUILINATO_6', '🚨 VIOLAÇÃO 6 À LEI DO INQUILINATO', 'CRÍTICA'),
            (r'Viol.*7\b', 'VIOLACAO_INQUILINATO_7', '🚨 VIOLAÇÃO 7 À LEI DO INQUILINATO', 'CRÍTICA'),
            (r'Viol.*8\b', 'VIOLACAO_INQUILINATO_8', '🚨 VIOLAÇÃO 8 À LEI DO INQUILINATO', 'CRÍTICA'),
            (r'Viol.*9\b', 'VIOLACAO_INQUILINATO_9', '🚨 VIOLAÇÃO 9 À LEI DO INQUILINATO', 'CRÍTICA'),
            (r'Viol.*10\b', 'VIOLACAO_INQUILINATO_10', '🚨 VIOLAÇÃO 10 À LEI DO INQUILINATO', 'CRÍTICA'),
        ]
    
    def detectar_tipo_documento(self, texto):
        """Detecção ULTRA precisa do tipo de documento"""
        if not texto:
            return 'DESCONHECIDO'
        
        texto_limpo = limpar_texto(texto).lower()
        
        # Verificação direta por termos chave
        if 'versão de teste' in texto_limpo or 'cláusula de risco' in texto_limpo:
            return 'CONTRATO_LOCACAO_TESTE'
        
        if 'nota fiscal' in texto_limpo or 'nfse' in texto_limpo or 'nfe' in texto_limpo:
            return 'NOTA_FISCAL'
        
        if 'empregador' in texto_limpo and 'empregado' in texto_limpo:
            return 'CONTRATO_TRABALHO'
        
        if 'locação' in texto_limpo or ('locador' in texto_limpo and 'locatário' in texto_limpo):
            return 'CONTRATO_LOCACAO'
        
        # Contagem de termos
        scores = {}
        for doc_type, termos in self.indicadores_tipo.items():
            score = 0
            for termo in termos:
                if termo.lower() in texto_limpo:
                    score += 3
            scores[doc_type] = score
        
        # Escolher o tipo com maior score
        if scores:
            tipo_detectado = max(scores.items(), key=lambda x: x[1])
            if tipo_detectado[1] > 0:
                return tipo_detectado[0]
        
        return 'DESCONHECIDO'
    
    def analisar_documento(self, texto):
        """Análise super agressiva e abrangente"""
        if not texto or len(texto) < 50:
            return [], 'DESCONHECIDO', self._calcular_metricas([])
        
        texto_limpo = limpar_texto(texto).lower()
        problemas = []
        
        # Determinar tipo de documento
        tipo_doc = self.detectar_tipo_documento(texto_limpo)
        
        # Análise específica por tipo
        if tipo_doc in self.padroes:
            for padrao in self.padroes[tipo_doc]['padroes']:
                try:
                    if re.search(padrao['regex'], texto_limpo, re.IGNORECASE | re.DOTALL):
                        problemas.append({
                            'tipo': self.padroes[tipo_doc]['nome'],
                            'problema_id': padrao['regex'][:50],
                            'descricao': padrao['descricao'],
                            'detalhe': padrao['detalhe'],
                            'lei': padrao['lei'],
                            'gravidade': padrao['gravidade'],
                            'posicao': 0
                        })
                except:
                    continue
        
        # Detecção especial para violações numeradas
        for regex, problema_id, descricao, gravidade in self.violacoes_numeradas:
            matches = re.findall(regex, texto_limpo, re.IGNORECASE)
            for match in matches:
                problemas.append({
                    'tipo': 'Violação Numerada',
                    'problema_id': problema_id,
                    'descricao': descricao,
                    'detalhe': f'Encontrada: {match}. O contrato lista explicitamente violações à legislação!',
                    'lei': 'Legislação trabalhista ou Lei do Inquilinato',
                    'gravidade': gravidade,
                    'posicao': 0
                })
        
        # Análise genérica adicional (para capturar qualquer violação)
        padroes_genéricos = [
            # Violações trabalhistas
            (r'\b900\b.*reais|\bR\$\s*900\b|\b800\b.*reais|\bR\$\s*800\b', 'SALARIO_ABAIXO_MINIMO_GENERICO', '🚨 SALÁRIO ABAIXO DO MÍNIMO LEGAL', 'CRÍTICA'),
            (r'jornada.*>.*8.*horas|trabalhar.*mais.*de.*8.*horas|jornada.*excessiva', 'JORNADA_EXCESSIVA_GENERICO', '⚠️ JORNADA ACIMA DE 8H DIÁRIAS', 'ALTA'),
            (r'sem.*horas.*extras|não.*paga.*horas.*extras', 'SEM_HORAS_EXTRAS_GENERICO', '🚨 HORAS EXTRAS NÃO REMUNERADAS', 'CRÍTICA'),
            
            # Violações de locação
            (r'multa.*>.*2.*meses', 'MULTA_EXCESSIVA_GENERICO', '🚨 MULTA ACIMA DE 2 MESES', 'CRÍTICA'),
            (r'caução.*>.*1.*mês', 'CAUCAO_EXCESSIVA_GENERICO', '⚠️ CAUÇÃO ACIMA DE 1 MÊS', 'ALTA'),
            (r'reajuste.*<.*12.*meses', 'REAJUSTE_FREQUENTE_GENERICO', '⚠️ REAJUSTE MAIS FREQUENTE QUE ANUAL', 'ALTA'),
            
            # Cláusulas abusivas
            (r'cláusula.*abusiva|cláusula.*ilegal|cláusula.*nula', 'CLAUSULA_PROBLEMATICA', '🚨 CLÁUSULA PROBLEMÁTICA IDENTIFICADA', 'CRÍTICA'),
            (r'renúncia.*direito|renúncia.*garantia', 'RENUNCIA_DIREITOS', '⚠️ RENÚNCIA A DIREITOS', 'ALTA'),
            
            # Valores numéricos suspeitos
            (r'\b12\b.*meses.*multa', 'MULTA_12_MESES_DIRETO', '🚨 MULTA DE 12 MESES ENCONTRADA', 'CRÍTICA'),
            (r'\b3\b.*meses.*caução', 'CAUCAO_3_MESES_DIRETO', '🚨 CAUÇÃO DE 3 MESES ENCONTRADA', 'CRÍTICA'),
            (r'\b30\b.*meses.*contrato', 'PRAZO_30_MESES', '📋 CONTRATO LONGO (30 MESES)', 'MÉDIA'),
            
            # Violações específicas dos documentos analisados
            (r'intervalo.*10.*minutos', 'INTERVALO_10_MINUTOS', '🚨🚨 INTERVALO DE 10 MINUTOS - VIOLAÇÃO GRAVÍSSIMA!', 'CRÍTICA'),
            (r'60.*horas.*semanais', 'JORNADA_60_HORAS', '🚨 JORNADA DE 60 HORAS SEMANAIS - ILEGAL!', 'CRÍTICA'),
            (r'reajuste.*dólar', 'REAJUSTE_DOLAR', '🚨 REAJUSTE PELO DÓLAR - ILEGAL!', 'CRÍTICA'),
            (r'cumulação.*garantia', 'CUMULACAO_GARANTIAS', '⚠️ CUMULAÇÃO DE GARANTIAS - ILEGAL', 'ALTA'),
            (r'despejo.*48.*horas', 'DESPEJO_48_HORAS', '🚨 DESPEJO EM 48 HORAS - ILEGAL!', 'CRÍTICA'),
        ]
        
        for regex, problema_id, descricao, gravidade in padroes_genéricos:
            if re.search(regex, texto_limpo, re.IGNORECASE):
                problemas.append({
                    'tipo': 'Violação Genérica',
                    'problema_id': problema_id,
                    'descricao': descricao,
                    'detalhe': 'Detectado por análise genérica do conteúdo',
                    'lei': 'Legislação brasileira aplicável',
                    'gravidade': gravidade,
                    'posicao': 0
                })
        
        # Busca direta por números problemáticos
        numeros_suspeitos = [
            (r'900', '🚨🚨 NÚMERO 900 ENCONTRADO - PROVÁVEL SALÁRIO ILEGAL', 'CRÍTICA'),
            (r'800', '🚨🚨 NÚMERO 800 ENCONTRADO - SALÁRIO ILEGAL EXTREMO', 'CRÍTICA'),
            (r'12.*multa|multa.*12', '🚨🚨 NÚMERO 12 COM "MULTA" - MULTA DE 12 MESES', 'CRÍTICA'),
            (r'3.*caução|caução.*3', '🚨 NÚMERO 3 COM "CAUÇÃO" - CAUÇÃO DE 3 MESES', 'ALTA'),
            (r'20%.*ano|ano.*20%', '⚠️ 20% AO ANO ENCONTRADO - REAJUSTE ABUSIVO', 'ALTA'),
            (r'30.*meses', '📋 CONTRATO DE 30 MESES - LONGO PRAZO', 'MÉDIA'),
            (r'60.*horas', '🚨 NÚMERO 60 COM "HORAS" - JORNADA EXCESSIVA', 'CRÍTICA'),
        ]
        
        for numero, descricao, gravidade in numeros_suspeitos:
            if re.search(numero, texto_limpo, re.IGNORECASE):
                problemas.append({
                    'tipo': 'Número Problemático',
                    'problema_id': f'NUMERO_{numero.replace(" ", "_")}',
                    'descricao': descricao,
                    'detalhe': 'Número potencialmente problemático encontrado no texto',
                    'lei': 'Legislação aplicável conforme contexto',
                    'gravidade': gravidade,
                    'posicao': 0
                })
        
        # Análise contextual avançada
        if tipo_doc == 'CONTRATO_TRABALHO':
            # Verificar múltiplas violações
            if texto_limpo.count('violação') > 5 or texto_limpo.count('viol') > 5:
                problemas.append({
                    'tipo': 'Contrato de Trabalho',
                    'problema_id': 'MULTIPLAS_VIOLACOES',
                    'descricao': '🚨🚨 CONTRATO COM MÚLTIPLAS VIOLAÇÕES À CLT!',
                    'detalhe': f'Documento contém {texto_limpo.count("violação") + texto_limpo.count("viol")} menções a violações trabalhistas',
                    'lei': 'CLT diversos artigos',
                    'gravidade': 'CRÍTICA',
                    'posicao': 0
                })
        
        if tipo_doc == 'CONTRATO_LOCACAO':
            # Verificar violações à Lei do Inquilinato
            if texto_limpo.count('violação') > 3 or 'lei 8.245' in texto_limpo:
                problemas.append({
                    'tipo': 'Contrato de Locação',
                    'problema_id': 'VIOLACOES_INQUILINATO',
                    'descricao': '🚨 CONTRATO COM VIOLAÇÕES À LEI DO INQUILINATO!',
                    'detalhe': 'Documento contém múltiplas violações à Lei 8.245/1991',
                    'lei': 'Lei 8.245/1991',
                    'gravidade': 'CRÍTICA',
                    'posicao': 0
                })
        
        # Remover duplicatas
        problemas_unicos = []
        problemas_vistos = set()
        for problema in problemas:
            chave = (problema['descricao'], problema['lei'])
            if chave not in problemas_vistos:
                problemas_vistos.add(chave)
                problemas_unicos.append(problema)
        
        return problemas_unicos, tipo_doc, self._calcular_metricas(problemas_unicos)
    
    def _calcular_metricas(self, problemas):
        """Cálculo agressivo de métricas"""
        total = len(problemas)
        criticos = sum(1 for p in problemas if 'CRÍTICA' in p.get('gravidade', ''))
        altos = sum(1 for p in problemas if 'ALTA' in p.get('gravidade', ''))
        medios = sum(1 for p in problemas if 'MÉDIA' in p.get('gravidade', ''))
        info = sum(1 for p in problemas if 'INFO' in p.get('gravidade', ''))
        
        # Penalização EXTREMA
        score = 100
        score -= criticos * 40  # -40 por crítica
        score -= altos * 25     # -25 por alta
        score -= medios * 10    # -10 por média
        score -= info * 0       # info não penaliza
        
        score = max(0, min(100, score))
        
        # Status ULTRA alarmante para problemas
        if criticos >= 5:
            status = '🚨🚨🚨 DOCUMENTO CRIMINAL - DENUNCIE!'
            cor = '#8B0000'
            nivel_risco = 'RISCO EXTREMO'
        elif criticos >= 3:
            status = '🚨🚨🚨 DOCUMENTO CRIMINOSO - NÃO ASSINE!'
            cor = '#FF0000'
            nivel_risco = 'RISCO MÁXIMO'
        elif criticos >= 1:
            status = '🚨🚨 MÚLTIPLAS VIOLAÇÕES GRAVES - PERIGO!'
            cor = '#FF4500'
            nivel_risco = 'ALTO RISCO'
        elif altos >= 2:
            status = '🚨 VIOLAÇÕES SÉRIAS - CONSULTE UM ADVOGADO!'
            cor = '#FF8C00'
            nivel_risco = 'RISCO ELEVADO'
        elif total > 0:
            status = '⚠️ PROBLEMAS DETECTADOS - REVISE COM CUIDADO'
            cor = '#FFD700'
            nivel_risco = 'RISCO MODERADO'
        else:
            status = '✅ DOCUMENTO APARENTEMENTE REGULAR'
            cor = '#27AE60'
            nivel_risco = 'BAIXO RISCO'
        
        return {
            'total': total,
            'criticos': criticos,
            'altos': altos,
            'medios': medios,
            'info': info,
            'score': round(score, 1),
            'status': status,
            'cor': cor,
            'nivel_risco': nivel_risco
        }

# --------------------------------------------------
# FUNÇÕES AUXILIARES - MELHORADAS
# --------------------------------------------------

def extrair_texto_pdf(arquivo):
    """Extração ULTRA robusta de texto de PDF"""
    try:
        texto_total = ""
        
        # Primeiro, ler o arquivo como bytes para verificação
        conteudo = arquivo.read()
        arquivo.seek(0)  # Voltar ao início para o pdfplumber
        
        # Tentar detectar encoding
        try:
            # Tentar como UTF-8
            preview = conteudo[:1000].decode('utf-8', errors='ignore')
        except:
            try:
                # Tentar como latin-1
                preview = conteudo[:1000].decode('latin-1', errors='ignore')
            except:
                preview = ""
        
        with pdfplumber.open(arquivo) as pdf:
            for i, pagina in enumerate(pdf.pages):
                try:
                    # Método 1: Extração padrão
                    texto = pagina.extract_text()
                    if texto and len(texto.strip()) > 20:
                        texto_total += texto + "\n\n"
                    else:
                        # Método 2: Extração com tolerância alta
                        texto = pagina.extract_text(
                            x_tolerance=5,
                            y_tolerance=5,
                            keep_blank_chars=False,
                            use_text_flow=True
                        )
                        if texto and len(texto.strip()) > 20:
                            texto_total += texto + "\n\n"
                        else:
                            # Método 3: Extrair por linhas
                            chars = pagina.chars
                            if chars:
                                linhas = {}
                                for char in chars:
                                    y = char['top']
                                    if y not in linhas:
                                        linhas[y] = []
                                    linhas[y].append(char)
                                
                                for y in sorted(linhas.keys()):
                                    linha_chars = sorted(linhas[y], key=lambda c: c['x0'])
                                    linha_texto = ''.join(c['text'] for c in linha_chars)
                                    if linha_texto.strip():
                                        texto_total += linha_texto + "\n"
                
                except Exception as e:
                    continue
        
        # Se ainda não tem texto suficiente, tentar métodos extremos
        if len(texto_total.strip()) < 100:
            try:
                # Usar OCR como último recurso (simulado)
                st.warning("⚠️ PDF difícil de ler. Usando métodos avançados...")
                
                # Extrair tabelas
                with pdfplumber.open(arquivo) as pdf:
                    for pagina in pdf.pages:
                        tabelas = pagina.extract_tables()
                        if tabelas:
                            for tabela in tabelas:
                                for linha in tabela:
                                    if linha:
                                        linha_texto = " | ".join(str(c).strip() for c in linha if c)
                                        if linha_texto:
                                            texto_total += linha_texto + "\n"
            except:
                pass
        
        texto_limpo = limpar_texto(texto_total)
        
        if not texto_limpo or len(texto_limpo) < 50:
            st.error("❌ Não foi possível extrair texto suficiente do PDF")
            return None
            
        return texto_limpo
        
    except Exception as e:
        st.error(f"❌ Erro crítico ao processar PDF: {str(e)}")
        return None

# --------------------------------------------------
# TELA DE LOGIN
# --------------------------------------------------

def mostrar_tela_login():
    """Tela de login"""
    st.markdown("""
    <div class="header-main">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>IA de Análise Documental</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'modo_auth' not in st.session_state:
        st.session_state.modo_auth = 'login'
    
    with st.container():
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        if st.session_state.modo_auth == 'login':
            st.markdown('<div class="auth-title">🔐 Entrar na Conta</div>', unsafe_allow_html=True)
            
            email = st.text_input("E-mail", placeholder="seu@email.com", key="login_email")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha", key="login_senha")
            
            if email == "pedrohenriquemarques720@gmail.com":
                st.info("🔑 **Conta Especial Detectada:** Use sua senha pessoal para acessar.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Entrar", use_container_width=True, key="btn_entrar"):
                    if email and senha:
                        sucesso, resultado = autenticar_usuario(email, senha)
                        if sucesso:
                            st.session_state.usuario = resultado
                            st.session_state.autenticado = True
                            
                            if email == "pedrohenriquemarques720@gmail.com":
                                st.success("✅ **Conta Especial:** Acesso concedido com créditos ilimitados!")
                            else:
                                st.success("✅ Login realizado com sucesso!")
                            
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {resultado}")
                    else:
                        st.warning("⚠️ Preencha todos os campos")
            
            with col2:
                if st.button("📝 Criar Conta", use_container_width=True, key="btn_criar_conta_login"):
                    st.session_state.modo_auth = 'cadastro'
                    st.rerun()
        
        else:
            st.markdown('<div class="auth-title">📝 Criar Nova Conta</div>', unsafe_allow_html=True)
            
            nome = st.text_input("Nome Completo", placeholder="Seu nome", key="cad_nome")
            email = st.text_input("E-mail", placeholder="seu@email.com", key="cad_email")
            senha = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", key="cad_senha")
            confirmar_senha = st.text_input("Confirmar Senha", type="password", placeholder="Digite novamente", key="cad_confirmar")
            
            st.info("ℹ️ **Importante:** Novas contas começam com 0 BuroCreds. Para adquirir créditos, entre em contato com o suporte.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎉 Criar Conta", use_container_width=True, key="btn_criar"):
                    if nome and email and senha and confirmar_senha:
                        if senha != confirmar_senha:
                            st.error("❌ As senhas não coincidem")
                        elif len(senha) < 6:
                            st.error("❌ A senha deve ter no mínimo 6 caracteres")
                        else:
                            sucesso, mensagem = criar_usuario(nome, email, senha)
                            if sucesso:
                                st.success(f"✅ {mensagem}")
                                sucesso_login, usuario = autenticar_usuario(email, senha)
                                if sucesso_login:
                                    st.session_state.usuario = usuario
                                    st.session_state.autenticado = True
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.error(f"❌ {mensagem}")
                    else:
                        st.warning("⚠️ Preencha todos os campos")
            
            with col2:
                if st.button("🔙 Voltar ao Login", use_container_width=True, key="btn_voltar"):
                    st.session_state.modo_auth = 'login'
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    mostrar_faq_rodape()

# --------------------------------------------------
# CABEÇALHO DO USUÁRIO
# --------------------------------------------------

def mostrar_cabecalho_usuario():
    """Mostra o cabeçalho simplificado com informações do usuário"""
    usuario = st.session_state.usuario
    
    is_conta_especial = usuario['email'] == "pedrohenriquemarques720@gmail.com"
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="user-profile">
                <h3 style="color: #F8D96D; margin: 0; font-size: 1.8em;">
                    👤 {usuario['nome']}
                </h3>
                <p style="color: #FFFFFF; margin: 5px 0 0 0;">{usuario['email']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: #1a3658;
                      padding: 20px;
                      border-radius: 15px;
                      border: 2px solid #F8D96D;
                      text-align: center;
                      box-shadow: 0 5px 15px rgba(0,0,0,0.3);">
                <div style="font-size: 2em; color: #F8D96D; font-weight: 700;">
                    {'∞' if is_conta_especial else usuario['burocreds']}
                </div>
                <div style="color: #FFFFFF; font-size: 0.9em;">BuroCreds</div>
            </div>
            """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Atualizar Dados", use_container_width=True, key="btn_atualizar"):
            usuario_atualizado = get_usuario_por_id(usuario['id'])
            if usuario_atualizado:
                st.session_state.usuario = usuario_atualizado
                st.success("✅ Dados atualizados!")
                time.sleep(0.5)
                st.rerun()
    
    with col2:
        if st.button("🚪 Sair", use_container_width=True, key="btn_sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# --------------------------------------------------
# SEÇÃO: O QUE ANALISAMOS
# --------------------------------------------------

def mostrar_secao_analises():
    """Mostra a seção com os tipos de documentos que analisamos"""
    st.markdown("""
    <div style="text-align: center; margin: 40px 0 30px 0;">
        <h2 style="color: #F8D96D; font-size: 2.2em; margin-bottom: 10px;">
            📋 O QUE ANALISAMOS
        </h2>
        <p style="color: #FFFFFF; font-size: 1.1em; max-width: 800px; margin: 0 auto;">
            Nossa inteligência artificial verifica os pontos mais importantes dos seus documentos jurídicos
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">🏠</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Contrato de Locação</div>', unsafe_allow_html=True)
            
            # Itens do contrato de locação
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Valor do Aluguel e Reajuste</div>
                <div class="analise-item-desc">Onde dói no bolso (ou entra o dinheiro).</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Vigência e Prazo</div>
                <div class="analise-item-desc">Quanto tempo dura o "felizes para sempre".</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Conservação e Reformas</div>
                <div class="analise-item-desc">Quem paga pelo cano que estourou.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Multas e Rescisão</div>
                <div class="analise-item-desc">O preço de sair antes da hora.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Garantia Locatória</div>
                <div class="analise-item-desc">O famoso fiador, caução ou seguro.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">💼</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Contrato de Emprego</div>', unsafe_allow_html=True)
            
            # Itens do contrato de emprego
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Remuneração e Benefícios</div>
                <div class="analise-item-desc">Salário, VR, VT e os mimos.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Jornada de Trabalho</div>
                <div class="analise-item-desc">O horário de bater o ponto.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Atribuições do Cargo</div>
                <div class="analise-item-desc">O que, afinal, você foi contratado para fazer.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Confidencialidade</div>
                <div class="analise-item-desc">O que acontece na empresa, morre na empresa.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Aviso Prévio e Rescisão</div>
                <div class="analise-item-desc">As regras do adeus.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">🧾</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Notas Fiscais</div>', unsafe_allow_html=True)
            
            # Itens das notas fiscais
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Dados do Emissor/Destinatário</div>
                <div class="analise-item-desc">Quem vendeu e quem comprou.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Itens e Serviços</div>
                <div class="analise-item-desc">A lista de compras detalhada.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Impostos e Tributação</div>
                <div class="analise-item-desc">A fatia que fica para o governo.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Valor Total e Descontos</div>
                <div class="analise-item-desc">O número final da conta.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Status de Pagamento</div>
                <div class="analise-item-desc">Se já caiu na conta ou se ainda é promessa.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 40px 0;'></div>", unsafe_allow_html=True)

# --------------------------------------------------
# FAQ NO RODAPÉ
# --------------------------------------------------

def mostrar_faq_rodape():
    """Mostra a seção de FAQ no rodapé"""
    st.markdown("---")
    
    with st.container():
        st.markdown('<div class="faq-container">', unsafe_allow_html=True)
        
        st.markdown('<h3 style="color: #F8D96D; text-align: center; margin-bottom: 20px;">❓ Perguntas Frequentes</h3>', unsafe_allow_html=True)
        
        # FAQ Items
        st.markdown('<div class="faq-question">1. Como adquirir BuroCreds?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Assista a videos<strong>ou nos contate pelo contatoburocrata@outlook.com</strong> solicitando créditos. Você receberá instruções para pagamento e ativação.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">2. Quanto custa cada análise?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Cada análise de documento custa <strong>10 BuroCreds</strong>.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">3. Posso analisar vários documentos de uma vez?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Atualmente, o sistema analisa um documento por vez. Cada análise consome 10 BuroCreds.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">4. Quais tipos de documentos são suportados?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Analisamos contratos de locação, emprego, serviços e compra e venda em formato PDF.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">5. Como funciona o Plano PRO?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">O Plano PRO oferece análises profundas e recursos avançados. Entre em contato para mais informações.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">6. Precisa de suporte ou tem reclamações?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Entre em contato: <strong>contatoburocrata@outlook.com</strong> - Respondemos em até 24h.</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Links sociais
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="social-links">
            <a href="https://www.instagram.com/burocratadebolso/" target="_blank" class="social-link">
                📷 Instagram
            </a>
            <a href="mailto:contatoburocrata@outlook.com" class="social-link">
                📧 E-mail
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    # Rodapé final
    st.markdown("""
    <div style="text-align: center; color: #FFFFFF; margin-top: 30px; padding: 20px;">
        <p><strong>⚖️ Burocrata de Bolso</strong> • IA de análise documental • v2.1</p>
        <p style="font-size: 0.9em;">Para suporte técnico: contatoburocrata@outlook.com</p>
        <p style="font-size: 0.8em; color: #F8D96D; margin-top: 10px;">
            © 2026 Burocrata de Bolso. Todos os direitos reservados.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# TELA PRINCIPAL
# --------------------------------------------------

def mostrar_tela_principal():
    """Tela principal após login"""
    
    st.markdown("""
    <div class="header-main">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>IA de Análise Documental</p>
    </div>
    """, unsafe_allow_html=True)
    
    mostrar_cabecalho_usuario()
    
    is_conta_especial = st.session_state.usuario['email'] == "pedrohenriquemarques720@gmail.com"
    
    hora = datetime.now().hour
    if hora < 12:
        saudacao = "Bom dia"
    elif hora < 18:
        saudacao = "Boa tarde"
    else:
        saudacao = "Boa noite"
    
    nome_usuario = st.session_state.usuario['nome'].split()[0]
    
    if is_conta_especial:
        st.markdown(f"""
        <div style="background: #F8D96D;
                    padding: 25px;
                    border-radius: 15px;
                    margin: 20px 0;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(248, 217, 109, 0.3);">
            <h3 style="color: #10263D; margin-top: 0; font-size: 1.8em;">
                👋 {saudacao}, {nome_usuario}!
            </h3>
            <p style="color: #10263D; margin-bottom: 0; font-size: 1.1em; font-weight: 600;">
                🚀 <strong>Modo Desenvolvedor Ativo:</strong> Você tem <strong>créditos ilimitados</strong> para testar o sistema.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: #F8D96D;
                    padding: 25px;
                    border-radius: 15px;
                    margin: 20px 0;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(248, 217, 109, 0.3);">
            <h3 style="color: #10263D; margin-top: 0; font-size: 1.8em;">
                👋 {saudacao}, {nome_usuario}!
            </h3>
            <p style="color: #10263D; margin-bottom: 0; font-size: 1.1em; font-weight: 600;">
                Analise seus documentos com precisão jurídica. Cada análise custa <strong>10 BuroCreds</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    mostrar_secao_analises()
    
    detector = SistemaDetecção()
    
    st.markdown("""
    <div style="text-align: center; margin: 30px 0;">
        <div style="font-size: 2em; color: #F8D96D; margin-bottom: 10px;">📄</div>
        <h3 style="color: #F8D96D;">Envie seu documento para análise</h3>
        <p style="color: #FFFFFF;">Formatos suportados: PDF • Até 10MB</p>
    </div>
    """, unsafe_allow_html=True)
    
    arquivo = st.file_uploader("Selecione um arquivo PDF", type=["pdf"], key="file_uploader")
    
    if arquivo:
        if not is_conta_especial and st.session_state.usuario['burocreds'] < 10:
            st.error("""
            ❌ **Saldo insuficiente!** 
            
            Você precisa de pelo menos **10 BuroCreds** para realizar uma análise.
            
            **Solução:** Entre em contato com o suporte para adquirir créditos.
            """)
        else:
            with st.spinner(f"🔍 Analisando juridicamente '{arquivo.name}'..."):
                texto = extrair_texto_pdf(arquivo)
                
                if texto:
                    problemas, tipo_doc, metricas = detector.analisar_documento(texto)
                    
                    if st.session_state.usuario['id']:
                        registrar_analise(
                            st.session_state.usuario['id'],
                            arquivo.name,
                            tipo_doc,
                            metricas['total'],
                            metricas['score']
                        )
                        
                        if not is_conta_especial:
                            atualizar_burocreds(st.session_state.usuario['id'], -10)
                            st.session_state.usuario['burocreds'] -= 10
                    
                    # Mostrar resumo da análise
                    st.markdown("### 📊 Resultados da Análise Jurídica")
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div style="font-size: 2em; margin-right: 15px;">⚖️</div>
                            <div>
                                <h3 style="color: {metricas['cor']}; margin: 0;">{metricas['status']}</h3>
                                <p style="color: #FFFFFF; margin: 5px 0 0 0;">
                                    <strong>Documento:</strong> {arquivo.name}
                                    {f"• <strong>Tipo:</strong> {detector.padroes.get(tipo_doc, {}).get('nome', 'Documento')}" if tipo_doc != 'DESCONHECIDO' else ''}
                                    • <strong>Nível de Risco:</strong> {metricas['nivel_risco']}
                                </p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Métricas detalhadas
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Problemas Detectados", metricas['total'], delta_color="inverse")
                    
                    with col2:
                        st.metric("Críticos", metricas['criticos'], delta_color="inverse")
                    
                    with col3:
                        st.metric("Altos", metricas['altos'], delta_color="inverse")
                    
                    with col4:
                        st.metric("Score Conformidade", f"{metricas['score']}%")
                    
                    with col5:
                        if is_conta_especial:
                            st.metric("BuroCreds Restantes", "∞")
                        else:
                            st.metric("BuroCreds Restantes", st.session_state.usuario['burocreds'], delta=-10)
                    
                    # Detalhes dos problemas detectados
                    if problemas:
                        st.markdown("### ⚖️ Problemas Jurídicos Detectados")
                        
                        # Agrupar por gravidade
                        problemas_criticos = [p for p in problemas if p['gravidade'] == 'CRÍTICA']
                        problemas_altos = [p for p in problemas if p['gravidade'] == 'ALTA']
                        problemas_medios = [p for p in problemas if p['gravidade'] == 'MÉDIA']
                        
                        if problemas_criticos:
                            st.markdown("#### 🔴 Problemas Críticos (Requerem Atenção Imediata)")
                            for i, problema in enumerate(problemas_criticos, 1):
                                st.markdown(f"""
                                <div style="background: rgba(231, 76, 60, 0.15);
                                          border-left: 4px solid #E74C3C;
                                          padding: 20px;
                                          border-radius: 10px;
                                          margin: 10px 0;
                                          box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
                                    <div style="display: flex; align-items: flex-start;">
                                        <div style="font-size: 1.5em; margin-right: 15px; color: #E74C3C;">🔴</div>
                                        <div style="flex: 1;">
                                            <h4 style="margin: 0 0 8px 0; color: #E74C3C;">
                                                {problema['descricao']}
                                            </h4>
                                            <p style="margin: 5px 0; color: #FFFFFF;">
                                                <strong>Base Legal:</strong> {problema['lei']}
                                            </p>
                                            <p style="margin: 5px 0; color: #e2e8f0; font-size: 0.9em;">
                                                {problema.get('detalhe', '')}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if problemas_altos:
                            st.markdown("#### 🟠 Problemas Altos (Ajustes Necessários)")
                            for i, problema in enumerate(problemas_altos, 1):
                                st.markdown(f"""
                                <div style="background: rgba(243, 156, 18, 0.15);
                                          border-left: 4px solid #F39C12;
                                          padding: 20px;
                                          border-radius: 10px;
                                          margin: 10px 0;
                                          box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
                                    <div style="display: flex; align-items: flex-start;">
                                        <div style="font-size: 1.5em; margin-right: 15px; color: #F39C12;">🟠</div>
                                        <div style="flex: 1;">
                                            <h4 style="margin: 0 0 8px 0; color: #F39C12;">
                                                {problema['descricao']}
                                            </h4>
                                            <p style="margin: 5px 0; color: #FFFFFF;">
                                                <strong>Base Legal:</strong> {problema['lei']}
                                            </p>
                                            <p style="margin: 5px 0; color: #e2e8f0; font-size: 0.9em;">
                                                {problema.get('detalhe', '')}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if problemas_medios:
                            st.markdown("#### 🟡 Problemas Médios (Revisão Recomendada)")
                            for i, problema in enumerate(problemas_medios, 1):
                                st.markdown(f"""
                                <div style="background: rgba(241, 196, 15, 0.15);
                                          border-left: 4px solid #F1C40F;
                                          padding: 20px;
                                          border-radius: 10px;
                                          margin: 10px 0;
                                          box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
                                    <div style="display: flex; align-items: flex-start;">
                                        <div style="font-size: 1.5em; margin-right: 15px; color: #F1C40F;">🟡</div>
                                        <div style="flex: 1;">
                                            <h4 style="margin: 0 0 8px 0; color: #F1C40F;">
                                                {problema['descricao']}
                                            </h4>
                                            <p style="margin: 5px 0; color: #FFFFFF;">
                                                <strong>Base Legal:</strong> {problema['lei']}
                                            </p>
                                            <p style="margin: 5px 0; color: #e2e8f0; font-size: 0.9em;">
                                                {problema.get('detalhe', '')}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Recomendação jurídica
                        st.markdown("""
                        <div style="background: #1a3658;
                                  padding: 20px;
                                  border-radius: 15px;
                                  margin: 20px 0;
                                  border: 2px solid #F8D96D;">
                            <h4 style="color: #F8D96D; margin-top: 0;">💡 Recomendação Jurídica</h4>
                            <p style="color: #FFFFFF; margin-bottom: 0;">
                                <strong>Atenção:</strong> Esta análise identifica potenciais problemas jurídicos com base na legislação brasileira vigente. 
                                Para validação completa e assessoria jurídica personalizada, recomenda-se a consulta com um advogado especializado.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    else:
                        st.success("""
                        ### ✅ Excelente! Nenhum problema jurídico detectado.
                        
                        Seu documento parece estar em conformidade com os padrões legais analisados.
                        Para uma avaliação jurídica completa, ainda recomenda-se consultar um advogado.
                        """)
                        st.balloons()
                    
                    # Botão para nova análise
                    st.markdown("---")
                    if st.button("🔄 Realizar Nova Análise", use_container_width=True, type="primary"):
                        st.rerun()
                    
                else:
                    st.error("""
                    ❌ **Não foi possível analisar o documento**
                    
                    Possíveis causas:
                    - O arquivo PDF está corrompido
                    - O PDF está protegido por senha
                    - O arquivo está em formato de imagem (não contém texto)
                    - O arquivo está muito grande
                    
                    **Solução:** Certifique-se de que o PDF contém texto selecionável.
                    """)
    
    # Histórico de análises
    historico = get_historico_usuario(st.session_state.usuario['id'])
    if historico:
        with st.expander("📜 Histórico de Análises (Últimas 5)", expanded=False):
            for item in historico:
                score_cor = "#27AE60" if item['score'] >= 80 else "#F39C12" if item['score'] >= 60 else "#E74C3C"
                
                st.markdown(f"""
                <div style="background: #1a3658;
                          padding: 15px;
                          border-radius: 10px;
                          margin: 10px 0;
                          border: 1px solid #F8D96D;
                          box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <strong style="color: #F8D96D;">{item['arquivo']}</strong>
                            <div style="color: #FFFFFF; font-size: 0.9em; margin-top: 5px;">
                                <span style="background: #2a4a75; padding: 2px 8px; border-radius: 4px; margin-right: 10px;">
                                    {item['tipo'] or 'Geral'}
                                </span>
                                <span>⚖️ {item['problemas']} problemas</span>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.2em; color: {score_cor}; font-weight: 700;">
                                {item['score']:.1f}%
                            </div>
                            <div style="color: #FFFFFF; font-size: 0.8em;">
                                {item['data'].split()[0] if ' ' in str(item['data']) else item['data']}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    if not is_conta_especial:
        st.markdown("---")
        st.markdown("""
        <div style="background: #1a3658;
                    padding: 20px;
                    border-radius: 15px;
                    margin: 20px 0;
                    border: 2px solid #F8D96D;">
            <h4 style="color: #F8D96D; margin-top: 0;">💰 Sobre os BuroCreds</h4>
            <ul style="color: #FFFFFF; margin-bottom: 0;">
                <li>Cada análise custa <strong>10 BuroCreds</strong></li>
                <li>Para adquirir créditos: <strong>Veja vídeos ou nos chame em contatoburocrata@outlook.com</strong></li>
                <li>Plano PRO: Análises profundas + recursos avançados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    mostrar_faq_rodape()

# --------------------------------------------------
# APLICATIVO PRINCIPAL
# --------------------------------------------------

def main():
    """Função principal do aplicativo"""
    
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        mostrar_tela_login()
    else:
        mostrar_tela_principal()

if __name__ == "__main__":
    main()
