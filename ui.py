import streamlit as st
from detection import SistemaDetecção
from utils import extrair_texto_pdf

# Importar as funções de interface
from ui import (
    mostrar_tela_login, 
    mostrar_cabecalho_usuario, 
    mostrar_secao_analises, 
    mostrar_faq_rodape,
    mostrar_politica_privacidade_streamlit
)

# --------------------------------------------------
# TELA PRINCIPAL
# --------------------------------------------------

def mostrar_tela_principal():
    """Tela principal após login"""
    
    # Adicionar verificação de página
    if 'pagina' not in st.session_state:
        st.session_state.pagina = "principal"
    
    # Se não estiver na página principal, mostrar outra página
    if st.session_state.pagina != "principal":
        if st.session_state.pagina == "privacidade":
            mostrar_politica_privacidade_streamlit()
        return
    
    st.markdown("""
    <div class="header-main">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>IA de Análise Documental</p>
    </div>
    """, unsafe_allow_html=True)
    
    mostrar_cabecalho_usuario()
    
    is_conta_especial = st.session_state.usuario['email'] == "pedrohenriquemarques720@gmail.com"
    
    from datetime import datetime
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
        from database import atualizar_burocreds, registrar_analise
        is_conta_especial = st.session_state.usuario['email'] == "pedrohenriquemarques720@gmail.com"
        
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
                    
                    # ... (resto do código de análise) ...
                    
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
    from database import get_historico_usuario
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
    
    mostrar_faq_rodape()

# --------------------------------------------------
# FUNÇÃO MAIN()
# --------------------------------------------------

def main():
    """Função principal do app"""
    
    # Inicializar estado da sessão
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    if 'pagina' not in st.session_state:
        st.session_state.pagina = "login" if not st.session_state.autenticado else "principal"
    
    # Configuração da página
    st.set_page_config(
        page_title="Burocrata de Bolso",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # CSS customizado (coloque seu CSS aqui)
    st.markdown("""
    <style>
    /* CSS que você já tinha */
    .header-main { text-align: center; margin-bottom: 30px; }
    /* ... resto do CSS ... */
    </style>
    """, unsafe_allow_html=True)
    
    # Lógica de navegação baseada no estado
    if not st.session_state.autenticado:
        mostrar_tela_login()
    else:
        mostrar_tela_principal()

if __name__ == "__main__":
    main()
