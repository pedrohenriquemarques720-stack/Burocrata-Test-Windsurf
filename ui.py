"""
Módulo de interface do usuário do Burocrata de Bolso
"""
import streamlit as st
import time
from config import USER_CONFIG, MESSAGES, CONTACT_CONFIG, is_special_account
from database import autenticar_usuario, criar_usuario, get_usuario_por_id
from utils import validar_email, formatar_data, calcular_score_cor

def mostrar_css_personalizado():
    """Aplica CSS personalizado ao aplicativo"""
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

def mostrar_tela_login():
    """Tela de login e cadastro"""
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
            
            if email == USER_CONFIG['special_account']['email']:
                st.info(MESSAGES['info']['special_account'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Entrar", use_container_width=True, key="btn_entrar"):
                    if email and senha:
                        sucesso, resultado = autenticar_usuario(email, senha)
                        if sucesso:
                            st.session_state.usuario = resultado
                            st.session_state.autenticado = True
                            
                            if is_special_account(email):
                                st.success("✅ **Conta Especial:** Acesso concedido com créditos ilimitados!")
                            else:
                                st.success(MESSAGES['success']['login'])
                            
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(MESSAGES['error']['invalid_credentials'])
                    else:
                        st.warning(MESSAGES['warning']['fill_fields'])
            
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
            
            st.info(MESSAGES['info']['new_account_info'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎉 Criar Conta", use_container_width=True, key="btn_criar"):
                    if nome and email and senha and confirmar_senha:
                        if not validar_email(email):
                            st.error("❌ E-mail inválido")
                        elif senha != confirmar_senha:
                            st.error(MESSAGES['warning']['password_mismatch'])
                        elif len(senha) < 6:
                            st.error(MESSAGES['warning']['password_length'])
                        else:
                            sucesso, mensagem = criar_usuario(nome, email, senha)
                            if sucesso:
                                st.success(mensagem)
                                sucesso_login, usuario = autenticar_usuario(email, senha)
                                if sucesso_login:
                                    st.session_state.usuario = usuario
                                    st.session_state.autenticado = True
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.error(mensagem)
                    else:
                        st.warning(MESSAGES['warning']['fill_fields'])
            
            with col2:
                if st.button("🔙 Voltar ao Login", use_container_width=True, key="btn_voltar"):
                    st.session_state.modo_auth = 'login'
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    mostrar_faq_rodape()

def mostrar_cabecalho_usuario():
    """Mostra o cabeçalho com informações do usuário"""
    usuario = st.session_state.usuario
    is_conta_especial = is_special_account(usuario['email'])
    
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

def mostrar_secao_analises():
    """Mostra seção com tipos de documentos analisados"""
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
    
    # Contrato de Locação
    with col1:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">🏠</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Contrato de Locação</div>', unsafe_allow_html=True)
            
            itens = [
                ("Valor do Aluguel e Reajuste", "Onde dói no bolso (ou entra o dinheiro)."),
                ("Vigência e Prazo", "Quanto tempo dura o \"felizes para sempre\"."),
                ("Conservação e Reformas", "Quem paga pelo cano que estourou."),
                ("Multas e Rescisão", "O preço de sair antes da hora."),
                ("Garantia Locatória", "O famoso fiador, caução ou seguro.")
            ]
            
            for titulo, desc in itens:
                st.markdown(f"""
                <div class="analise-item">
                    <div class="analise-item-title">{titulo}</div>
                    <div class="analise-item-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Contrato de Trabalho
    with col2:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">💼</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Contrato de Emprego</div>', unsafe_allow_html=True)
            
            itens = [
                ("Remuneração e Benefícios", "Salário, VR, VT e os mimos."),
                ("Jornada de Trabalho", "O horário de bater o ponto."),
                ("Atribuições do Cargo", "O que, afinal, você foi contratado para fazer."),
                ("Confidencialidade", "O que acontece na empresa, morre na empresa."),
                ("Aviso Prévio e Rescisão", "As regras do adeus.")
            ]
            
            for titulo, desc in itens:
                st.markdown(f"""
                <div class="analise-item">
                    <div class="analise-item-title">{titulo}</div>
                    <div class="analise-item-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Notas Fiscais
    with col3:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">🧾</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Notas Fiscais</div>', unsafe_allow_html=True)
            
            itens = [
                ("Dados do Emissor/Destinatário", "Quem vendeu e quem comprou."),
                ("Itens e Serviços", "A lista de compras detalhada."),
                ("Impostos e Tributação", "A fatia que fica para o governo."),
                ("Valor Total e Descontos", "O número final da conta."),
                ("Status de Pagamento", "Se já caiu na conta ou se ainda é promessa.")
            ]
            
            for titulo, desc in itens:
                st.markdown(f"""
                <div class="analise-item">
                    <div class="analise-item-title">{titulo}</div>
                    <div class="analise-item-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 40px 0;'></div>", unsafe_allow_html=True)

def mostrar_resultados_analise(nome_arquivo, problemas, tipo_doc, metricas, detector):
    """Mostra resultados detalhados da análise"""
    st.markdown("### 📊 Resultados da Análise Jurídica")
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <div style="font-size: 2em; margin-right: 15px;">⚖️</div>
            <div>
                <h3 style="color: {metricas['cor']}; margin: 0;">{metricas['status']}</h3>
                <p style="color: #FFFFFF; margin: 5px 0 0 0;">
                    <strong>Documento:</strong> {nome_arquivo}
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
        is_conta_especial = is_special_account(st.session_state.usuario['email'])
        if is_conta_especial:
            st.metric("BuroCreds Restantes", "∞")
        else:
            st.metric("BuroCreds Restantes", st.session_state.usuario['burocreds'], delta=-USER_CONFIG['analysis_cost'])
    
    # Detalhes dos problemas detectados
    if problemas:
        st.markdown("### ⚖️ Problemas Jurídicos Detectados")
        
        # Agrupar por gravidade
        problemas_criticos = [p for p in problemas if p['gravidade'] == 'CRÍTICA']
        problemas_altos = [p for p in problemas if p['gravidade'] == 'ALTA']
        problemas_medios = [p for p in problemas if p['gravidade'] == 'MÉDIA']
        
        # Mostrar problemas por gravidade
        if problemas_criticos:
            st.markdown("#### 🔴 Problemas Críticos (Requerem Atenção Imediata)")
            for problema in problemas_criticos:
                mostrar_problema_card(problema, "#E74C3C", "🔴")
        
        if problemas_altos:
            st.markdown("#### 🟠 Problemas Altos (Ajustes Necessários)")
            for problema in problemas_altos:
                mostrar_problema_card(problema, "#F39C12", "🟠")
        
        if problemas_medios:
            st.markdown("#### 🟡 Problemas Médios (Revisão Recomendada)")
            for problema in problemas_medios:
                mostrar_problema_card(problema, "#F1C40F", "🟡")
        
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

def mostrar_problema_card(problema, cor, icone):
    """Mostra card de problema individual"""
    st.markdown(f"""
    <div style="background: rgba(231, 76, 60, 0.15) if '{cor}' == '#E74C3C' else rgba(243, 156, 18, 0.15) if '{cor}' == '#F39C12' else rgba(241, 196, 15, 0.15);
              border-left: 4px solid {cor};
              padding: 20px;
              border-radius: 10px;
              margin: 10px 0;
              box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
        <div style="display: flex; align-items: flex-start;">
            <div style="font-size: 1.5em; margin-right: 15px; color: {cor};">{icone}</div>
            <div style="flex: 1;">
                <h4 style="margin: 0 0 8px 0; color: {cor};">
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

def mostrar_historico_analises(historico):
    """Mostra histórico de análises do usuário"""
    with st.expander("📜 Histórico de Análises (Últimas 5)", expanded=False):
        for item in historico:
            score_cor = calcular_score_cor(item['score'])
            
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
                            {formatar_data(item['data'])}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def mostrar_faq_rodape():
    """Mostra seção de FAQ e rodapé"""
    st.markdown("---")
    
    with st.container():
        st.markdown('<div class="faq-container">', unsafe_allow_html=True)
        
        st.markdown('<h3 style="color: #F8D96D; text-align: center; margin-bottom: 20px;">❓ Perguntas Frequentes</h3>', unsafe_allow_html=True)
        
        faq_items = [
            ("1. Como adquirir BuroCreds?", "Assista a videos<strong>ou nos contate pelo contatoburocrata@outlook.com</strong> solicitando créditos. Você receberá instruções para pagamento e ativação."),
            ("2. Quanto custa cada análise?", "Cada análise de documento custa <strong>10 BuroCreds</strong>."),
            ("3. Posso analisar vários documentos de uma vez?", "Atualmente, o sistema analisa um documento por vez. Cada análise consome 10 BuroCreds."),
            ("4. Quais tipos de documentos são suportados?", "Analisamos contratos de locação, emprego, serviços e compra e venda em formato PDF."),
            ("5. Como funciona o Plano PRO?", "O Plano PRO oferece análises profundas e recursos avançados. Entre em contato para mais informações."),
            ("6. Precisa de suporte ou tem reclamações?", "Entre em contato: <strong>contatoburocrata@outlook.com</strong> - Respondemos em até 24h.")
        ]
        
        for pergunta, resposta in faq_items:
            st.markdown(f'<div class="faq-question">{pergunta}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="faq-answer">{resposta}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Links sociais
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="social-links">
            <a href="{CONTACT_CONFIG['instagram']}" target="_blank" class="social-link">
                📷 Instagram
            </a>
            <a href="mailto:{CONTACT_CONFIG['email']}" class="social-link">
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
