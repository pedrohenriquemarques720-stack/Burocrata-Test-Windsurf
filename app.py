"""
Aplicação principal Burocrata de Bolso - Versão Modular
"""
import streamlit as st
import time
from datetime import datetime

# Importar módulos
from config import APP_CONFIG, USER_CONFIG, MESSAGES, is_special_account, DOMAIN_CONFIG
from database import (
    criar_usuario, autenticar_usuario, get_usuario_por_id, 
    atualizar_burocreds, registrar_analise, get_historico_usuario
)
from analysis import SistemaDetecção
from utils import extrair_texto_pdf, validar_email, obter_saudacao, calcular_score_cor
from ui import (
    mostrar_css_personalizado, mostrar_tela_login, mostrar_cabecalho_usuario,
    mostrar_secao_analises, mostrar_faq_rodape, mostrar_resultados_analise,
    mostrar_historico_analises
)

# Configuração da página
st.set_page_config(**APP_CONFIG)

# Aplicar CSS personalizado
mostrar_css_personalizado()

# Função para mostrar informações de domínio e deploy
def mostrar_informacoes_sistema():
    """Mostra informações do sistema e domínio"""
    dominio = DOMAIN_CONFIG['domain']
    app_streamlit = DOMAIN_CONFIG['streamlit_app']
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    ### 🌐 Informações do Sistema
    **Domínio Principal:** {dominio}
    **App Streamlit:** {app_streamlit}
    **Status:** 🟢 Produção
    """)
    
    # Links rápidos
    st.sidebar.markdown("### 🔗 Links Rápidos")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🌐 Site Principal", use_container_width=True, key="btn_site"):
            st.info(f"Abrindo {DOMAIN_CONFIG['production_url']}")
    
    with col2:
        if st.button("☁️ App Streamlit", use_container_width=True, key="btn_streamlit"):
            st.info(f"Abrindo {DOMAIN_CONFIG['streamlit_url']}")

def main():
    """Função principal do aplicativo"""
    
    # Mostrar informações do sistema na sidebar
    mostrar_informacoes_sistema()
    
    # Inicializar estado da sessão
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        mostrar_tela_login()
    else:
        mostrar_tela_principal()

def mostrar_tela_principal():
    """Tela principal após login"""
    
    # Cabeçalho principal
    st.markdown("""
    <div class="header-main">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>IA de Análise Documental</p>
    </div>
    """, unsafe_allow_html=True)
    
    mostrar_cabecalho_usuario()
    
    is_conta_especial = is_special_account(st.session_state.usuario['email'])
    saudacao = obter_saudacao()
    nome_usuario = st.session_state.usuario['nome'].split()[0]
    
    # Mensagem de boas-vindas
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
    
    # Sistema de análise
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
        if not is_conta_especial and st.session_state.usuario['burocreds'] < USER_CONFIG['analysis_cost']:
            st.error(f"""
            ❌ **Saldo insuficiente!** 
            
            Você precisa de pelo menos **{USER_CONFIG['analysis_cost']} BuroCreds** para realizar uma análise.
            
            **Solução:** Entre em contato com o suporte para adquirir créditos.
            """)
        else:
            with st.spinner(f"🔍 Analisando juridicamente '{arquivo.name}'..."):
                texto = extrair_texto_pdf(arquivo)
                
                if texto:
                    problemas, tipo_doc, metricas = detector.analisar_documento(texto)
                    
                    # Registrar análise no banco
                    if st.session_state.usuario['id']:
                        registrar_analise(
                            st.session_state.usuario['id'],
                            arquivo.name,
                            tipo_doc,
                            metricas['total'],
                            metricas['score']
                        )
                        
                        # Debitar créditos (exceto conta especial)
                        if not is_conta_especial:
                            atualizar_burocreds(st.session_state.usuario['id'], -USER_CONFIG['analysis_cost'])
                            st.session_state.usuario['burocreds'] -= USER_CONFIG['analysis_cost']
                    
                    # Mostrar resultados
                    mostrar_resultados_analise(arquivo.name, problemas, tipo_doc, metricas, detector)
                    
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
        mostrar_historico_analises(historico)
    
    # Informações sobre créditos (apenas para usuários normais)
    if not is_conta_especial:
        st.markdown("---")
        st.markdown(f"""
        <div style="background: #1a3658;
                    padding: 20px;
                    border-radius: 15px;
                    margin: 20px 0;
                    border: 2px solid #F8D96D;">
            <h4 style="color: #F8D96D; margin-top: 0;">💰 Sobre os BuroCreds</h4>
            <ul style="color: #FFFFFF; margin-bottom: 0;">
                <li>Cada análise custa <strong>{USER_CONFIG['analysis_cost']} BuroCreds</strong></li>
                <li>Para adquirir créditos: <strong>Veja vídeos ou nos chame em contatoburocrata@outlook.com</strong></li>
                <li>Plano PRO: Análises profundas + recursos avançados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    mostrar_faq_rodape()

if __name__ == "__main__":
    main()
