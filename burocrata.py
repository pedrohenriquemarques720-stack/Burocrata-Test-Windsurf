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
# SISTEMA DE DETECÇÃO EXPERT JURÍDICO
# --------------------------------------------------

class SistemaDeteccaoExpert:
    """Sistema de deteção de problemas em documentos com base na legislação real"""
    
    def __init__(self):
        self.leis_referencia = self._carregar_base_legal()
        self.padroes = self._gerar_padroes_completos()
        
    def _carregar_base_legal(self):
        """Carrega a base completa de leis e regulamentos"""
        return {
            # ===== CONSTITUIÇÃO FEDERAL =====
            'constituicao': {
                'artigos': {
                    '5': 'Direitos e garantias fundamentais',
                    '6': 'Direitos sociais',
                    '7': 'Direitos dos trabalhadores',
                }
            },
            
            # ===== CÓDIGO CIVIL =====
            'codigo_civil': {
                'arrendamento': {
                    'artigos': {
                        '565': 'Locação de coisas',
                        '566': 'Obrigações do locador',
                        '567': 'Obrigações do locatário',
                        '568': 'Vício redibitório',
                        '569': 'Benfeitorias necessárias',
                        '570': 'Benfeitorias úteis e voluptuárias',
                        '571': 'Direito de retenção por benfeitorias',
                        '572': 'Perda do direito de retenção',
                    }
                },
                'compra_venda': {
                    'artigos': {
                        '481': 'Compromisso de compra e venda',
                        '482': 'Prazo para arrependimento',
                        '483': 'Direito de preferência',
                        '484': 'Cláusula de irretratabilidade',
                        '485': 'Resolução por inadimplemento',
                    }
                }
            },
            
            # ===== CÓDIGO DE DEFESA DO CONSUMIDOR =====
            'codigo_defesa_consumidor': {
                'artigos': {
                    '39': 'Práticas abusivas',
                    '46': 'Direito à informação',
                    '47': 'Cláusulas abusivas',
                    '48': 'Contratos de adesão',
                    '49': 'Direito de arrependimento',
                    '50': 'Garantia contratual',
                    '51': 'Cláusulas abusivas (lista)',
                }
            },
            
            # ===== CÓDIGO DO TRABALHO (CLT) =====
            'clt': {
                'artigos': {
                    '58': 'Jornada de trabalho',
                    '59': 'Horas extras',
                    '60': 'Trabalho noturno',
                    '61': 'Banco de horas',
                    '62': 'Excludentes do controle de horário',
                    '63': 'Trabalho em regime de tempo parcial',
                    '64': 'Salário mínimo',
                    '65': 'Equiparação salarial',
                    '66': 'Intervalo intrajornada',
                    '67': 'Intervalo interjornada',
                    '68': 'Descanso semanal remunerado',
                    '129': 'Férias',
                    '130': 'Período aquisitivo',
                    '142': '13º salário',
                    '158': 'Fundo de Garantia (FGTS)',
                    '168': 'Seguro-desemprego',
                    '477': 'Rescisão contratual',
                    '478': 'Aviso prévio',
                    '479': 'Justa causa',
                    '480': 'Indenização',
                }
            },
            
            # ===== LEI DO INQUILINATO (Lei 8.245/91) =====
            'lei_inquilinato': {
                'artigos': {
                    '3': 'Locação residencial',
                    '4': 'Locação não residencial',
                    '5': 'Locação por temporada',
                    '6': 'Contrato verbal',
                    '7': 'Prazo da locação',
                    '8': 'Renovação compulsória',
                    '9': 'Denúncia vazia',
                    '10': 'Multa rescisória',
                    '11': 'Reajuste de aluguel',
                    '12': 'Índices de reajuste',
                    '13': 'Fiador',
                    '14': 'Caução',
                    '15': 'Seguro fiança',
                    '16': 'Cessão da locação',
                    '17': 'Sublocação',
                    '18': 'Benfeitorias',
                    '19': 'Obras urgentes',
                    '20': 'Direito de preferência',
                    '21': 'Ação de despejo',
                    '22': 'Consignação em pagamento',
                }
            },
            
            # ===== CÓDIGO TRIBUTÁRIO NACIONAL =====
            'codigo_tributario': {
                'notas_fiscais': {
                    'requisitos': [
                        'Identificação do emitente',
                        'Identificação do destinatário',
                        'Descrição dos produtos/serviços',
                        'Valor unitário',
                        'Quantidade',
                        'Base de cálculo',
                        'Alíquota do ICMS/IPI',
                        'Valor do imposto',
                        'Data de emissão',
                        'Número da nota fiscal',
                    ]
                }
            }
        }
    
    def _gerar_padroes_completos(self):
        """Gera padrões de detecção baseados em toda a legislação"""
        return {
            # ===== CONTRATO DE LOCAÇÃO/ARRENDAMENTO =====
            'CONTRATO_LOCACAO': {
                'nome': 'Contrato de Arrendamento',
                'descricao': 'Analisa contratos de aluguel residencial e comercial com base na Lei do Inquilinato',
                'padroes': [
                    # Prazo e vigência
                    r'prazo.*(inferior|menor).*30.*(dia|dias)',
                    r'vigência.*(inferior|menor).*12.*(mês|meses)',
                    r'renovação.*automática.*(não|não|sem)',
                    
                    # Reajuste abusivo
                    r'reajuste.*(anual|mensal).*(acima|superior).*(IGPM|IPCA)',
                    r'reajuste.*(livre|arbitrário|unilateral)',
                    r'índice.*(não|não).*especificado',
                    
                    # Multa rescisória
                    r'multa.*(acima|superior).*3.*(mês|meses)',
                    r'multa.*(acima|superior).*20.*%',
                    r'multa.*(proporcional|integral).*(não|não)',
                    
                    # Caução e garantias
                    r'caução.*(acima|superior).*3.*(mês|meses)',
                    r'fiador.*(não|não).*aceito',
                    r'garantia.*(adicional|extra).*(acima|superior)',
                    
                    # Obras e benfeitorias
                    r'obras.*(necessárias|urgentes).*locatário',
                    r'benfeitorias.*(não|não).*indenizadas',
                    r'reparações.*estruturais.*locatário',
                    
                    # Direito de preferência
                    r'direito.*preferência.*(não|não).*assegurado',
                    r'venda.*imóvel.*(sem|não).*comunicação',
                    
                    # Sublocação e cessão
                    r'sublocação.*(proibida|vedada).*(total|parcial)',
                    r'cessão.*(proibida|vedada).*(total|parcial)',
                    
                    # Ação de despejo
                    r'despejo.*(imediato|sumário).*(sem|não).*notificação',
                    r'desocupação.*prazo.*(inferior|menor).*30',
                    
                    # Juros e correção
                    r'juros.*(acima|superior).*1%.*mês',
                    r'correção.*monetária.*(não|não).*aplicada',
                    
                    # Cláusulas abusivas
                    r'(cláusula|condição).*abusiva',
                    r'(vantagem|benefício).*exclusiva.*locador',
                    r'(ônus|encargo).*exclusivo.*locatário',
                ],
                'jurisprudencia': [
                    'Súmula 3 do STJ: Nos contratos de locação, a multa rescisória não pode ser superior a 10% do valor do contrato',
                    'Súmula 306 do STJ: O direito de preferência do locatário deve ser respeitado em caso de venda do imóvel',
                ],
                'gravidade': 'ALTA'
            },
            
            # ===== CONTRATO DE TRABALHO =====
            'CONTRATO_TRABALHO': {
                'nome': 'Contrato de Trabalho',
                'descricao': 'Analisa contratos trabalhistas com base na CLT e legislação complementar',
                'padroes': [
                    # Salário
                    r'salário.*(abaixo|inferior).*mínimo',
                    r'salário.*(inferior|menor).*R?\$?\s*1.412',
                    r'(pagamento|remuneração).*(inferior|menor).*piso.*(categoria|profissional)',
                    
                    # Jornada
                    r'jornada.*(acima|superior).*8.*horas',
                    r'jornada.*(acima|superior).*44.*horas.*semana',
                    r'jornada.*12.*horas.*(sem|não).*descanso',
                    r'(trabalho|jornada).*(ininterrupta|ininterrupto).*(sem|não).*pausa',
                    
                    # Horas extras
                    r'horas.*extra.*(não|não).*remuneradas',
                    r'horas.*extra.*(incluídas|incorporadas).*salário',
                    r'banco.*horas.*(sem|não).*compensação',
                    r'(compensação|banco).*horas.*prazo.*(superior|acima).*6.*meses',
                    
                    # Trabalho noturno
                    r'trabalho.*noturno.*(sem|não).*adicional',
                    r'adicional.*noturno.*(inferior|menor).*20%',
                    r'hora.*noturna.*(superior|acima).*52.*minutos',
                    
                    # Intervalos
                    r'intervalo.*intrajornada.*(inferior|menor).*1.*hora',
                    r'intervalo.*interjornada.*(inferior|menor).*11.*horas',
                    r'descanso.*semanal.*(não|não).*remunerado',
                    
                    # Férias
                    r'férias.*(inferior|menor).*30.*dias',
                    r'férias.*(fracionadas|divididas).*(mais|acima).*2.*períodos',
                    r'férias.*(período|pagamento).*(após|depois).*12.*meses',
                    
                    # 13º salário
                    r'13º.*(não|não).*previsto',
                    r'(décimo|13º).*terceiro.*(não|não).*garantido',
                    
                    # FGTS
                    r'FGTS.*(não|não).*recolhido',
                    r'fundo.*garantia.*(não|não).*previsto',
                    
                    # Aviso prévio
                    r'aviso.*prévio.*(inferior|menor).*30.*dias',
                    r'aviso.*prévio.*(proporcional|tempo).*(não|não).*aplicado',
                    
                    # Rescisão
                    r'rescisão.*(sem|não).*justa.*causa.*(sem|não).*indenização',
                    r'justa.*causa.*(sem|não).*especificação',
                    r'(despedimento|demissão).*(sem|não).*aviso.*prévio',
                    
                    # Estabilidade
                    r'estabilidade.*(não|não).*respeitada',
                    r'gestante.*(sem|não).*estabilidade',
                    r'cipeiro.*(sem|não).*estabilidade',
                    
                    # Benefícios
                    r'vale.*transporte.*(não|não).*fornecido',
                    r'vale.*alimentação.*(não|não).*fornecido',
                    r'(auxílio|assistência).*médica.*(não|não).*prevista',
                    
                    # Confidencialidade
                    r'confidencialidade.*(ilimitada|perpétua)',
                    r'sigilo.*(após|depois).*término.*(sem|não).*limite',
                    
                    # Cláusulas abusivas
                    r'(cláusula|condição).*abusiva',
                    r'(penalidade|multa).*(superior|acima).*salário',
                    r'desconto.*(salarial|salário).*(não|não).*autorizado',
                ],
                'jurisprudencia': [
                    'Súmula 338 do TST: Jornada de trabalho deve ser registrada',
                    'Súmula 291 do TST: Horas extras habituais integram o salário',
                    'Súmula 347 do TST: Intervalo intrajornada não concedido gera pagamento integral',
                ],
                'gravidade': 'CRÍTICA'
            },
            
            # ===== CONTRATO DE COMPRA E VENDA =====
            'CONTRATO_COMPRA_VENDA': {
                'nome': 'Contrato de Compra e Venda',
                'descricao': 'Analisa contratos de compra e venda com base no Código Civil e CDC',
                'padroes': [
                    # Prazo de entrega
                    r'prazo.*entrega.*(indeterminado|não).*especificado',
                    r'entrega.*(acima|superior).*30.*dias.*(sem|não).*justificativa',
                    r'atraso.*entrega.*(sem|não).*multa',
                    
                    # Garantia
                    r'garantia.*(inferior|menor).*90.*dias',
                    r'garantia.*(não|não).*especificada',
                    r'exclusão.*garantia.*(abusiva|ilegal)',
                    
                    # Juros
                    r'juros.*(acima|superior).*1%.*mês',
                    r'juros.*(acima|superior).*12%.*ano',
                    r'multa.*mora.*(acima|superior).*2%',
                    
                    # Arrependimento
                    r'direito.*arrependimento.*(não|não).*assegurado',
                    r'arrependimento.*prazo.*(inferior|menor).*7.*dias',
                    
                    # Vícios
                    r'vício.*(produto|serviço).*(não|não).*coberto',
                    r'defeito.*(oculto|aparente).*(sem|não).*responsabilidade',
                    
                    # Rescisão
                    r'rescisão.*(unilateral|unilateral).*(sem|não).*motivo',
                    r'multa.*rescisória.*(acima|superior).*20%',
                    
                    # Preço e pagamento
                    r'reajuste.*(livre|arbitrário).*preço',
                    r'correção.*monetária.*(não|não).*especificada',
                    
                    # Cláusulas abusivas
                    r'(cláusula|condição).*abusiva',
                    r'(vantagem|benefício).*exclusiva.*vendedor',
                    r'(ônus|encargo).*exclusivo.*comprador',
                ],
                'jurisprudencia': [
                    'Art. 49 do CDC: Direito de arrependimento de 7 dias para compras fora do estabelecimento',
                    'Art. 26 do CDC: Prazo para reclamação de vícios aparentes',
                ],
                'gravidade': 'MÉDIA'
            },
            
            # ===== CONTRATO DE SERVIÇOS =====
            'CONTRATO_SERVICOS': {
                'nome': 'Contrato de Serviços',
                'descricao': 'Analisa contratos de prestação de serviços',
                'padroes': [
                    # Escopo
                    r'serviços.*(não|não).*especificados',
                    r'escopo.*(indeterminado|vago)',
                    
                    # Prazo
                    r'prazo.*execução.*(indeterminado|não).*especificado',
                    r'entrega.*(acima|superior).*30.*dias.*(sem|não).*justificativa',
                    
                    # Responsabilidade
                    r'responsabilidade.*(ilimitada|irrestrita)',
                    r'exclusão.*responsabilidade.*(abusiva|ilegal)',
                    
                    # Rescisão
                    r'rescisão.*(unilateral|unilateral).*(sem|não).*aviso',
                    r'multa.*rescisória.*(acima|superior).*20%',
                    
                    # Cláusulas abusivas
                    r'(cláusula|condição).*abusiva',
                ],
                'gravidade': 'MÉDIA'
            },
            
            # ===== FATURAS/NOTAS FISCAIS =====
            'NOTA_FISCAL': {
                'nome': 'Fatura/Nota Fiscal',
                'descricao': 'Analisa notas fiscais e faturas quanto à conformidade tributária',
                'padroes': [
                    # Dados obrigatórios
                    r'(nif|cpf|cnpj).*(não|não).*consta',
                    r'(endereço|morada).*(não|não).*consta',
                    
                    # Itens
                    r'itens.*(não|não).*especificados',
                    r'descrição.*(insuficiente|incompleta)',
                    
                    # Valores
                    r'valor.*unitário.*(não|não).*especificado',
                    r'quantidade.*(não|não).*especificada',
                    
                    # Impostos
                    r'(icms|ipi).*(não|não).*destacado',
                    r'base.*cálculo.*(não|não).*especificada',
                    r'alíquota.*(não|não).*especificada',
                    
                    # Totais
                    r'total.*(não|não).*coerente',
                    r'soma.*(incorreta|errada)',
                    
                    # Prazos
                    r'vencimento.*(não|não).*especificado',
                    r'juros.*mora.*(acima|superior).*1%.*mês',
                    
                    # Identificação
                    r'(emitente|destinatário).*(não|não).*identificado',
                ],
                'jurisprudencia': [
                    'Lei Complementar 116/2003: ISS',
                    'Lei Kandir: ICMS',
                ],
                'gravidade': 'MÉDIA'
            },
            
            # ===== CONTRATO DE EMPRÉSTIMO =====
            'CONTRATO_EMPRESTIMO': {
                'nome': 'Contrato de Empréstimo',
                'descricao': 'Analisa contratos de empréstimo e financiamento',
                'padroes': [
                    # Juros
                    r'juros.*(acima|superior).*12%.*ano',
                    r'juros.*(abusivos|extorsivos)',
                    r'capitalização.*juros.*(diária|mensal)',
                    
                    # CET
                    r'cet.*(não|não).*informado',
                    r'custo.*efetivo.*(não|não).*especificado',
                    
                    # Garantias
                    r'garantias.*(abusivas|excessivas)',
                    r'penhora.*(bem|salário).*(não|não).*permitido',
                    
                    # Cláusulas abusivas
                    r'(cláusula|condição).*abusiva',
                ],
                'gravidade': 'ALTA'
            },
            
            # ===== CONTRATO DE SEGURO =====
            'CONTRATO_SEGURO': {
                'nome': 'Contrato de Seguro',
                'descricao': 'Analisa contratos de seguro',
                'padroes': [
                    # Coberturas
                    r'coberturas.*(não|não).*especificadas',
                    r'exclusões.*(abusivas|amplas).*demais',
                    
                    # Prêmio
                    r'prêmio.*(não|não).*especificado',
                    r'reajuste.*(livre|arbitrário)',
                    
                    # Sinistro
                    r'prazo.*comunicação.*sinistro.*(inferior|menor).*24.*horas',
                    r'indenização.*(inferior|menor).*valor.*segurado',
                    
                    # Cláusulas abusivas
                    r'(cláusula|condição).*abusiva',
                ],
                'gravidade': 'MÉDIA'
            },
            
            # ===== CONTRATO DE FRANQUIA =====
            'CONTRATO_FRANQUIA': {
                'nome': 'Contrato de Franquia',
                'descricao': 'Analisa contratos de franquia (Lei 13.966/2019)',
                'padroes': [
                    # COF
                    r'cof.*(não|não).*entregue',
                    r'circular.*oferta.*franquia.*(não|não).*entregue',
                    
                    # Prazo
                    r'prazo.*(inferior|menor).*90.*dias.*cof',
                    r'prazo.*(inferior|menor).*10.*dias.*assinatura',
                    
                    # Royalties
                    r'royalties.*(não|não).*especificados',
                    r'taxa.*publicidade.*(não|não).*especificada',
                    
                    # Cláusulas abusivas
                    r'(cláusula|condição).*abusiva',
                ],
                'gravidade': 'ALTA'
            },
            
            # ===== CONTRATO DE CONSÓRCIO =====
            'CONTRATO_CONSORCIO': {
                'nome': 'Contrato de Consórcio',
                'descricao': 'Analisa contratos de consórcio',
                'padroes': [
                    # Taxas
                    r'taxa.*administração.*(não|não).*especificada',
                    r'fundo.*reserva.*(não|não).*especificado',
                    
                    # Contemplação
                    r'critérios.*contemplação.*(não|não).*especificados',
                    r'lances.*(não|não).*permitidos',
                    
                    # Desistência
                    r'desistência.*(não|não).*prevista',
                    r'restituição.*(inferior|menor).*80%',
                    
                    # Cláusulas abusivas
                    r'(cláusula|condição).*abusiva',
                ],
                'gravidade': 'MÉDIA'
            }
        }
    
    def analisar_documento(self, texto):
        """Analisa um documento em busca de problemas usando base legal completa"""
        if not texto or len(texto) < 50:
            return [], 'DESCONHECIDO', self._calcular_metricas([]), []
        
        texto_limpo = texto.lower()
        problemas = []
        tipo_doc = 'DESCONHECIDO'
        sugestoes_legais = []
        
        # Detetar tipo de documento (com maior precisão)
        scores_tipo = {}
        for doc_id, config in self.padroes.items():
            score = 0
            for padrao in config.get('padroes', []):
                if re.search(padrao, texto_limpo, re.IGNORECASE):
                    score += 1
            scores_tipo[doc_id] = score
        
        if scores_tipo:
            tipo_doc = max(scores_tipo, key=scores_tipo.get)
            if scores_tipo[tipo_doc] == 0:
                tipo_doc = 'DESCONHECIDO'
        
        # Analisar cada padrão
        for doc_id, config in self.padroes.items():
            # Se documento for desconhecido, analisa todos os padrões
            if tipo_doc == 'DESCONHECIDO' or doc_id == tipo_doc:
                for padrao in config.get('padroes', []):
                    matches = list(re.finditer(padrao, texto_limpo, re.IGNORECASE))
                    for match in matches:
                        # Contexto da violação
                        contexto_inicio = max(0, match.start() - 50)
                        contexto_fim = min(len(texto_limpo), match.end() + 50)
                        contexto = texto[contexto_inicio:contexto_fim]
                        
                        # Sugestão legal baseada no tipo de violação
                        sugestao = self._gerar_sugestao_legal(doc_id, padrao, match.group(0))
                        if sugestao:
                            sugestoes_legais.append(sugestao)
                        
                        problemas.append({
                            'tipo': config['nome'],
                            'descricao': f"⚠️ Violação detectada: '{match.group(0)[:100]}...'",
                            'contexto': f"...{contexto}...",
                            'gravidade': config['gravidade'],
                            'posicao': match.start(),
                            'padrao': padrao,
                            'sugestao_legal': sugestao
                        })
        
        # Remover duplicatas (mesmo tipo de problema)
        problemas_unicos = []
        vistos = set()
        for p in problemas:
            chave = f"{p['tipo']}_{p['descricao'][:50]}"
            if chave not in vistos:
                vistos.add(chave)
                problemas_unicos.append(p)
        
        metricas = self._calcular_metricas(problemas_unicos)
        
        return problemas_unicos, tipo_doc, metricas, sugestoes_legais
    
    def _gerar_sugestao_legal(self, doc_id, padrao, texto_encontrado):
        """Gera sugestões legais baseadas no tipo de violação"""
        sugestoes = {
            # Locação
            'multa.*acima.*3.*meses': 'A multa rescisória em contratos de locação não pode ser superior a 3 meses de aluguel (Lei 8.245/91, art. 4º)',
            'caução.*superior.*3.*meses': 'A caução em contratos de locação não pode exceder o equivalente a 3 meses de aluguel (Lei 8.245/91, art. 37)',
            'reajuste.*livre': 'O reajuste deve seguir índice previsto em lei (IGP-M, IPCA) e não pode ser arbitrário (Lei 8.245/91, art. 17)',
            
            # Trabalhista
            'salário.*abaixo.*mínimo': f'Salário abaixo do mínimo legal (atualmente R$ 1.412,00) - Art. 7º, IV da Constituição Federal e Lei 12.382/11',
            'jornada.*excessiva': 'Jornada de trabalho excede o limite constitucional de 8 horas diárias e 44 horas semanais - Art. 7º, XIII da CF',
            'horas.*extra.*não.*remuneradas': 'Horas extras devem ser remuneradas com adicional mínimo de 50% - Art. 7º, XVI da CF e Art. 59 da CLT',
            'férias.*inferior.*30.*dias': 'Período de férias inferior a 30 dias - Art. 7º, XVII da CF e Art. 130 da CLT',
            'intervalo.*intrajornada.*inferior': 'Intervalo intrajornada inferior ao mínimo legal - Art. 71 da CLT',
            
            # Consumidor
            'garantia.*inferior.*90.*dias': 'Prazo de garantia inferior ao mínimo legal de 90 dias para bens duráveis - Art. 26 do CDC',
            'juros.*acima.*1%.*mês': 'Juros acima do permitido por lei - Art. 591 do Código Civil c/c Lei de Usura',
            'direito.*arrependimento.*não': 'Direito de arrependimento não assegurado para compras fora do estabelecimento - Art. 49 do CDC',
            
            # Tributário
            'icms.*não.*destacado': 'ICMS deve ser destacado na nota fiscal - Lei Complementar 87/96 (Lei Kandir)',
            'base.*cálculo.*não': 'Base de cálculo do imposto não especificada - Código Tributário Nacional, art. 142',
        }
        
        for chave, sugestao in sugestoes.items():
            if re.search(chave, padrao, re.IGNORECASE):
                return sugestao
        
        return None
    
    def _calcular_metricas(self, problemas):
        """Calcula métricas baseadas nos problemas encontrados"""
        total = len(problemas)
        criticos = sum(1 for p in problemas if p.get('gravidade') == 'CRÍTICA')
        altos = sum(1 for p in problemas if p.get('gravidade') == 'ALTA')
        medios = sum(1 for p in problemas if p.get('gravidade') == 'MÉDIA')
        
        # Cálculo mais preciso da pontuação
        pontuacao_base = 100
        pontuacao_base -= criticos * 25  # -25 pontos por crítico
        pontuacao_base -= altos * 15     # -15 pontos por alto
        pontuacao_base -= medios * 8      # -8 pontos por médio
        
        pontuacao = max(0, min(100, pontuacao_base))
        
        # Status baseado na gravidade
        if criticos > 0:
            status = '⚠️⚠️⚠️ REQUER ATENÇÃO JURÍDICA IMEDIATA'
            cor = '#E74C3C'
            recomendacao = 'Consulte urgentemente um advogado especializado. Este documento apresenta violações graves que podem resultar em prejuízos significativos.'
        elif altos > 0:
            status = '⚠️⚠️ AJUSTES JURÍDICOS NECESSÁRIOS'
            cor = '#F39C12'
            recomendacao = 'Recomendamos revisão por um profissional de direito para corrigir as cláusulas identificadas.'
        elif medios > 0:
            status = '⚠️ REVISÃO RECOMENDADA'
            cor = '#F1C40F'
            recomendacao = 'O documento contém pontos que merecem atenção, embora não sejam críticos.'
        elif total > 0:
            status = '📋 PEQUENAS INCONSISTÊNCIAS'
            cor = '#3498DB'
            recomendacao = 'Existem pequenas questões que podem ser ajustadas para maior segurança jurídica.'
        else:
            status = '✅ DOCUMENTO EM CONFORMIDADE'
            cor = '#27AE60'
            recomendacao = 'Nenhuma violação significativa foi detectada. O documento parece estar em conformidade com a legislação aplicável.'
        
        return {
            'total': total,
            'criticos': criticos,
            'altos': altos,
            'medios': medios,
            'pontuacao': round(pontuacao, 1),
            'status': status,
            'cor': cor,
            'recomendacao': recomendacao
        }
    
    def obter_base_legal(self, tipo_doc):
        """Retorna a base legal consultada para o tipo de documento"""
        if tipo_doc in self.padroes:
            return {
                'leis': self.leis_referencia,
                'jurisprudencia': self.padroes[tipo_doc].get('jurisprudencia', []),
                'descricao': self.padroes[tipo_doc].get('descricao', '')
            }
        return None

# --------------------------------------------------
# FUNÇÕES AUXILIARES
# --------------------------------------------------

def extrair_texto_pdf(ficheiro):
    """Extrai texto de PDF"""
    try:
        with pdfplumber.open(ficheiro) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto += pagina.extract_text() + "\n"
            return texto if texto.strip() else None
    except:
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
    
    detetor = SistemaDeteccaoExpert()
    
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
                    problemas, tipo_doc, metricas, sugestoes = detetor.analisar_documento(texto)
                    
                    if st.session_state.utilizador['id']:
                        registar_analise(
                            st.session_state.utilizador['id'],
                            ficheiro.name,
                            tipo_doc,
                            metricas['total'],
                            metricas['pontuacao']
                        )
                        
                        if not is_conta_especial:
                            atualizar_burocreditos(st.session_state.utilizador['id'], -10)
                            st.session_state.utilizador['burocreditos'] -= 10
                    
                    st.markdown("### 📊 Resultados da Análise Jurídica")
                    
                    # Informações do documento
                    tipo_nome = detetor.padroes.get(tipo_doc, {}).get('nome', 'Documento não identificado')
                    tipo_descricao = detetor.padroes.get(tipo_doc, {}).get('descricao', '')
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div style="font-size: 2em; margin-right: 15px;">📋</div>
                            <div>
                                <h3 style="color: {metricas['cor']}; margin: 0;">{metricas['status']}</h3>
                                <p style="color: #FFFFFF; margin: 5px 0 0 0;">
                                    Documento: <strong>{ficheiro.name}</strong><br>
                                    Tipo identificado: <strong>{tipo_nome}</strong><br>
                                    <small>{tipo_descricao}</small>
                                </p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Métricas detalhadas
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Problemas Totais", metricas['total'])
                    
                    with col2:
                        st.metric("Críticos", metricas['criticos'], delta_color="inverse")
                    
                    with col3:
                        st.metric
