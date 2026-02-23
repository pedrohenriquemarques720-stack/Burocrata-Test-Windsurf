import streamlit as st
import pdfplumber
import re
import unicodedata
from datetime import datetime
import pandas as pd
import sqlite3
import hashlib
import time
from typing import Dict, List, Tuple, Any
import json

# IMPORTAR o Core Engine Jurídico do arquivo separado
from core_juridico import CoreEngineJuridico

# --------------------------------------------------
# CONFIGURAÇÃO DO MODO ESPECIALISTA
# --------------------------------------------------
st.set_page_config(
    page_title="⚖️ BUROCRATA DE BOLSO - MODO ESPECIALISTA JURÍDICO",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# FUNÇÕES AUXILIARES
# --------------------------------------------------

def extrair_texto_pdf(arquivo):
    """Extrai texto de PDF com tratamento robusto"""
    try:
        with pdfplumber.open(arquivo) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
            return texto if texto.strip() else None
    except Exception as e:
        st.error(f"❌ Erro ao processar PDF: {str(e)}")
        return None

# --------------------------------------------------
# INTERFACE PRINCIPAL DO MODO ESPECIALISTA
# --------------------------------------------------

def main():
    # Configurar estilo profissional
    st.markdown("""
    <style>
        .stApp {
            background: #0a0f1e;
        }
        .main-header {
            background: linear-gradient(135deg, #0a1a2f, #1a2a3f);
            padding: 20px;
            border-radius: 10px;
            border-bottom: 3px solid #F8D96D;
            margin-bottom: 20px;
            text-align: center;
        }
        .main-header h1 {
            color: #F8D96D;
            font-size: 2.5em;
            font-weight: 900;
            font-family: 'Courier New', monospace;
            margin: 0;
        }
        .main-header p {
            color: #FFFFFF;
            font-size: 1.1em;
            font-family: 'Courier New', monospace;
        }
        .veredito-card {
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: center;
            font-size: 1.5em;
            font-weight: bold;
        }
        .violacao-card {
            background: #1a2a3f;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 5px solid;
        }
        .metric-card {
            background: #1a2a3f;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #F8D96D;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Cabeçalho do Modo Especialista
    st.markdown("""
    <div class="main-header">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>MODO ESPECIALISTA JURÍDICO • DETECÇÃO EXTREMA DE RISCOS</p>
        <p style="color: #F8D96D; font-size: 0.9em;">"Nenhuma violação passará despercebida"</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar detector
    detector = CoreEngineJuridico()
    
    # Upload de arquivo
    arquivo = st.file_uploader(
        "📄 ENVIE O DOCUMENTO PARA AUDITORIA JURÍDICA COMPLETA",
        type=['pdf'],
        help="Formatos suportados: PDF. Análise de todas as vulnerabilidades contratuais e fiscais."
    )
    
    if arquivo:
        with st.spinner("🔍 MODO ESPECIALISTA ATIVADO - Escaneando estruturas jurídicas..."):
            texto = extrair_texto_pdf(arquivo)
            
            if texto:
                # Análise completa
                resultado = detector.analisar_documento_completo(texto)
                
                # Métricas principais
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: #F8D96D; margin:0;">{resultado['metricas']['total']}</h3>
                        <p>Violações Totais</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: #ff0000; margin:0;">{resultado['metricas']['criticas']}</h3>
                        <p>Críticas</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    cor_pontuacao = '#27AE60' if resultado['metricas']['pontuacao'] >= 70 else '#ffaa44' if resultado['metricas']['pontuacao'] >= 40 else '#ff0000'
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: {cor_pontuacao}; margin:0;">{resultado['metricas']['pontuacao']}%</h3>
                        <p>Conformidade</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    cor_veredito = {
                        'APROVADO': '#27AE60',
                        'REVISÃO OBRIGATÓRIA': '#ffaa44',
                        'REJEITADO': '#ff0000'
                    }.get(resultado['veredito'], '#ffaa44')
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: {cor_veredito}; margin:0;">{resultado['exposicao_risco']}%</h3>
                        <p>Exposição a Risco</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Veredito
                st.markdown(f"""
                <div class="veredito-card" style="background: {cor_veredito}20; border: 2px solid {cor_veredito};">
                    <h2 style="color: {cor_veredito}; margin:0;">🎯 VEREDITO: {resultado['veredito']}</h2>
                    <p style="color: #FFFFFF; margin-top:10px;">Tipo de Documento: {resultado['tipo_documento']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Recomendações
                if resultado['recomendacoes']:
                    st.markdown("### ⚠️ RECOMENDAÇÕES URGENTES")
                    for rec in resultado['recomendacoes']:
                        st.warning(rec)
                
                # Violações detectadas
                if resultado['violacoes']:
                    st.markdown("### 🚨 VIOLAÇÕES JURÍDICAS DETECTADAS")
                    
                    for i, v in enumerate(resultado['violacoes'], 1):
                        with st.expander(f"{i}. [{v.get('tipo', 'GERAL')}] {v['nome']}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**📋 Descrição:** {v['descricao']}")
                                st.markdown(f"**⚖️ Lei:** {v['lei']}")
                                if 'penalidade' in v:
                                    st.markdown(f"**⚠️ Penalidade:** {v['penalidade']}")
                                if 'jurisprudencia' in v:
                                    st.markdown(f"**📚 Jurisprudência:** {v['jurisprudencia']}")
                                st.markdown(f"**✅ Solução:** {v['solucao']}")
                                st.markdown(f"**📄 Contexto:** \"{v.get('contexto', 'N/A')}\"")
                            
                            with col2:
                                cor_gravidade = v.get('cor', '#ffaa44')
                                st.markdown(f"""
                                <div style="background: {cor_gravidade}20; padding:10px; border-radius:5px; text-align:center;">
                                    <h4 style="color: {cor_gravidade}; margin:0;">{v.get('gravidade', 'MÉDIA')}</h4>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.success("✅ NENHUMA VIOLAÇÃO DETECTADA - DOCUMENTO EM CONFORMIDADE PLENA")
                
                # Relatório completo
                st.markdown("---")
                if st.button("📥 GERAR RELATÓRIO COMPLETO (JSON)"):
                    relatorio = {
                        'data_analise': datetime.now().isoformat(),
                        'documento': arquivo.name,
                        'tipo': resultado['tipo_documento'],
                        'metricas': resultado['metricas'],
                        'exposicao_risco': resultado['exposicao_risco'],
                        'veredito': resultado['veredito'],
                        'recomendacoes': resultado['recomendacoes'],
                        'violacoes': [
                            {
                                'nome': v['nome'],
                                'tipo': v.get('tipo', 'GERAL'),
                                'gravidade': v.get('gravidade', 'MÉDIA'),
                                'descricao': v['descricao'],
                                'lei': v['lei'],
                                'solucao': v['solucao']
                            } for v in resultado['violacoes']
                        ]
                    }
                    
                    st.json(relatorio)
                    
                    # Botão para download
                    st.download_button(
                        label="📥 BAIXAR RELATÓRIO JSON",
                        data=json.dumps(relatorio, indent=2, ensure_ascii=False),
                        file_name=f"relatorio_juridico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
    
    else:
        # Instruções do Modo Especialista
        st.info("""
        ### 🔍 MODO ESPECIALISTA JURÍDICO ATIVADO
        
        **Protocolo de Análise:**
        1. **Parsing de Ambiguidade** - Identificação de termos vagos
        2. **Cross-Reference Legislativo** - Comparação com CLT, Lei do Inquilinato, CDC
        3. **Detecção de Cláusulas Leoninas** - Desequilíbrios contratuais
        4. **Shadow Analysis** - Identificação de omissões críticas
        
        **Envie um PDF para iniciar a auditoria completa.**
        """)

if __name__ == "__main__":
    main()
