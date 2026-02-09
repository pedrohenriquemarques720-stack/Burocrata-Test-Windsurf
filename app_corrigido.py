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
    .stApp { background: #10263D !important; min-height: 100vh; }
    .header-main { text-align: center; padding: 30px 0; margin-bottom: 20px; }
    .header-main h1 { font-family: 'Arial Black', sans-serif; font-size: 3em; font-weight: 900; color: #F8D96D; letter-spacing: 1px; margin-bottom: 5px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    .header-main p { font-family: 'Georgia', serif; font-size: 1.2em; color: #FFFFFF; font-weight: 300; letter-spacing: 0.5px; }
    .auth-card { background: #1a3658; border-radius: 15px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 3px solid #F8D96D; max-width: 500px; margin: 0 auto; }
    .auth-title { color: #F8D96D; font-size: 2.2em; font-weight: 800; text-align: center; margin-bottom: 30px; }
    .user-profile { background: #1a3658; border-radius: 15px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 2px solid #F8D96D; margin-bottom: 30px; }
    .stTextInput > div > div > input { border-radius: 10px !important; border: 2px solid #F8D96D !important; padding: 12px 15px !important; font-size: 1em !important; background-color: #2a4a75 !important; color: white !important; }
    .stTextInput > div > div > input::placeholder { color: #a0aec0 !important; }
    .stTextInput > div > div > input:focus { border-color: #FFE87C !important; box-shadow: 0 0 0 3px rgba(248, 217, 109, 0.3) !important; }
    .stButton > button { background: linear-gradient(135deg, #F8D96D, #d4b747) !important; color: #10263D !important; border: none !important; padding: 15px 30px !important; border-radius: 10px !important; font-weight: 700 !important; font-size: 1.1em !important; transition: all 0.3s !important; width: 100% !important; }
    .stButton > button:hover { transform: translateY(-3px) !important; box-shadow: 0 10px 25px rgba(248, 217, 109, 0.4) !important; background: linear-gradient(135deg, #FFE87C, #F8D96D) !important; }
    .secondary-button { background: linear-gradient(135deg, #2a4a75, #1a3658) !important; color: #F8D96D !important; border: 2px solid #F8D96D !important; }
    .secondary-button:hover { background: linear-gradient(135deg, #3a5a85, #2a4a75) !important; color: #FFE87C !important; border-color: #FFE87C !important; }
    .faq-container { background: #1a3658; border-radius: 15px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 2px solid #F8D96D; margin: 20px 0; }
    .faq-question { color: #F8D96D; font-weight: 700; margin-bottom: 5px; font-size: 1.1em; }
    .faq-answer { color: #FFFFFF; margin-bottom: 15px; font-size: 1em; line-height: 1.5; }
    .social-links { display: flex; justify-content: center; gap: 20px; margin-top: 15px; }
    .social-link { display: flex; align-items: center; gap: 8px; color: #F8D96D; text-decoration: none; font-weight: 700; padding: 8px 15px; border-radius: 20px; border: 2px solid #F8D96D; background: #1a3658; transition: all 0.3s; }
    .social-link:hover { background: rgba(248, 217, 109, 0.1); transform: translateY(-2px); color: #FFE87C; border-color: #FFE87C; }
    .analise-card { background: #1a3658; border-radius: 15px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); border-top: 5px solid #F8D96D; height: 100%; transition: transform 0.3s; }
    .analise-card:hover { transform: translateY(-5px); box-shadow: 0 15px 40px rgba(0,0,0,0.4); }
    .analise-icon { font-size: 2.5em; margin-bottom: 15px; color: #F8D96D; }
    .analise-title { color: #F8D96D; font-size: 1.5em; font-weight: 700; margin-bottom: 20px; text-align: center; }
    .analise-item { margin-bottom: 15px; padding-left: 10px; border-left: 3px solid rgba(248, 217, 109, 0.5); }
    .analise-item-title { color: #FFFFFF; font-weight: 600; margin-bottom: 5px; font-size: 1.1em; }
    .analise-item-desc { color: #e2e8f0; font-size: 0.95em; line-height: 1.4; }
    .metric-card { background: #1a3658; border-radius: 15px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); border-left: 4px solid #F8D96D; }
    .stExpander { background: #1a3658; border: 1px solid #F8D96D; border-radius: 10px; }
    .stExpander > div > div { background: #1a3658 !important; }
    .stAlert { background: #2a4a75 !important; border: 1px solid #F8D96D !important; color: white !important; }
    [data-testid="stMetric"] { background: #1a3658; padding: 15px; border-radius: 10px; border: 1px solid #F8D96D; }
    [data-testid="stMetricLabel"] { color: #F8D96D !important; }
    [data-testid="stMetricValue"] { color: white !important; }
    [data-testid="stMetricDelta"] { color: white !important; }
    .stFileUploader > div > div { background: #1a3658 !important; border: 2px solid #F8D96D !important; border-radius: 10px !important; color: white !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; background-color: #1a3658; }
    .stTabs [data-baseweb="tab"] { background-color: #2a4a75; border-radius: 4px 4px 0 0; padding: 10px 16px; color: white; border: 1px solid #F8D96D; }
    .stTabs [aria-selected="true"] { background-color: #F8D96D !important; color: #10263D !important; font-weight: bold; }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #1a3658; }
    ::-webkit-scrollbar-thumb { background: #F8D96D; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #FFE87C; }
</style>
""", unsafe_allow_html=True)

# Sistema de detecção simplificado para evitar erros
class SistemaDetecção:
    def __init__(self):
        self.padroes = {
            'CONTRATO_LOCACAO': {
                'nome': 'Contrato de Locação',
                'padroes': [
                    {
                        'regex': r'multa.*12.*meses.*aluguel',
                        'descricao': '🚨 MULTA DE 12 MESES DE ALUGUEL - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Lei 8.245/1991, Art. 4º',
                        'detalhe': 'Multa máxima permitida é 2 meses de aluguel.'
                    }
                ]
            },
            'CONTRATO_TRABALHO': {
                'nome': 'Contrato de Trabalho',
                'padroes': [
                    {
                        'regex': r'salário.*R\$\s*900|R\$\s*800',
                        'descricao': '🚨 SALÁRIO ABAIXO DO MÍNIMO - ILEGAL!',
                        'gravidade': 'CRÍTICA',
                        'lei': 'Constituição Federal Art. 7º IV',
                        'detalhe': 'Salário mínimo atual é superior a R$ 1.400,00.'
                    }
                ]
            }
        }
    
    def detectar_tipo_documento(self, texto):
        if not texto:
            return 'DESCONHECIDO'
        
        texto_limpo = limpar_texto(texto).lower()
        
        if 'locação' in texto_limpo or 'aluguel' in texto_limpo:
            return 'CONTRATO_LOCACAO'
        elif 'empregador' in texto_limpo or 'empregado' in texto_limpo:
            return 'CONTRATO_TRABALHO'
        else:
            return 'DESCONHECIDO'
    
    def analisar_documento(self, texto):
        if not texto or len(texto) < 50:
            return [], 'DESCONHECIDO', self._calcular_metricas([])
        
        texto_limpo = limpar_texto(texto).lower()
        problemas = []
        tipo_doc = self.detectar_tipo_documento(texto_limpo)
        
        if tipo_doc in self.padroes:
            for padrao in self.padroes[tipo_doc]['padroes']:
                try:
                    if re.search(padrao['regex'], texto_limpo, re.IGNORECASE):
                        problemas.append({
                            'tipo': self.padroes[tipo_doc]['nome'],
                            'descricao': padrao['descricao'],
                            'detalhe': padrao['detalhe'],
                            'lei': padrao['lei'],
                            'gravidade': padrao['gravidade']
                        })
                except:
                    continue
        
        return problemas, tipo_doc, self._calcular_metricas(problemas)
    
    def _calcular_metricas(self, problemas):
        total = len(problemas)
        criticos = sum(1 for p in problemas if 'CRÍTICA' in p.get('gravidade', ''))
        
        score = 100
        score -= criticos * 40
        score = max(0, min(100, score))
        
        if criticos >= 1:
            status = '🚨 PROBLEMAS GRAVES DETECTADOS!'
            cor = '#FF0000'
            nivel_risco = 'ALTO RISCO'
        elif total > 0:
            status = '⚠️ PROBLEMAS DETECTADOS'
            cor = '#FFD700'
            nivel_risco = 'RISCO MODERADO'
        else:
            status = '✅ DOCUMENTO REGULAR'
            cor = '#27AE60'
            nivel_risco = 'BAIXO RISCO'
        
        return {
            'total': total,
            'criticos': criticos,
            'altos': 0,
            'medios': 0,
            'info': 0,
            'score': round(score, 1),
            'status': status,
            'cor': cor,
            'nivel_risco': nivel_risco
        }

def extrair_texto_pdf(arquivo):
    """Extração robusta de texto de PDF"""
    try:
        texto_total = ""
        
        with pdfplumber.open(arquivo) as pdf:
            for pagina in pdf.pages:
                try:
                    texto = pagina.extract_text()
                    if texto and len(texto.strip()) > 20:
                        texto_total += texto + "\n\n"
                except:
                    continue
        
        texto_limpo = limpar_texto(texto_total)
        
        if not texto_limpo or len(texto_limpo) < 50:
            st.error("❌ Não foi possível extrair texto suficiente do PDF")
            return None
            
        return texto_limpo
        
    except Exception as e:
        st.error(f"❌ Erro ao processar PDF: {str(e)}")
        return None

# Funções de interface simplificadas
def mostrar_tela_login():
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
                st.info("🔑 Conta Especial Detectada: Use sua senha pessoal para acessar.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Entrar", use_container_width=True, key="btn_entrar"):
                    if email and senha:
                        sucesso, resultado = autenticar_usuario(email, senha)
                        if sucesso:
                            st.session_state.usuario = resultado
                            st.session_state.autenticado = True
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
        
        st.markdown('</div>', unsafe_allow_html=True)

def mostrar_tela_principal():
    st.markdown("""
    <div class="header-main">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>IA de Análise Documental</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Informações do usuário
    usuario = st.session_state.usuario
    st.markdown(f"""
    <div class="user-profile">
        <h3 style="color: #F8D96D; margin: 0;">👤 {usuario['nome']}</h3>
        <p style="color: #FFFFFF;">{usuario['email']} • {usuario['burocreds']} BuroCreds</p>
    </div>
    """, unsafe_allow_html=True)
    
    detector = SistemaDetecção()
    
    st.markdown("### 📄 Envie seu documento para análise")
    arquivo = st.file_uploader("Selecione um arquivo PDF", type=["pdf"])
    
    if arquivo:
        with st.spinner("🔍 Analisando documento..."):
            texto = extrair_texto_pdf(arquivo)
            
            if texto:
                problemas, tipo_doc, metricas = detector.analisar_documento(texto)
                
                # Registrar análise
                if st.session_state.usuario['id']:
                    registrar_analise(
                        st.session_state.usuario['id'],
                        arquivo.name,
                        tipo_doc,
                        metricas['total'],
                        metricas['score']
                    )
                
                # Mostrar resultados
                st.markdown(f"### 📊 Resultados da Análise")
                st.markdown(f"**Status:** {metricas['status']}")
                st.markdown(f"**Score:** {metricas['score']}%")
                st.markdown(f"**Problemas:** {metricas['total']}")
                
                if problemas:
                    for problema in problemas:
                        st.markdown(f"**{problema['descricao']}**")
                        st.markdown(f"- {problema['detalhe']}")
                        st.markdown(f"- Base Legal: {problema['lei']}")
                        st.markdown("---")
                else:
                    st.success("✅ Nenhum problema jurídico detectado!")
    
    # Botão de sair
    if st.button("🚪 Sair", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Função principal
def main():
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        mostrar_tela_login()
    else:
        mostrar_tela_principal()

if __name__ == "__main__":
    main()
