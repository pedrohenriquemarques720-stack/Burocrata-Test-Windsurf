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

# Import modules
from database import init_database, criar_usuario, autenticar_usuario, get_usuario_por_id, atualizar_burocreds, registrar_analise, get_historico_usuario
from detection import SistemaDetecção
from utils import limpar_texto, extrair_texto_pdf
from ui import mostrar_tela_login, mostrar_cabecalho_usuario, mostrar_secao_analises, mostrar_faq_rodape, mostrar_tela_principal

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
# APLICATIVO PRINCIPAL
# --------------------------------------------------

def main():
    """Função principal do aplicativo"""
    
    # Inicializar banco de dados
    init_database()
    
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        mostrar_tela_login()
    else:
        mostrar_tela_principal()

if __name__ == "__main__":
    main()
