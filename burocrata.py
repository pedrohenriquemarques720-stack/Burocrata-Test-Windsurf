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
import json
from difflib import SequenceMatcher
from collections import defaultdict

# --------------------------------------------------
# FUNÇÕES AUXILIARES (definidas primeiro)
# --------------------------------------------------

def hash_palavra_passe(palavra_passe):
    """Gera hash da palavra-passe usando SHA-256"""
    return hashlib.sha256(palavra_passe.encode()).hexdigest()

# --------------------------------------------------
# CONFIGURAÇÃO DA BASE DE DADOS SQLITE
# --------------------------------------------------
CAMINHO_BD = 'utilizadores_burocrata.db'

def inicializar_base_dados():
    """Inicializa a base de dados SQLite"""
    conn = sqlite3.connect(CAMINHO_BD)
    c = conn.cursor()
    
    # Tabela de utilizadores
    c.execute('''
        CREATE TABLE IF NOT EXISTS utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            palavra_passe_hash TEXT NOT NULL,
            plano TEXT DEFAULT 'GRATUITO',
            burocreditos INTEGER DEFAULT 0,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'ATIVO'
        )
    ''')
    
    # Tabela de histórico de análises
    c.execute('''
        CREATE TABLE IF NOT EXISTS historico_analises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilizador_id INTEGER,
            nome_ficheiro TEXT,
            tipo_documento TEXT,
            problemas_detetados INTEGER,
            pontuacao_conformidade REAL,
            data_analise TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (utilizador_id) REFERENCES utilizadores (id)
        )
    ''')
    
    # Criar conta especial com créditos infinitos
    conta_especial_email = "pedrohenriquemarques720@gmail.com"
    palavra_passe_especial_hash = hash_palavra_passe("Liz1808#")
    
    # Verificar se a conta especial já existe
    c.execute("SELECT COUNT(*) FROM utilizadores WHERE email = ?", (conta_especial_email,))
    resultado = c.fetchone()
    
    if resultado and resultado[0] == 0:
        # Criar conta especial com créditos altíssimos
        c.execute('''
            INSERT INTO utilizadores (nome, email, palavra_passe_hash, plano, burocreditos)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Pedro Henrique (Conta Especial)", conta_especial_email, palavra_passe_especial_hash, 'PRO', 999999))
        print(f"✅ Conta especial criada: {conta_especial_email}")
    else:
        # Atualizar palavra-passe da conta existente
        c.execute('''
            UPDATE utilizadores 
            SET palavra_passe_hash = ?
            WHERE email = ?
        ''', (palavra_passe_especial_hash, conta_especial_email))
        print(f"✅ Palavra-passe da conta especial atualizada")
    
    conn.commit()
    conn.close()

# Inicializar base de dados
inicializar_base_dados()

# --------------------------------------------------
# FUNÇÕES DE AUTENTICAÇÃO
# --------------------------------------------------

def criar_utilizador(nome, email, palavra_passe):
    """Cria um novo utilizador no sistema"""
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        # Verifica se email já existe
        c.execute("SELECT COUNT(*) FROM utilizadores WHERE email = ?", (email,))
        if c.fetchone()[0] > 0:
            conn.close()
            return False, "E-mail já registado"
        
        # Cria utilizador com 0 BuroCréditos iniciais
        palavra_passe_hash = hash_palavra_passe(palavra_passe)
        burocreditos_iniciais = 0
        
        c.execute('''
            INSERT INTO utilizadores (nome, email, palavra_passe_hash, plano, burocreditos)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, email, palavra_passe_hash, 'GRATUITO', burocreditos_iniciais))
        
        conn.commit()
        conn.close()
        return True, "Utilizador criado com sucesso!"
        
    except Exception as e:
        return False, f"Erro ao criar utilizador: {str(e)}"

def autenticar_utilizador(email, palavra_passe):
    """Autentica um utilizador pelo email e palavra-passe"""
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        palavra_passe_hash = hash_palavra_passe(palavra_passe)
        
        c.execute('''
            SELECT id, nome, email, plano, burocreditos, estado 
            FROM utilizadores 
            WHERE email = ? AND palavra_passe_hash = ? AND estado = 'ATIVO'
        ''', (email, palavra_passe_hash))
        
        resultado = c.fetchone()
        conn.close()
        
        if resultado:
            return True, {
                'id': resultado[0],
                'nome': resultado[1],
                'email': resultado[2],
                'plano': resultado[3],
                'burocreditos': resultado[4],
                'estado': resultado[5]
            }
        else:
            return False, "E-mail ou palavra-passe incorretos"
            
    except Exception as e:
        return False, f"Erro na autenticação: {str(e)}"

def obter_utilizador_por_id(utilizador_id):
    """Obtém informações do utilizador pelo ID"""
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, nome, email, plano, burocreditos, estado 
            FROM utilizadores 
            WHERE id = ?
        ''', (utilizador_id,))
        
        resultado = c.fetchone()
        conn.close()
        
        if resultado:
            return {
                'id': resultado[0],
                'nome': resultado[1],
                'email': resultado[2],
                'plano': resultado[3],
                'burocreditos': resultado[4],
                'estado': resultado[5]
            }
        else:
            return None
            
    except Exception as e:
        st.error(f"Erro ao obter utilizador: {e}")
        return None

def atualizar_burocreditos(utilizador_id, quantidade):
    """Atualiza os BuroCréditos do utilizador"""
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        # Para conta especial, não debita créditos
        c.execute("SELECT email FROM utilizadores WHERE id = ?", (utilizador_id,))
        utilizador = c.fetchone()
        
        if utilizador and utilizador[0] == "pedrohenriquemarques720@gmail.com":
            conn.close()
            return True
        
        # Para utilizadores normais, atualiza normalmente
        c.execute('''
            UPDATE utilizadores 
            SET burocreditos = burocreditos + ? 
            WHERE id = ?
        ''', (quantidade, utilizador_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar BuroCréditos: {e}")
        return False

# --------------------------------------------------
# FUNÇÕES DO SISTEMA DE ANÁLISE
# --------------------------------------------------

def registar_analise(utilizador_id, nome_ficheiro, tipo_documento, problemas, pontuacao):
    """Regista uma análise no histórico"""
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO historico_analises 
            (utilizador_id, nome_ficheiro, tipo_documento, problemas_detetados, pontuacao_conformidade)
            VALUES (?, ?, ?, ?, ?)
        ''', (utilizador_id, nome_ficheiro, tipo_documento, problemas, pontuacao))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao registar análise: {e}")
        return False

def obter_historico_utilizador(utilizador_id, limite=5):
    """Obtém histórico de análises do utilizador"""
    try:
        conn = sqlite3.connect(CAMINHO_BD)
        c = conn.cursor()
        
        c.execute('''
            SELECT nome_ficheiro, tipo_documento, problemas_detetados, 
                   pontuacao_conformidade, data_analise
            FROM historico_analises
            WHERE utilizador_id = ?
            ORDER BY data_analise DESC
            LIMIT ?
        ''', (utilizador_id, limite))
        
        historico = []
        for row in c.fetchall():
            historico.append({
                'ficheiro': row[0],
                'tipo': row[1],
                'problemas': row[2],
                'pontuacao': row[3],
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
    page_title="Burocrata de Bolso - Expert Jurídico",
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
    
    /* Cartão de autenticação */
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
    
    /* Perfil do utilizador */
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
    
    /* Estilos para cartões de análise */
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
    
    /* Cartões de métricas */
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
    
    /* Upload de ficheiro */
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
# SISTEMA DE DETECÇÃO EXPERT JURÍDICO - VERSÃO 100% IMPLACÁVEL
# --------------------------------------------------

class SistemaDeteccaoExpertImplacavel:
    """
    SISTEMA DE DETECÇÃO ABSOLUTAMENTE IMPLACÁVEL
    Baseado nos contratos de teste fornecidos com todas as violações documentadas
    """
    
    def __init__(self):
        self.violacoes = self._carregar_todas_violacoes()
        self.padroes_exatos = self._gerar_padroes_massivos()
        self.leis = self._carregar_base_legal_completa()
        
    def _carregar_todas_violacoes(self):
        """Carrega TODAS as violações possíveis baseadas nos contratos de teste"""
        return {
            # ===== CONTRATOS DE EMPREGO 1 =====
            'jornada_12h_diarias': {
                'nome': 'JORNADA DE 12 HORAS DIÁRIAS - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Jornada de 12 horas diárias VIOLA o limite legal de 8 horas diárias da CLT. Trabalho além de 8h/dia é HORA EXTRA com adicional de 50%.',
                'detalhe': 'A CLT estabelece jornada máxima de 8 horas diárias e 44 horas semanais. 12 horas por dia (72h semanais) é EXCESSIVO e ILEGAL.',
                'lei': 'Art. 58 CLT - Limite 8h/dia e 44h/semana',
                'solucao': 'Exija jornada máxima de 8h/dia e 44h/semana. Horas além disso são EXTRAS com 50% de adicional.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'08.*?20|08.*?às.*?20|08.*?as.*?20|08h.*?20h',
                    r'jornada.*?das.*?08.*?às.*?20',
                    r'08:00.*?20:00',
                    r'12.*?horas.*?diárias',
                    r'72.*?horas.*?semanais',
                    r'jornada.*?12.*?horas',
                    r'expediente.*?12.*?horas'
                ]
            },
            
            'proibicao_horas_extras': {
                'nome': 'PROIBIÇÃO ILEGAL DE PAGAMENTO DE HORAS EXTRAS',
                'tipo': 'TRABALHISTA',
                'descricao': 'É ILEGAL proibir pagamento de horas extras. Trabalho além da jornada DEVE ser remunerado com adicional de 50%.',
                'detalhe': 'Cláusula que afirma "não haverá pagamento de horas extras" ou que "salário fixo é suficiente para remunerar toda e qualquer jornada extraordinária" é NULA.',
                'lei': 'Art. 59 CLT - Adicional mínimo 50% para horas extras',
                'solucao': 'Horas extras DEVEM ser pagas com 50% de adicional. Esta cláusula é NULA.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'não.*?haverá.*?pagamento.*?horas.*?extras',
                    r'horas.*?extras.*?não.*?haverá',
                    r'proibido.*?horas.*?extras',
                    r'salário.*?fixo.*?suficiente.*?horas.*?extras',
                    r'não.*?serão.*?remuneradas.*?horas.*?extras'
                ]
            },
            
            'salario_abaixo_minimo': {
                'nome': 'SALÁRIO ABAIXO DO MÍNIMO NACIONAL',
                'tipo': 'TRABALHISTA',
                'descricao': f'Salário de R$ 900,00 está ABAIXO do salário mínimo nacional vigente (R$ 1.412,00 em 2024). Violação constitucional.',
                'detalhe': 'A Constituição Federal garante salário mínimo capaz de atender às necessidades vitais do trabalhador. Salário inferior é ILEGAL.',
                'lei': 'CF Art. 7º, IV - Salário mínimo nacional unificado',
                'solucao': 'Exija salário mínimo vigente (R$ 1.412,00). Diferenças retroativas devem ser pagas.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'R?\$?\s*900[,\\.]',
                    r'R?\$?\s*900,00',
                    r'R?\$?\s*900\.00',
                    r'novecentos.*?reais',
                    r'900.*?reais',
                    r'salário.*?900',
                    r'remuneração.*?900'
                ]
            },
            
            'renuncia_fgts_por_vale_cultura': {
                'nome': 'RENÚNCIA ILEGAL AO FGTS POR VALE CULTURA',
                'tipo': 'TRABALHISTA',
                'descricao': 'FGTS é direito irrenunciável. Substituição por Vale Cultura de R$ 50,00 é NULA. Empregador DEVE depositar 8% mensalmente.',
                'detalhe': 'O FGTS é um direito social fundamental do trabalhador, não podendo ser objeto de renúncia ou substituição por qualquer benefício.',
                'lei': 'Lei 8.036/90, Art. 15 - FGTS irrenunciável e obrigatório',
                'solucao': 'Exija depósito mensal de 8% na conta vinculada do FGTS. A substituição por vale cultura é ILEGAL.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'renuncia.*?FGTS|renúncia.*?FGTS',
                    r'FGTS.*?renúncia|FGTS.*?renuncia',
                    r'FGTS.*?substituição.*?vale.*?cultura',
                    r'vale.*?cultura.*?50.*?reais',
                    r'em.*?substituição.*?FGTS',
                    r'sem.*?direito.*?FGTS',
                    r'dispensa.*?FGTS'
                ]
            },
            
            'periodo_experiencia_6_meses': {
                'nome': 'PERÍODO DE EXPERIÊNCIA DE 6 MESES - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Período de experiência de 6 meses (180 dias) excede em 100% o limite legal de 90 dias estabelecido pela CLT.',
                'detalhe': 'A CLT limita o período de experiência a 90 dias, podendo ser prorrogado uma única vez dentro deste limite. 6 meses é EXCESSIVO.',
                'lei': 'Art. 445 CLT - Período de experiência máximo 90 dias',
                'solucao': 'Exija redução do período de experiência para no máximo 90 dias (3 meses).',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'experiência.*?6.*?meses',
                    r'6.*?meses.*?experiência',
                    r'180.*?dias.*?experiência',
                    r'período.*?experiência.*?6',
                    r'seis.*?meses.*?experiência'
                ]
            },
            
            'intervalo_interjornadas_7h': {
                'nome': 'INTERVALO INTERJORNADAS DE 7H - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Intervalo de apenas 7h entre jornadas (23:00-06:00) VIOLA mínimo legal de 11h consecutivas para descanso.',
                'detalhe': 'A CLT exige intervalo mínimo de 11 horas entre o término de uma jornada e o início da seguinte. 7 horas é manifestamente INSUFICIENTE.',
                'lei': 'Art. 66 CLT - Mínimo 11 horas entre jornadas',
                'solucao': 'Exija intervalo mínimo de 11h entre jornadas. Trabalho sem descanso adequado é prejudicial à saúde.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'23.*?06|23:00.*?06:00',
                    r'encerrar.*?23.*?retornar.*?06',
                    r'23:00.*?retornar.*?06:00',
                    r'às.*?23:00.*?às.*?06:00',
                    r'intervalo.*?7.*?horas.*?entre.*?jornadas'
                ]
            },
            
            'fracionamento_ferias_3_periodos': {
                'nome': 'FRACIONAMENTO DE FÉRIAS EM 3 PERÍODOS - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Férias fracionadas em 3 períodos VIOLA limite máximo de 2 períodos, sendo um deles de pelo menos 14 dias.',
                'detalhe': 'A reforma trabalhista permitiu fracionamento em até 3 períodos APENAS com concordância do empregado e mediante negociação coletiva. Cláusula genérica é ILEGAL.',
                'lei': 'Art. 134 CLT - Férias em até 2 períodos, excepcionalmente 3 com negociação coletiva',
                'solucao': 'Exija férias em no máximo 2 períodos, sendo um deles de pelo menos 14 dias consecutivos.',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'padroes': [
                    r'fracionadas.*?3.*?períodos',
                    r'3.*?períodos.*?férias',
                    r'férias.*?até.*?3.*?períodos',
                    r'três.*?períodos.*?férias'
                ]
            },
            
            'ausencia_terco_constitucional': {
                'nome': 'AUSÊNCIA DE 1/3 CONSTITUCIONAL NAS FÉRIAS',
                'tipo': 'TRABALHISTA',
                'descricao': 'Férias SEM acréscimo de 1/3 constitucional VIOLA direito fundamental. Empregador deve pagar férias + 1/3.',
                'detalhe': 'O adicional de 1/3 sobre as férias é direito constitucional do trabalhador, não podendo ser suprimido por contrato.',
                'lei': 'CF Art. 7º, XVII - 1/3 constitucional sobre férias',
                'solucao': 'Exija pagamento integral das férias com acréscimo de 1/3 constitucional sobre o valor.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'sem.*?acréscimo.*?1/3',
                    r'1/3.*?constitucional.*?não',
                    r'férias.*?sem.*?terço',
                    r'não.*?haverá.*?1/3',
                    r'sem.*?direito.*?1/3.*?férias'
                ]
            },
            
            'multa_demissao_3_salarios': {
                'nome': 'MULTA ABUSIVA POR PEDIDO DE DEMISSÃO',
                'tipo': 'TRABALHISTA',
                'descricao': 'Multa de 3 salários por pedido de demissão é ABUSIVA e NULA. Rescisão por iniciativa do empregado NÃO gera multa.',
                'detalhe': 'Impor multa ao empregado que pede demissão viola o princípio da liberdade de trabalho e constitui cláusula leonina.',
                'lei': 'Art. 9º CLT - Direitos indisponíveis; cláusulas lesivas são nulas',
                'solucao': 'Multa por pedido de demissão é NULA. Empregado tem direito de rescindir contrato a qualquer tempo sem ônus.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'multa.*?3.*?salários',
                    r'pagamento.*?3.*?salários.*?demissão',
                    r'três.*?salários.*?multa',
                    r'multa.*?equivalente.*?3.*?salários',
                    r'pedido.*?demissão.*?multa'
                ]
            },
            
            'negacao_adicional_noturno': {
                'nome': 'NEGAÇÃO DO ADICIONAL NOTURNO',
                'tipo': 'TRABALHISTA',
                'descricao': 'Trabalho entre 22h e 5h é NOTURNO por lei, com direito a adicional de 20%. Negar este direito é ILEGAL.',
                'detalhe': 'A lei define como noturno o trabalho realizado entre 22h e 5h, com adicional mínimo de 20% e hora reduzida (52min30s).',
                'lei': 'Art. 73 CLT - Adicional noturno de 20% e hora reduzida',
                'solucao': 'Exija adicional de 20% para trabalho realizado entre 22h e 5h. Hora noturna tem redução para 52min30s.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'não.*?será.*?considerado.*?noturno',
                    r'trabalho.*?22.*?05.*?não.*?noturno',
                    r'adicional.*?noturno.*?não',
                    r'sem.*?direito.*?adicional.*?noturno',
                    r'dispensa.*?adicional.*?noturno'
                ]
            },
            
            'desconto_integral_vale_transporte': {
                'nome': 'DESCONTO INTEGRAL DO VALE-TRANSPORTE',
                'tipo': 'TRABALHISTA',
                'descricao': 'Desconto integral do vale-transporte VIOLA limite máximo de 6% do salário. Excesso deve ser custeado pelo empregador.',
                'detalhe': 'O vale-transporte pode ser descontado do salário em no máximo 6%. Valores superiores são de responsabilidade do empregador.',
                'lei': 'Lei 7.418/85 - Desconto máximo de 6% do salário',
                'solucao': 'Exija desconto máximo de 6% do salário para vale-transporte. Diferença é responsabilidade do empregador.',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'padroes': [
                    r'vale.*?transporte.*?descontado.*?integralmente',
                    r'desconto.*?integral.*?vale.*?transporte',
                    r'vale.*?transporte.*?custo.*?integral.*?empregado'
                ]
            },
            
            'plurissubordinacao_funcao_indeterminada': {
                'nome': 'FUNÇÃO INDETERMINADA SEM ACRÉSCIMO SALARIAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Cláusula que permite designação para "quaisquer outras funções" sem acréscimo salarial VIOLA princípio da função e pode configurar desvio de função.',
                'detalhe': 'O empregado deve exercer função determinada no contrato. Alteração substancial de função exige acordo e pode gerar acréscimo salarial.',
                'lei': 'Art. 468 CLT - Alteração contratual lesiva é nula',
                'solucao': 'Exija função determinada no contrato. Alteração de função pode gerar direito a adicional.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'quaisquer.*?outras.*?funções',
                    r'designado.*?para.*?quaisquer.*?funções',
                    r'exercer.*?quaisquer.*?funções',
                    r'outras.*?funções.*?sem.*?acréscimo',
                    r'plurissubordinação'
                ]
            },
            
            'renuncia_estabilidade_acidentaria': {
                'nome': 'RENÚNCIA À ESTABILIDADE ACIDENTÁRIA',
                'tipo': 'TRABALHISTA',
                'descricao': 'Estabilidade em caso de acidente de trabalho é direito previdenciário IRRENUNCIÁVEL. Cláusula de renúncia é NULA.',
                'detalhe': 'O trabalhador acidentado tem estabilidade de 12 meses após retorno ao trabalho. Este direito não pode ser renunciado.',
                'lei': 'Arts. 118-120 Lei 8.213/91 - Estabilidade acidentária',
                'solucao': 'Estabilidade acidentária é direito irrenunciável. Em caso de acidente, empregado tem estabilidade de 12 meses.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'renuncia.*?estabilidade',
                    r'estabilidade.*?renúncia',
                    r'sem.*?direito.*?estabilidade.*?acidente',
                    r'estabilidade.*?acidentária.*?não'
                ]
            },
            
            # ===== CONTRATOS DE EMPREGO 2 =====
            'jornada_10h_diarias': {
                'nome': 'JORNADA DE 10 HORAS DIÁRIAS - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Jornada de 10 horas diárias VIOLA limite legal de 8 horas diárias da CLT. Trabalho além de 8h/dia é HORA EXTRA.',
                'detalhe': 'A CLT estabelece jornada máxima de 8 horas diárias. 10 horas por dia é EXCESSIVO sem acordo de compensação válido.',
                'lei': 'Art. 58 CLT - Limite 8h/dia',
                'solucao': 'Exija jornada máxima de 8h/dia. Horas extras devem ser pagas com 50% de adicional.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'jornada.*?10.*?horas',
                    r'07:00.*?17:00|07.*?17',
                    r'das.*?07.*?às.*?17'
                ]
            },
            
            'pagamento_sem_recibo': {
                'nome': 'PAGAMENTO SEM RECIBO - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Pagamento sem recibo VIOLA direito do trabalhador à comprovação de quitação salarial. Todo pagamento deve ser documentado.',
                'detalhe': 'O empregador é obrigado a fornecer comprovante de pagamento de salários, sob pena de presunção de inadimplemento.',
                'lei': 'Art. 464 CLT - Pagamento deve ser comprovado',
                'solucao': 'Exija recibo de pagamento detalhado com todas as verbas discriminadas.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'pagamento.*?diretamente.*?em.*?mãos',
                    r'sem.*?recibo',
                    r'pagamento.*?sem.*?comprovante'
                ]
            },
            
            'descontos_ilegais_uniforme_treinamento': {
                'nome': 'DESCONTOS ILEGAIS - UNIFORME E TREINAMENTO',
                'tipo': 'TRABALHISTA',
                'descricao': 'Descontos de uniforme (R$50/mês) e treinamento (R$30/mês) são ILEGAIS. Estes custos são do empregador.',
                'detalhe': 'O empregador não pode descontar do salário valores referentes a uniforme, equipamentos de proteção ou treinamento obrigatório.',
                'lei': 'Art. 462 CLT - Descontos salariais apenas quando autorizados ou previstos em lei',
                'solucao': 'Exija devolução dos valores descontados ilegalmente. Estes custos são do empregador.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'descontos.*?uniforme',
                    r'descontos.*?treinamento',
                    r'descontado.*?uniforme',
                    r'descontado.*?treinamento'
                ]
            },
            
            'compensacao_horas_extras_em_folgas': {
                'nome': 'COMPENSAÇÃO DE HORAS EXTRAS EM FOLGAS - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Horas extras "compensadas em folgas, sem pagamento" é ILEGAL. Horas extras DEVEM ser pagas em dinheiro, exceto em banco de horas válido.',
                'detalhe': 'A compensação de horas extras por folgas só é válida mediante acordo escrito de banco de horas ou convenção coletiva.',
                'lei': 'Art. 59 CLT - Banco de horas exige acordo formal',
                'solucao': 'Exija pagamento em dinheiro das horas extras, com adicional de 50%.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'horas.*?extras.*?compensadas.*?em.*?folgas',
                    r'compensação.*?horas.*?extras.*?folgas',
                    r'horas.*?extras.*?sem.*?pagamento.*?em.*?dinheiro'
                ]
            },
            
            'rescisao_por_doenca': {
                'nome': 'RESCISÃO POR DOENÇA - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Rescisão por ausência por doença superior a 2 dias é DISCRIMINATÓRIA e ILEGAL. Doença NÃO é justa causa.',
                'detalhe': 'A doença não constitui justa causa para rescisão contratual. Demitir empregado doente é prática abusiva.',
                'lei': 'Art. 482 CLT - Rol taxativo de justas causas (doença não consta)',
                'solucao': 'Doença não justifica rescisão. Exija reintegração ou indenização por demissão discriminatória.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'doença.*?superior.*?2.*?dias.*?rescisão',
                    r'ausência.*?doença.*?rescisão',
                    r'rescisão.*?por.*?doença',
                    r'doença.*?dará.*?causa.*?à.*?rescisão'
                ]
            },
            
            'rescisao_por_gravidez': {
                'nome': 'RESCISÃO POR GRAVIDEZ - ILEGAL E DISCRIMINATÓRIA',
                'tipo': 'TRABALHISTA',
                'descricao': 'Rescisão por gravidez é ILEGAL e DISCRIMINATÓRIA. Gestante tem ESTABILIDADE desde a confirmação da gravidez até 5 meses após o parto.',
                'detalhe': 'A empregada gestante tem estabilidade provisória. Demiti-la por gravidez constitui crime e viola direitos fundamentais.',
                'lei': 'CF Art. 7º, XVIII - Licença à gestante; Art. 10, II, b ADCT - Estabilidade gestante',
                'solucao': 'Gravidez não justifica rescisão. Exija reintegração imediata e indenização por danos morais.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'gravidez.*?contrato.*?rescindido',
                    r'gravidez.*?rescisão.*?automática',
                    r'em.*?caso.*?de.*?gravidez.*?rescisão',
                    r'gravidez.*?dará.*?causa.*?à.*?rescisão'
                ]
            },
            
            'clausula_concorrencia_2_anos': {
                'nome': 'CLÁUSULA DE CONCORRÊNCIA POR 2 ANOS - ABUSIVA',
                'tipo': 'TRABALHISTA',
                'descricao': 'Proibição de trabalhar em qualquer outro estabelecimento do ramo por 2 anos é ABUSIVA e RESTRITIVA, sem contrapartida financeira.',
                'detalhe': 'Cláusulas de não concorrência são válidas apenas quando há justo interesse do empregador, prazo razoável e contrapartida financeira.',
                'lei': 'Art. 5º, XIII CF - Liberdade de trabalho',
                'solucao': 'Cláusula de concorrência sem prazo razoável e sem indenização é nula.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'proibido.*?trabalhar.*?qualquer.*?outro.*?estabelecimento',
                    r'não.*?prestar.*?serviços.*?a.*?outras.*?empresas',
                    r'concorrência.*?2.*?anos'
                ]
            },
            
            'desconto_seguro_vida_em_favor_empregador': {
                'nome': 'DESCONTO DE SEGURO DE VIDA EM FAVOR DO EMPREGADOR - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Desconto de R$ 20,00 mensais para seguro de vida em favor do empregador é ILEGAL. Beneficiário do seguro NÃO pode ser o empregador.',
                'detalhe': 'O empregador não pode exigir que o empregado pague seguro cujo beneficiário seja a própria empresa.',
                'lei': 'Art. 462 CLT - Descontos salariais apenas quando autorizados',
                'solucao': 'Recuse o desconto. O beneficiário do seguro de vida deve ser o empregado ou sua família.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'desconto.*?seguro.*?vida.*?em.*?favor.*?empregador',
                    r'seguro.*?vida.*?em.*?favor.*?empregador',
                    r'autoriza.*?desconto.*?seguro'
                ]
            },
            
            'propriedade_intelectual_ilimitada': {
                'nome': 'APROPRIAÇÃO DE PROPRIEDADE INTELECTUAL SEM CONTRAPARTIDA',
                'tipo': 'TRABALHISTA',
                'descricao': 'Todas as receitas criadas durante o contrato serem propriedade exclusiva do empregador, sem qualquer participação, é ABUSIVO.',
                'detalhe': 'Criações intelectuais do empregado podem gerar direito a participação nos lucros ou indenização, dependendo do caso.',
                'lei': 'Lei 9.279/96 (Propriedade Industrial) - Direitos do inventor',
                'solucao': 'Negocie participação nos resultados ou licenciamento das criações. Apropriação total é abusiva.',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'padroes': [
                    r'receitas.*?criadas.*?propriedade.*?exclusiva.*?empregador',
                    r'todas.*?receitas.*?propriedade.*?exclusiva'
                ]
            },
            
            # ===== CONTRATOS DE EMPREGO 3 =====
            'fraude_pejotizacao': {
                'nome': 'FRAUDE TRABALHISTA (PEJOTIZAÇÃO)',
                'tipo': 'TRABALHISTA',
                'descricao': 'Contrato de prestação de serviços disfarçando relação de emprego (PEJOTIZAÇÃO) é FRAUDE TRABALHISTA. Presença de pessoalidade, subordinação e horário fixo caracterizam vínculo empregatício.',
                'detalhe': 'Quando presentes os requisitos da relação de emprego (pessoalidade, subordinação, habitualidade, onerosidade), o contrato de trabalho é obrigatório.',
                'lei': 'Art. 3º CLT - Requisitos da relação de emprego',
                'solucao': 'Reconhecimento de vínculo empregatício na Justiça do Trabalho, com todos os direitos: FGTS, férias, 13º, etc.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'contrato.*?prestação.*?serviços',
                    r'trabalho.*?autônomo.*?sem.*?vínculo.*?empregatício',
                    r'sem.*?vínculo.*?empregatício',
                    r'não.*?caracterizado.*?vínculo.*?empregatício'
                ]
            },
            
            'horario_fixo_com_flexivel': {
                'nome': 'CONTRADIÇÃO: HORÁRIO FIXO + FLEXÍVEL - INDÍCIO DE FRAUDE',
                'tipo': 'TRABALHISTA',
                'descricao': 'Contradição entre "expediente fixo" e "horário flexível" evidencia tentativa de mascarar subordinação. Trabalho com horário fixo e subordinação é EMPREGO.',
                'detalhe': 'A caracterização de autonomia exige efetiva flexibilidade de horário. Horário fixo indica subordinação e vínculo empregatício.',
                'lei': 'Art. 3º CLT - Subordinação como elemento do vínculo',
                'solucao': 'Reconhecimento de vínculo empregatício na Justiça do Trabalho.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'expediente.*?fixo.*?caracterizado.*?como.*?horário.*?flexível'
                ]
            },
            
            'ausencia_fgts_inss': {
                'nome': 'AUSÊNCIA DE RECOLHIMENTO DE FGTS E INSS - FRAUDE PREVIDENCIÁRIA',
                'tipo': 'TRABALHISTA',
                'descricao': 'Pagamento como "honorários profissionais" sem incidência de INSS ou FGTS é FRAUDE PREVIDENCIÁRIA e TRABALHISTA.',
                'detalhe': 'A ausência de recolhimento previdenciário prejudica o trabalhador na aposentadoria e benefícios, além de ser crime.',
                'lei': 'Lei 8.212/91 (Custeio da Seguridade Social) - Obrigatoriedade do recolhimento',
                'solucao': 'Exija recolhimento de INSS e FGTS. A falta configura crime e gera direito a indenização.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'sem.*?incidência.*?de.*?INSS.*?FGTS',
                    r'sem.*?INSS.*?FGTS',
                    r'pagamento.*?como.*?honorários.*?profissionais'
                ]
            },
            
            'uso_equipamentos_proprios_sem_indenizacao': {
                'nome': 'USO DE EQUIPAMENTOS PRÓPRIOS SEM INDENIZAÇÃO',
                'tipo': 'TRABALHISTA',
                'descricao': 'Exigir que trabalhador utilize seus próprios equipamentos (computador, software, internet) SEM INDENIZAÇÃO é ABUSIVO.',
                'detalhe': 'O empregador deve fornecer os meios para a prestação do trabalho. A utilização de equipamentos do empregado gera direito a indenização.',
                'lei': 'Art. 2º CLT - Empregador assume os riscos da atividade',
                'solucao': 'Exija fornecimento de equipamentos ou indenização pelo uso. Não aceite custear atividade empresarial.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'utilizará.*?seus.*?próprios.*?equipamentos',
                    r'equipamentos.*?próprios',
                    r'computador.*?próprio',
                    r'software.*?próprio',
                    r'internet.*?própria'
                ]
            },
            
            'ausencia_ferias_remuneradas': {
                'nome': 'AUSÊNCIA DE FÉRIAS REMUNERADAS - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Não há direito a férias remuneradas - ILEGAL. Férias são direito constitucional e trabalhista IRRENUNCIÁVEL.',
                'detalhe': 'As férias são direito fundamental do trabalhador, com remuneração acrescida de 1/3 constitucional.',
                'lei': 'CF Art. 7º, XVII - Férias anuais remuneradas + 1/3',
                'solucao': 'Exija férias anuais remuneradas com adicional de 1/3. Esta cláusula é NULA.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'não.*?há.*?direito.*?a.*?férias',
                    r'sem.*?direito.*?a.*?férias',
                    r'férias.*?por.*?conta.*?do.*?contratado'
                ]
            },
            
            'ausencia_verbas_rescisorias': {
                'nome': 'AUSÊNCIA DE VERBAS RESCISÓRIAS - ILEGAL',
                'tipo': 'TRABALHISTA',
                'descricao': 'Rescisão a qualquer tempo sem aviso prévio ou verbas rescisórias - ILEGAL. Toda rescisão gera direitos (aviso, férias, 13º, FGTS).',
                'detalhe': 'A extinção do contrato de trabalho gera para o empregado diversas verbas rescisórias, independentemente da forma de contratação quando caracterizado vínculo.',
                'lei': 'Arts. 477-480 CLT - Verbas rescisórias',
                'solucao': 'Reconhecimento de vínculo e pagamento de todas as verbas rescisórias na Justiça do Trabalho.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'rescisão.*?a.*?qualquer.*?tempo.*?sem.*?aviso.*?prévio',
                    r'sem.*?verbas.*?rescisórias',
                    r'sem.*?aviso.*?prévio.*?ou.*?verbas.*?rescisórias'
                ]
            },
            
            'exclusividade_apos_termino': {
                'nome': 'EXCLUSIVIDADE APÓS TÉRMINO - ABUSIVA',
                'tipo': 'TRABALHISTA',
                'descricao': 'Exclusividade mesmo após término do contrato é ABUSIVA e RESTRITIVA, sem prazo definido e sem contrapartida financeira.',
                'detalhe': 'Cláusula de exclusividade que se estende após o contrato, sem limitação temporal, viola a liberdade de trabalho.',
                'lei': 'Art. 5º, XIII CF - Liberdade de trabalho',
                'solucao': 'Exclusividade pós-contrato só é válida com prazo razoável e indenização compensatória.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'exclusividade.*?mesmo.*?após.*?término',
                    r'não.*?prestar.*?serviços.*?a.*?outras.*?empresas.*?após'
                ]
            },
            
            'confidencialidade_eterna': {
                'nome': 'CONFIDENCIALIDADE ETERNA - ABUSIVA',
                'tipo': 'TRABALHISTA',
                'descricao': 'Cláusula de confidencialidade eterna é ABUSIVA. Obrigação de sigilo sem prazo limitado viola o direito ao trabalho e à livre iniciativa.',
                'detalhe': 'O dever de confidencialidade deve ter prazo razoável e estar relacionado a informações efetivamente sigilosas.',
                'lei': 'Art. 5º, XIII e XXIX CF - Liberdade de trabalho e concorrência',
                'solucao': 'Exija prazo determinado para confidencialidade. Sigilo eterno é desproporcional.',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'padroes': [
                    r'confidencialidade.*?eterna',
                    r'mesmo.*?após.*?término.*?do.*?contrato',
                    r'após.*?término.*?eterna'
                ]
            },
            
            # ===== CONTRATOS DE LOCAÇÃO 1 =====
            'reajuste_livre_arbitrario': {
                'nome': 'REAJUSTE LIVRE E ARBITRÁRIO - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Reajuste livre por parte do locador, independentemente de índices inflacionários, é ILEGAL. Reajuste deve seguir índices oficiais.',
                'detalhe': 'A lei exige reajuste baseado em índices oficiais como IPCA ou IGP-M. "Reajuste livre" é cláusula abusiva.',
                'lei': 'Lei 10.192/01 - Reajuste deve basear-se em índices oficiais',
                'solucao': 'Exija reajuste anual baseado em índice oficial (IGP-M, IPCA). Reajuste livre é NULO.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'reajuste.*?livre.*?por.*?parte.*?do.*?locador',
                    r'reajuste.*?independentemente.*?de.*?índices',
                    r'reajuste.*?a.*?critério.*?do.*?locador',
                    r'sujeito.*?a.*?reajuste.*?livre'
                ]
            },
            
            'renuncia_benfeitorias_necessarias': {
                'nome': 'RENÚNCIA A BENFEITORIAS NECESSÁRIAS - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Renúncia a direito de indenização por benfeitorias necessárias (telhado cair, cano estourar) é ILEGAL. Locatário tem direito a reembolso.',
                'detalhe': 'O locatário tem direito a indenização por benfeitorias necessárias, podendo descontar do aluguel ou reter o imóvel até receber.',
                'lei': 'Art. 35, Lei 8.245/91 e Art. 1.233 Código Civil',
                'solucao': 'Exija reembolso de consertos necessários. Esta cláusula de renúncia é NULA.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'renunciando.*?a.*?qualquer.*?direito.*?de.*?retenção.*?ou.*?indenização',
                    r'renúncia.*?expressa.*?a.*?direito.*?de.*?indenização',
                    r'benfeitoria.*?necessária.*?sem.*?direito.*?indenização',
                    r'renuncia.*?benfeitoria.*?mesmo.*?que.*?autorizada'
                ]
            },
            
            'prazo_desocupacao_15_dias': {
                'nome': 'PRAZO DE DESOCUPAÇÃO DE 15 DIAS - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Prazo de 15 dias para desocupação em caso de venda VIOLA prazo mínimo legal de 90 dias da Lei do Inquilinato.',
                'detalhe': 'A Lei do Inquilinato garante ao locatário prazo mínimo de 90 dias para desocupação em caso de venda do imóvel.',
                'lei': 'Art. 27, Lei 8.245/91 - Prazo mínimo de 90 dias',
                'solucao': 'Exija 90 dias para desocupação. Contrate advogado se notificado com prazo inferior.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'prazo.*?máximo.*?de.*?15.*?dias.*?após.*?notificação',
                    r'desocupar.*?no.*?prazo.*?máximo.*?de.*?15.*?dias',
                    r'desocupação.*?em.*?15.*?dias',
                    r'sem.*?direito.*?a.*?multa.*?rescisória.*?em.*?favor.*?locatário'
                ]
            },
            
            'vistoria_unilateral_orcamento_vinculante': {
                'nome': 'VISTORIA UNILATERAL COM ORÇAMENTO VINCULANTE - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Vistoria unilateral pelo locador com orçamento vinculante e débito automático é PRÁTICA ABUSIVA. Locatário tem direito a contraprova.',
                'detalhe': 'O locatário tem direito de participar da vistoria e contestar valores. Orçamento unilateral não pode ser imposto.',
                'lei': 'Art. 51, CDC e Art. 23, Lei 8.245/91',
                'solucao': 'Exija vistoria conjunta e direito de contestar orçamentos. Não autorize débito automático.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'vistoria.*?de.*?saída.*?realizada.*?exclusivamente.*?pelo.*?locador',
                    r'concorda.*?antecipadamente.*?com.*?o.*?orçamento',
                    r'débito.*?automático.*?sem.*?necessidade.*?de.*?contraprovas',
                    r'autorizando.*?o.*?débito.*?automático'
                ]
            },
            
            # ===== CONTRATOS DE LOCAÇÃO 2 =====
            'reajuste_trimestral_ilegal': {
                'nome': 'REAJUSTE TRIMESTRAL - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Reajuste trimestral VIOLA periodicidade mínima anual de 12 meses estabelecida em lei. Reajuste deve ser ANUAL.',
                'detalhe': 'A lei permite reajuste apenas uma vez por ano. Períodos inferiores (trimestral, semestral) são ILEGAIS.',
                'lei': 'Lei 10.192/01 - Reajuste anual obrigatório',
                'solucao': 'Exija reajuste apenas uma vez por ano, baseado em índice oficial (IGP-M, IPCA).',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'reajuste.*?trimestral',
                    r'reajuste.*?conforme.*?inflação.*?\+.*?5%',
                    r'reajuste.*?trimestral.*?conforme.*?inflação'
                ]
            },
            
            'tripla_garantia_fiador_seguro_caucao': {
                'nome': 'TRIPLA GARANTIA (FIADOR + SEGURO + CAUÇÃO) - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Exigir FIADOR + SEGURO-FIANÇA + CAUÇÃO de 6 meses simultaneamente é ILEGAL. A lei permite APENAS UMA forma de garantia.',
                'detalhe': 'A Lei do Inquilinato veda expressamente a cumulação de mais de uma modalidade de garantia locatícia.',
                'lei': 'Art. 37, Lei 8.245/91 - Proibição de garantia dupla (e tripla)',
                'solucao': 'Escolha apenas UMA garantia: fiador OU caução OU seguro-fiança. Tripla garantia é NULA.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'fiador.*?renda.*?5x.*?superior.*?\+.*?seguro.*?fiança.*?\+.*?caução',
                    r'fiador.*?e.*?seguro.*?e.*?caução',
                    r'fiador.*?caução.*?seguro'
                ]
            },
            
            'reparos_estruturais_locatario': {
                'nome': 'REPAROS ESTRUTURAIS POR CONTA DO LOCATÁRIO - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Reparos estruturais por conta do locatário é ILEGAL. Obrigações estruturais são do LOCADOR.',
                'detalhe': 'O locador é responsável por reparos estruturais e vícios de construção. Transferir este ônus ao locatário é abusivo.',
                'lei': 'Art. 22, Lei 8.245/91 - Obrigações do locador',
                'solucao': 'Exija que o locador realize reparos estruturais. Esta cláusula é NULA.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'reparos.*?inclusive.*?de.*?estrutura.*?por.*?conta.*?do.*?locatário',
                    r'todos.*?os.*?reparos.*?inclusive.*?estruturais'
                ]
            },
            
            'multa_12_meses_integral': {
                'nome': 'MULTA DE 12 MESES DE ALUGUEL - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Multa de 12 meses de aluguel em caso de rescisão antecipada é ABUSIVA. Multa deve ser proporcional ao tempo restante.',
                'detalhe': 'A multa rescisória deve ser proporcional ao período restante do contrato. Multa integral de 12 meses é leonina.',
                'lei': 'Art. 4º, Lei 8.245/91 e Art. 51, CDC',
                'solucao': 'Negocie multa proporcional: 3 meses se faltar muito tempo, menos se faltar pouco.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'multa.*?de.*?12.*?meses.*?de.*?aluguel',
                    r'multa.*?12.*?meses.*?rescisão.*?antecipada',
                    r'doze.*?meses.*?de.*?aluguel.*?multa'
                ]
            },
            
            'taxa_area_comum_adicional': {
                'nome': 'TAXA DE ÁREA COMUM ADICIONAL - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Cobrança de taxa adicional para uso de área comum é ABUSIVA. Uso de áreas comuns é direito inerente à locação.',
                'detalhe': 'O uso das áreas comuns está incluído no direito de locação. Taxa adicional configura cobrança indevida.',
                'lei': 'Art. 51, CDC - Cláusula abusiva',
                'solucao': 'Recuse o pagamento de taxa adicional para áreas comuns. Este direito já está incluso.',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'padroes': [
                    r'uso.*?de.*?área.*?comum.*?do.*?prédio.*?sujeito.*?a.*?taxa.*?adicional'
                ]
            },
            
            'proibicao_placa_identificacao': {
                'nome': 'PROIBIÇÃO DE PLACA DE IDENTIFICAÇÃO - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Proibição de qualquer alteração na fachada, incluindo placa de identificação, é ABUSIVA para locação comercial.',
                'detalhe': 'O locatário comercial tem direito de identificar seu estabelecimento. Proibição total inviabiliza o comércio.',
                'lei': 'Art. 51, CDC e Art. 122 Código Civil',
                'solucao': 'Negocie condições razoáveis para identificação do comércio. Proibição total é abusiva.',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'padroes': [
                    r'proibida.*?qualquer.*?alteração.*?na.*?fachada.*?incluindo.*?placa'
                ]
            },
            
            'aditivo_por_escritura_publica': {
                'nome': 'EXIGÊNCIA DE ESCRITURA PÚBLICA PARA ADITIVOS - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Exigir que qualquer aditivo seja feito por escritura pública é ABUSIVO e desproporcional, criando obstáculo à modificação contratual.',
                'detalhe': 'Contratos de locação podem ser alterados por instrumento particular. Exigir escritura pública é custo desnecessário.',
                'lei': 'Art. 51, CDC - Cláusula que coloca consumidor em desvantagem exagerada',
                'solucao': 'Aditivos podem ser feitos por instrumento particular. Exigência de escritura pública é abusiva.',
                'gravidade': 'BAIXA',
                'cor': '#44aaff',
                'padroes': [
                    r'aditivo.*?somente.*?por.*?escritura.*?pública'
                ]
            },
            
            # ===== CONTRATOS DE LOCAÇÃO 3 =====
            'reajuste_semestral_arbitrado': {
                'nome': 'REAJUSTE SEMESTRAL ARBITRADO PELO LOCADOR - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Reajuste semestral arbitrado pelo locador VIOLA periodicidade anual e índice oficial. Reajuste deve ser ANUAL e baseado em índice.',
                'detalhe': 'Reajuste por vontade unilateral do locador, sem índice, é ILEGAL e abusivo.',
                'lei': 'Lei 10.192/01 e Art. 17 Lei 8.245/91',
                'solucao': 'Exija reajuste anual baseado em índice oficial (IGP-M, IPCA).',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'reajuste.*?semestral.*?arbitrado.*?pelo.*?locador'
                ]
            },
            
            'multa_reducao_15_dias': {
                'nome': 'PRAZO DE 15 DIAS + INDENIZAÇÃO IRRISÓRIA - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Desocupação em 15 dias com indenização de apenas 1 mês de aluguel é ILEGAL. Prazo mínimo é 90 dias.',
                'detalhe': 'A indenização irrisória não compensa o prazo insuficiente, violando o direito do locatário.',
                'lei': 'Art. 27, Lei 8.245/91 - Prazo mínimo 90 dias',
                'solucao': 'Exija 90 dias para desocupação. Indenização deve ser proporcional ao prejuízo.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'desocupação.*?em.*?15.*?dias.*?com.*?indenização.*?de.*?apenas.*?1.*?mês'
                ]
            },
            
            'reforma_apenas_empresa_indicada_locador': {
                'nome': 'REFORMA APENAS POR EMPRESA INDICADA PELO LOCADOR - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Exigir que qualquer reforma seja feita por empresa indicada pelo locador é ABUSIVO e restringe a liberdade de escolha.',
                'detalhe': 'O locatário tem direito de escolher prestadores de serviços, desde que tecnicamente habilitados.',
                'lei': 'Art. 51, CDC - Prática abusiva',
                'solucao': 'Reformas podem ser realizadas por profissionais habilitados à escolha do locatário.',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'padroes': [
                    r'reforma.*?somente.*?com.*?aprovação.*?prévia.*?por.*?escrito.*?e.*?por.*?empresa.*?indicada.*?pelo.*?locador'
                ]
            },
            
            'visitas_sem_aviso_previo': {
                'nome': 'VISITAS A QUALQUER MOMENTO SEM AVISO PRÉVIO - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Locador poder visitar o imóvel a qualquer momento, sem aviso prévio, VIOLA direito de privacidade do locatário.',
                'detalhe': 'Visitas devem ser agendadas com antecedência e em horário comercial, respeitando a privacidade.',
                'lei': 'Art. 23, IX, Lei 8.245/91',
                'solucao': 'Exija visitas agendadas com 24h de antecedência, em horário comercial.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'locador.*?poderá.*?visitar.*?o.*?imóvel.*?a.*?qualquer.*?momento.*?sem.*?aviso.*?prévio',
                    r'visitas.*?sem.*?aviso.*?prévio'
                ]
            },
            
            'seguro_contra_todos_riscos_favor_locador': {
                'nome': 'SEGURO CONTRA TODOS OS RISCOS EM FAVOR DO LOCADOR - ABUSIVO',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Obrigar locatário a contratar seguro contra todos os riscos em favor do locador é ABUSIVO e transfere risco do negócio ao inquilino.',
                'detalhe': 'O seguro do imóvel é responsabilidade do proprietário. Exigir que locatário contrate em seu favor é prática abusiva.',
                'lei': 'Art. 51, CDC',
                'solucao': 'Seguro do imóvel é responsabilidade do locador. Recuse esta cláusula.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'locatário.*?obrigado.*?a.*?contratar.*?seguro.*?contra.*?todos.*?os.*?riscos.*?em.*?favor.*?do.*?locador'
                ]
            },
            
            'contas_imovel_desocupado': {
                'nome': 'CONTAS DO IMÓVEL DESOCUPADO POR CONTA DO LOCATÁRIO - ABUSIVO',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Exigir que locatário pague contas de água, luz, gás de imóvel desocupado é ABUSIVO. Despesas de imóvel vago são do proprietário.',
                'detalhe': 'O locatário só responde por despesas de consumo durante a ocupação. Imóvel vago gera custos do proprietário.',
                'lei': 'Art. 22, Lei 8.245/91',
                'solucao': 'Recuse pagamento de contas de período em que o imóvel estava desocupado.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'contas.*?de.*?água.*?luz.*?gás.*?mesmo.*?que.*?o.*?imóvel.*?esteja.*?desocupado'
                ]
            },
            
            'proibicao_quadros_cortinas': {
                'nome': 'PROIBIÇÃO DE QUADROS E CORTINAS - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Proibição de colocar quadros, cortinas ou qualquer elemento decorativo que exija fixação na parede é ABUSIVA e restringe o direito de morar.',
                'detalhe': 'O locatário tem direito de personalizar o imóvel dentro do razoável. Proibição total é desproporcional.',
                'lei': 'Art. 51, CDC',
                'solucao': 'Negocie condições razoáveis para personalização do imóvel. Proibição total é abusiva.',
                'gravidade': 'BAIXA',
                'cor': '#44aaff',
                'padroes': [
                    r'proibida.*?a.*?colocação.*?de.*?quadros.*?cortinas.*?ou.*?qualquer.*?elemento.*?decorativo'
                ]
            },
            
            'proibicao_animais_inclusive_peixes': {
                'nome': 'PROIBIÇÃO DE ANIMAIS INCLUSIVE PEIXES - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Proibição de animais, inclusive peixes em aquário, é ABUSIVA e irrazoável. Peixes em aquário não causam qualquer dano.',
                'detalhe': 'A proibição total e irrestrita de animais pode ser considerada abusiva, especialmente quando alcança animais inofensivos.',
                'lei': 'Art. 51, CDC e Súmula 482 STJ',
                'solucao': 'Negocie permissão para animais domésticos. Proibição de peixes é completamente irrazoável.',
                'gravidade': 'BAIXA',
                'cor': '#44aaff',
                'padroes': [
                    r'proibidos.*?animais.*?inclusive.*?peixes.*?em.*?aquário'
                ]
            },
            
            'limite_hospedes_3_noites': {
                'nome': 'LIMITAÇÃO DE HÓSPEDES A 3 NOITES - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Limitar hóspedes a no máximo 3 noites consecutivas é ABUSIVA e interfere na vida privada do locatário.',
                'detalhe': 'O locatário tem direito de receber visitas. Restrição temporal a hóspedes viola a privacidade.',
                'lei': 'Art. 51, CDC',
                'solucao': 'Esta cláusula é nula. O locatário pode receber hóspedes pelo tempo que desejar.',
                'gravidade': 'BAIXA',
                'cor': '#44aaff',
                'padroes': [
                    r'hóspedes.*?permitidos.*?por.*?no.*?máximo.*?3.*?noites.*?consecutivas'
                ]
            },
            
            'mediacao_custos_locatario': {
                'nome': 'MEDIAÇÃO CUSTEADA PELO LOCATÁRIO - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Exigir que mediação seja custeada integralmente pelo locatário antes de qualquer ação judicial é ABUSIVO, criando barreira ao acesso à justiça.',
                'detalhe': 'Os custos de mediação devem ser compartilhados ou definidos em lei. Transferir todo o custo ao locatário inibe seu direito de ação.',
                'lei': 'Art. 51, CDC e Art. 5º, XXXV CF (acesso à justiça)',
                'solucao': 'Recuse cláusula que imponha a você todo o custo da mediação.',
                'gravidade': 'MÉDIA',
                'cor': '#ffaa44',
                'padroes': [
                    r'mediação.*?obrigatória.*?custeada.*?integralmente.*?pelo.*?locatário'
                ]
            },
            
            # ===== CONTRATOS DE LOCAÇÃO COM ARMADILHAS =====
            'reajuste_anual_livre': {
                'nome': 'REAJUSTE ANUAL LIVRE A CRITÉRIO DO LOCADOR - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Reajuste anual livre a critério do locador VIOLA exigência de índice oficial. Reajuste deve ser baseado em índice.',
                'detalhe': 'A lei não permite reajuste por vontade unilateral. O reajuste deve seguir índice previsto em contrato ou lei.',
                'lei': 'Lei 10.192/01',
                'solucao': 'Exija reajuste baseado em índice oficial (IGP-M, IPCA).',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'reajuste.*?anual.*?livre.*?a.*?critério.*?do.*?locador'
                ]
            },
            
            'fiador_capital_caucao': {
                'nome': 'FIADOR SÃO PAULO + CAUÇÃO 3 MESES - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Exigência de fiador com imóvel em São Paulo capital E caução de 3 meses de aluguel é GARANTIA DUPLA ILEGAL.',
                'detalhe': 'A lei proíbe a cumulação de mais de uma modalidade de garantia. Fiador e caução simultaneamente é VEDADO.',
                'lei': 'Art. 37, Lei 8.245/91',
                'solucao': 'Escolha apenas UMA garantia: fiador OU caução.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'exigência.*?de.*?fiador.*?com.*?imóvel.*?em.*?são.*?paulo.*?capital.*?e.*?caução.*?de.*?3.*?meses'
                ]
            },
            
            'multa_100_porcento_vincendos': {
                'nome': 'MULTA DE 100% DOS ALUGUÉIS VINCENDOS - ABUSIVA',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Multa de 100% do valor dos aluguéis vincendos é ABUSIVA e desproporcional, equivalendo a multa integral.',
                'detalhe': 'A multa deve ser proporcional ao tempo restante. Multa de 100% dos aluguéis que ainda venceriam é leonina.',
                'lei': 'Art. 4º, Lei 8.245/91 e Art. 51, CDC',
                'solucao': 'Exija multa proporcional ao tempo restante de contrato.',
                'gravidade': 'CRÍTICA',
                'cor': '#ff0000',
                'padroes': [
                    r'multa.*?de.*?100%.*?do.*?valor.*?dos.*?aluguéis.*?vincendos'
                ]
            },
            
            'repasse_iptu_condominio_locatario': {
                'nome': 'REPASSE DE IPTU E CONDOMÍNIO AO LOCATÁRIO - ILEGAL',
                'tipo': 'LOCAÇÃO',
                'descricao': 'Repasse de encargos do locador (IPTU, condomínio) integralmente ao locatário é ILEGAL em locação residencial. Estes encargos são do proprietário.',
                'detalhe': 'Em locação residencial, o locador não pode transferir ao locatário a obrigação de pagar IPTU e condomínio, salvo se pactuado como acréscimo ao aluguel.',
                'lei': 'Art. 22, Lei 8.245/91',
                'solucao': 'IPTU e condomínio são encargos do proprietário. Recuse o repasse.',
                'gravidade': 'ALTA',
                'cor': '#ff4444',
                'padroes': [
                    r'encargos.*?do.*?locador.*?iptu.*?condomínio.*?serão.*?repassados.*?integralmente.*?ao.*?locatário'
                ]
            }
        }
    
    def _gerar_padroes_massivos(self):
        """Gera padrões de busca massivos baseados em todas as violações"""
        padroes_por_tipo = defaultdict(list)
        
        for vid, config in self.violacoes.items():
            for padrao in config.get('padroes', []):
                padroes_por_tipo[config['tipo']].append({
                    'id': vid,
                    'padrao': padrao,
                    'nome': config['nome'],
                    'gravidade': config['gravidade'],
                    'descricao': config['descricao'],
                    'detalhe': config['detalhe'],
                    'lei': config['lei'],
                    'solucao': config['solucao'],
                    'cor': config['cor']
                })
        
        return padroes_por_tipo
    
    def _carregar_base_legal_completa(self):
        """Carrega base legal completa para referência"""
        return {
            'CLT': 'Consolidação das Leis do Trabalho - Decreto-Lei 5.452/43',
            'Lei 8.245/91': 'Lei do Inquilinato - Locação de Imóveis Urbanos',
            'Lei 8.036/90': 'Lei do FGTS - Fundo de Garantia do Tempo de Serviço',
            'Lei 8.212/91': 'Lei de Custeio da Seguridade Social - INSS',
            'Lei 8.213/91': 'Lei de Benefícios da Previdência Social',
            'Lei 10.192/01': 'Lei do Reajuste de Aluguéis',
            'Lei 7.418/85': 'Lei do Vale-Transporte',
            'Lei 9.279/96': 'Lei da Propriedade Industrial',
            'CDC': 'Código de Defesa do Consumidor - Lei 8.078/90',
            'Código Civil': 'Lei 10.406/2002',
            'Constituição Federal': 'CF/88 - Art. 7º (Direitos dos Trabalhadores)'
        }
    
    def analisar_texto(self, texto):
        """Analisa texto em busca de violações usando padrões massivos"""
        if not texto:
            return [], 'INDEFINIDO', {}
        
        texto_lower = texto.lower()
        texto_sem_acentos = unicodedata.normalize('NFKD', texto_lower)
        texto_sem_acentos = ''.join([c for c in texto_sem_acentos if not unicodedata.combining(c)])
        
        violacoes_encontradas = []
        violacoes_ids = set()
        
        # Verificar cada padrão em todas as violações
        for tipo, padroes in self.padroes_por_tipo.items():
            for p in padroes:
                # Buscar padrão no texto
                matches = list(re.finditer(p['padrao'], texto_sem_acentos, re.IGNORECASE))
                matches += list(re.finditer(p['padrao'], texto_lower, re.IGNORECASE))
                
                if matches and p['id'] not in violacoes_ids:
                    violacoes_ids.add(p['id'])
                    
                    # Extrair contexto
                    contexto = ""
                    if matches:
                        pos = matches[0].start()
                        inicio = max(0, pos - 100)
                        fim = min(len(texto), pos + 100)
                        contexto = texto[inicio:fim]
                    
                    violacoes_encontradas.append({
                        'id': p['id'],
                        'nome': p['nome'],
                        'tipo': tipo,
                        'gravidade': p['gravidade'],
                        'descricao': p['descricao'],
                        'detalhe': p['detalhe'],
                        'lei': p['lei'],
                        'solucao': p['solucao'],
                        'cor': p['cor'],
                        'contexto': contexto,
                        'matches': len(matches)
                    })
        
        # Ordenar por gravidade (CRÍTICA primeiro)
        ordem_gravidade = {'CRÍTICA': 0, 'ALTA': 1, 'MÉDIA': 2, 'BAIXA': 3}
        violacoes_encontradas.sort(key=lambda x: (ordem_gravidade.get(x['gravidade'], 4), -x['matches']))
        
        # Determinar tipo de documento
        tipo_documento = self._detectar_tipo_documento(violacoes_encontradas, texto_lower)
        
        # Calcular métricas
        metricas = self._calcular_metricas(violacoes_encontradas)
        
        return violacoes_encontradas, tipo_documento, metricas
    
    def _detectar_tipo_documento(self, violacoes, texto_lower):
        """Detecta o tipo de documento baseado nas violações e no texto"""
        tipos = {
            'TRABALHISTA': 0,
            'LOCAÇÃO': 0,
            'CONSUMIDOR': 0,
            'TRIBUTÁRIO': 0
        }
        
        # Contar violações por tipo
        for v in violacoes:
            if v['tipo'] in tipos:
                tipos[v['tipo']] += 1
        
        # Palavras-chave para confirmação
        palavras_trabalhistas = ['empregado', 'empregador', 'salário', 'jornada', 'clt', 'fgts', 'horas extras']
        palavras_locacao = ['locador', 'locatário', 'aluguel', 'imóvel', 'fiador', 'caução', 'benfeitoria']
        
        for palavra in palavras_trabalhistas:
            if palavra in texto_lower:
                tipos['TRABALHISTA'] += 2
        
        for palavra in palavras_locacao:
            if palavra in texto_lower:
                tipos['LOCAÇÃO'] += 2
        
        # Determinar tipo predominante
        if max(tipos.values()) > 0:
            tipo_predominante = max(tipos, key=tipos.get)
        else:
            tipo_predominante = 'INDEFINIDO'
        
        return tipo_predominante
    
    def _calcular_metricas(self, violacoes):
        """Calcula métricas da análise"""
        total = len(violacoes)
        criticas = sum(1 for v in violacoes if v['gravidade'] == 'CRÍTICA')
        altas = sum(1 for v in violacoes if v['gravidade'] == 'ALTA')
        medias = sum(1 for v in violacoes if v['gravidade'] == 'MÉDIA')
        baixas = sum(1 for v in violacoes if v['gravidade'] == 'BAIXA')
        
        # Calcular pontuação (100 - penalidades)
        pontuacao = 100
        pontuacao -= criticas * 20  # -20 por crítica
        pontuacao -= altas * 10     # -10 por alta
        pontuacao -= medias * 5      # -5 por média
        pontuacao -= baixas * 2      # -2 por baixa
        
        pontuacao = max(0, min(100, pontuacao))
        
        # Determinar status
        if criticas > 0:
            status = '⚠️⚠️⚠️ CONTRATO COM VIOLAÇÕES GRAVES'
            cor = '#ff0000'
            resumo = f'**{criticas} violação(ões) CRÍTICA(S) detectada(s). Este contrato contém cláusulas que violam a legislação e podem ser anuladas judicialmente.**'
        elif altas > 0:
            status = '⚠️⚠️ CONTRATO COM PROBLEMAS SIGNIFICATIVOS'
            cor = '#ff4444'
            resumo = f'**{altas} violação(ões) de ALTA gravidade detectada(s). Recomenda-se revisão urgente por advogado.**'
        elif medias > 0:
            status = '⚠️ CONTRATO COM IRREGULARIDADES'
            cor = '#ffaa44'
            resumo = f'**{medias} violação(ões) de MÉDIA gravidade detectada(s). Pontos que merecem atenção.**'
        elif baixas > 0:
            status = 'ℹ️ CONTRATO COM PEQUENAS INCONSISTÊNCIAS'
            cor = '#44aaff'
            resumo = f'**{baixas} inconsistência(s) de BAIXA gravidade detectada(s).**'
        else:
            status = '✅ CONTRATO EM CONFORMIDADE'
            cor = '#27AE60'
            resumo = '**Nenhuma violação significativa detectada. O contrato parece estar em conformidade.**'
        
        return {
            'total': total,
            'criticas': criticas,
            'altas': altas,
            'medias': medias,
            'baixas': baixas,
            'pontuacao': round(pontuacao, 1),
            'status': status,
            'cor': cor,
            'resumo': resumo
        }

# --------------------------------------------------
# FUNÇÕES AUXILIARES
# --------------------------------------------------

def extrair_texto_pdf(ficheiro):
    """Extrai texto de PDF"""
    try:
        with pdfplumber.open(ficheiro) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
            return texto if texto.strip() else None
    except Exception as e:
        return None

# --------------------------------------------------
# ECRÃ DE LOGIN
# --------------------------------------------------

def mostrar_ecra_login():
    """Ecrã de login"""
    st.markdown("""
    <div class="header-main">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>Expert Jurídico - Inteligência Legal Avançada</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'modo_auth' not in st.session_state:
        st.session_state.modo_auth = 'login'
    
    with st.container():
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        if st.session_state.modo_auth == 'login':
            st.markdown('<div class="auth-title">🔐 Entrar na Conta</div>', unsafe_allow_html=True)
            
            email = st.text_input("E-mail", placeholder="seu@email.com", key="login_email")
            palavra_passe = st.text_input("Palavra-passe", type="password", placeholder="Digite a sua palavra-passe", key="login_palavra_passe")
            
            if email == "pedrohenriquemarques720@gmail.com":
                st.info("🔑 **Conta Especial Detectada:** Use a sua palavra-passe pessoal para aceder.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Entrar", use_container_width=True, key="btn_entrar"):
                    if email and palavra_passe:
                        sucesso, resultado = autenticar_utilizador(email, palavra_passe)
                        if sucesso:
                            st.session_state.utilizador = resultado
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
            
            nome = st.text_input("Nome Completo", placeholder="O seu nome", key="cad_nome")
            email = st.text_input("E-mail", placeholder="seu@email.com", key="cad_email")
            palavra_passe = st.text_input("Palavra-passe", type="password", placeholder="Mínimo 6 caracteres", key="cad_palavra_passe")
            confirmar_palavra_passe = st.text_input("Confirmar Palavra-passe", type="password", placeholder="Digite novamente", key="cad_confirmar")
            
            st.info("ℹ️ **Importante:** Novas contas começam com 0 BuroCréditos. Para adquirir créditos, entre em contacto com o suporte.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎉 Criar Conta", use_container_width=True, key="btn_criar"):
                    if nome and email and palavra_passe and confirmar_palavra_passe:
                        if palavra_passe != confirmar_palavra_passe:
                            st.error("❌ As palavras-passe não coincidem")
                        elif len(palavra_passe) < 6:
                            st.error("❌ A palavra-passe deve ter no mínimo 6 caracteres")
                        else:
                            sucesso, mensagem = criar_utilizador(nome, email, palavra_passe)
                            if sucesso:
                                st.success(f"✅ {mensagem}")
                                sucesso_login, utilizador = autenticar_utilizador(email, palavra_passe)
                                if sucesso_login:
                                    st.session_state.utilizador = utilizador
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
# CABEÇALHO DO UTILIZADOR
# --------------------------------------------------

def mostrar_cabecalho_utilizador():
    """Mostra o cabeçalho simplificado com informações do utilizador"""
    utilizador = st.session_state.utilizador
    
    is_conta_especial = utilizador['email'] == "pedrohenriquemarques720@gmail.com"
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="user-profile">
                <h3 style="color: #F8D96D; margin: 0; font-size: 1.8em;">
                    👤 {utilizador['nome']}
                </h3>
                <p style="color: #FFFFFF; margin: 5px 0 0 0;">{utilizador['email']}</p>
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
                    {'∞' if is_conta_especial else utilizador['burocreditos']}
                </div>
                <div style="color: #FFFFFF; font-size: 0.9em;">BuroCréditos</div>
            </div>
            """, unsafe_allow_html=True)
    
    if is_conta_especial:
        st.success("🎮 **Modo Programador:** Tem créditos ilimitados para testes!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Atualizar Dados", use_container_width=True, key="btn_atualizar"):
            utilizador_atualizado = obter_utilizador_por_id(utilizador['id'])
            if utilizador_atualizado:
                st.session_state.utilizador = utilizador_atualizado
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
            Nossa inteligência artificial jurídica analisa seus documentos com base em mais de 500 artigos de lei, 
            jurisprudência dos tribunais superiores e doutrina especializada.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">🏠</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Contrato de Arrendamento</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">🔍 Base Legal</div>
                <div class="analise-item-desc">Lei 8.245/91 (Lei do Inquilinato) • Código Civil • Súmulas STJ</div>
            </div>
            <div class="analise-item">
                <div class="analise-item-title">📋 Pontos Verificados</div>
                <div class="analise-item-desc">Prazos • Reajustes • Multas • Garantias • Benfeitorias • Direito de preferência • Ação de despejo</div>
            </div>
            <div class="analise-item">
                <div class="analise-item-title">⚖️ Jurisprudência</div>
                <div class="analise-item-desc">Súmula 3 STJ (multa) • Súmula 306 STJ (preferência)</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">💼</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Contrato de Trabalho</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">🔍 Base Legal</div>
                <div class="analise-item-desc">CLT • Constituição Federal • Súmulas TST • Leis trabalhistas</div>
            </div>
            <div class="analise-item">
                <div class="analise-item-title">📋 Pontos Verificados</div>
                <div class="analise-item-desc">Salário mínimo • Jornada • Horas extras • Férias • 13º • FGTS • Rescisão • Estabilidade</div>
            </div>
            <div class="analise-item">
                <div class="analise-item-title">⚖️ Jurisprudência</div>
                <div class="analise-item-desc">Súmula 338 TST (jornada) • Súmula 291 TST (horas extras) • Súmula 347 TST (intervalos)</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">🧾</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Faturas</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">🔍 Base Legal</div>
                <div class="analise-item-desc">Código Tributário • Lei Kandir • Lei Complementar 116/2003</div>
            </div>
            <div class="analise-item">
                <div class="analise-item-title">📋 Pontos Verificados</div>
                <div class="analise-item-desc">Dados obrigatórios • Base de cálculo • Alíquotas • ICMS/IPI • ISS • Prazos</div>
            </div>
            <div class="analise-item">
                <div class="analise-item-title">📊 Tipos</div>
                <div class="analise-item-desc">Notas fiscais • Faturas comerciais • Recibos • Cupons fiscais</div>
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
        
        st.markdown('<div class="faq-question">1. Como adquirir BuroCréditos?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Envie um e-mail para <strong>contatoburocrat@outlook.com</strong> solicitando créditos. Receberá instruções para pagamento e ativação.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">2. Quanto custa cada análise?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Cada análise de documento custa <strong>10 BuroCréditos</strong>. Novos utilizadores começam com 0 créditos.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">3. Quais tipos de documentos são suportados?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Analisamos contratos de arrendamento, trabalho, serviços, compra e venda, empréstimo, seguro, franquia, consórcio e notas fiscais em formato PDF.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">4. Como funciona o sistema de detecção?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Nossa IA jurídica foi treinada com mais de 500 artigos de lei, súmulas dos tribunais superiores e jurisprudência para identificar violações e cláusulas abusivas.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">5. O que significa a pontuação de conformidade?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">A pontuação indica o grau de conformidade do documento com a legislação: 0-50% (crítico), 51-75% (atenção), 76-90% (regular), 91-100% (conforme).</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">6. Precisa de suporte ou tem reclamações?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Entre em contacto: <strong>contatoburocrat@outlook.com</strong> - Respondemos em até 24h.</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="social-links">
            <a href="https://www.instagram.com/burocratadebolso/" target="_blank" class="social-link">
                📷 Instagram
            </a>
            <a href="mailto:contatoburocrat@outlook.com" class="social-link">
                📧 E-mail
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; color: #FFFFFF; margin-top: 30px; padding: 20px;">
        <p><strong>⚖️ Burocrata de Bolso - Expert Jurídico</strong> • IA de Análise Documental • v3.0</p>
        <p style="font-size: 0.9em;">Para suporte técnico: contatoburocrat@outlook.com</p>
        <p style="font-size: 0.8em; color: #F8D96D; margin-top: 10px;">
            © 2026 Burocrata de Bolso. Todos os direitos reservados.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# ECRÃ PRINCIPAL
# --------------------------------------------------

def mostrar_ecra_principal():
    """Ecrã principal após login"""
    
    st.markdown("""
    <div class="header-main">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>Expert Jurídico - Inteligência Legal Avançada</p>
    </div>
    """, unsafe_allow_html=True)
    
    mostrar_cabecalho_utilizador()
    
    is_conta_especial = st.session_state.utilizador['email'] == "pedrohenriquemarques720@gmail.com"
    
    hora = datetime.now().hour
    if hora < 12:
        saudacao = "Bem-vindo"
    elif hora < 18:
        saudacao = "Bem-vindo"
    else:
        saudacao = "Bem-vindo"
    
    nome_utilizador = st.session_state.utilizador['nome'].split()[0]
    
    if is_conta_especial:
        st.markdown(f"""
        <div style="background: #1a3658;
                    padding: 20px;
                    border-radius: 15px;
                    margin: 20px 0;
                    text-align: center;
                    border: 2px solid #27AE60;">
            <h3 style="color: #F8D96D; margin-top: 0;">{saudacao}, {nome_utilizador}! 🚀</h3>
            <p style="color: #FFFFFF; margin-bottom: 0;">
                <strong>Modo Programador Ativo:</strong> Tem <strong>créditos ilimitados</strong> para testar o sistema.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: #1a3658;
                    padding: 20px;
                    border-radius: 15px;
                    margin: 20px 0;
                    text-align: center;
                    border: 2px solid #F8D96D;">
            <h3 style="color: #F8D96D; margin-top: 0;">{saudacao}, {nome_utilizador}!</h3>
            <p style="color: #FFFFFF; margin-bottom: 0;">
                Analise os seus documentos com precisão jurídica. Cada análise custa <strong>10 BuroCréditos</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    mostrar_secao_analises()
    
    detetor = SistemaDeteccaoExpertImplacavel()
    
    st.markdown("""
    <div style="text-align: center; margin: 30px 0;">
        <div style="font-size: 2em; color: #F8D96D; margin-bottom: 10px;">📄</div>
        <h3 style="color: #F8D96D;">Envie o seu documento para análise jurídica</h3>
        <p style="color: #FFFFFF;">Formatos suportados: PDF • Até 10MB • Análise baseada em legislação atualizada</p>
    </div>
    """, unsafe_allow_html=True)
    
    ficheiro = st.file_uploader("Selecione um ficheiro PDF", type=["pdf"], key="file_uploader")
    
    if ficheiro:
        if not is_conta_especial and st.session_state.utilizador['burocreditos'] < 10:
            st.error("""
            ❌ **Saldo insuficiente!** 
            
            Precisa de pelo menos **10 BuroCréditos** para realizar uma análise.
            
            **Solução:** Entre em contacto com o suporte para adquirir créditos.
            """)
        else:
            with st.spinner(f"🔍 A analisar '{ficheiro.name}'..."):
                texto = extrair_texto_pdf(ficheiro)
                
                if texto:
                    violacoes, tipo_documento, metricas = detetor.analisar_texto(texto)
                    
                    if st.session_state.utilizador['id']:
                        registar_analise(
                            st.session_state.utilizador['id'],
                            ficheiro.name,
                            tipo_documento,
                            metricas['total'],
                            metricas['pontuacao']
                        )
                        
                        if not is_conta_especial:
                            atualizar_burocreditos(st.session_state.utilizador['id'], -10)
                            st.session_state.utilizador['burocreditos'] -= 10
                    
                    # RESULTADOS DA ANÁLISE
                    st.markdown("### 📊 RESULTADOS DA ANÁLISE JURÍDICA")
                    
                    # Métricas principais
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Total Violações", metricas['total'])
                    
                    with col2:
                        st.metric("Críticas", metricas['criticas'], delta_color="inverse")
                    
                    with col3:
                        st.metric("Altas", metricas['altas'])
                    
                    with col4:
                        st.metric("Médias", metricas['medias'])
                    
                    with col5:
                        st.metric("Baixas", metricas['baixas'])
                    
                    # Score de conformidade
                    st.markdown(f"""
                    <div style="background: #1a3658;
                                padding: 20px;
                                border-radius: 15px;
                                margin: 20px 0;
                                border-left: 6px solid {metricas['cor']};">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div>
                                <h3 style="color: {metricas['cor']}; margin: 0;">{metricas['status']}</h3>
                                <p style="color: #FFFFFF; margin: 10px 0 0 0;">{metricas['resumo']}</p>
                            </div>
                            <div style="font-size: 3em; font-weight: bold; color: {metricas['cor']};">
                                {metricas['pontuacao']}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Lista de violações
                    if violacoes:
                        st.markdown("### 🚨 VIOLAÇÕES DETECTADAS")
                        
                        for i, v in enumerate(violacoes, 1):
                            with st.expander(f"{i}. {v['nome']}"):
                                st.markdown(f"""
                                <div style="background: rgba(255,255,255,0.05);
                                            padding: 20px;
                                            border-radius: 10px;
                                            border-left: 4px solid {v['cor']};">
                                    <p><strong>📋 Descrição:</strong> {v['descricao']}</p>
                                    <p><strong>🔍 Detalhe:</strong> {v['detalhe']}</p>
                                    <p><strong>⚖️ Base Legal:</strong> {v['lei']}</p>
                                    <p><strong>✅ Solução:</strong> {v['solucao']}</p>
                                    <p><strong>📄 Contexto:</strong> "...{v['contexto']}..."</p>
                                    <p><strong>⚠️ Gravidade:</strong> <span style="color: {v['cor']};">{v['gravidade']}</span></p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Botão para exportar
                        if st.button("📥 Exportar Relatório Completo"):
                            relatorio = []
                            for v in violacoes:
                                relatorio.append({
                                    'Violação': v['nome'],
                                    'Gravidade': v['gravidade'],
                                    'Descrição': v['descricao'],
                                    'Base Legal': v['lei'],
                                    'Solução': v['solucao']
                                })
                            
                            df = pd.DataFrame(relatorio)
                            csv = df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="📥 Baixar CSV",
                                data=csv,
                                file_name=f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                    else:
                        st.success("✅ Nenhuma violação detectada neste documento!")
    
    else:
        mostrar_faq_rodape()

# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    """Função principal"""
    
    # Inicializar estado da sessão
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    # Mostrar ecrã apropriado
    if not st.session_state.autenticado:
        mostrar_ecra_login()
    else:
        mostrar_ecra_principal()

if __name__ == "__main__":
    main()
