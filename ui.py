import streamlit as st
import time
from datetime import datetime
import pandas as pd
from database import autenticar_usuario, criar_usuario, get_usuario_por_id, atualizar_burocreds, registrar_analise, get_historico_usuario
from detection import Detector
from utils import limpar_texto, extrair_texto_pdf

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
        if st.session_state.modo_auth == 'login':
            st.markdown("""
            <div class="auth-card">
                <div class="auth-title">🔐 Entrar na Conta</div>
            </div>
            """, unsafe_allow_html=True)
            
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
            st.markdown("""
            <div class="auth-card">
                <div class="auth-title">📝 Criar Nova Conta</div>
            </div>
            """, unsafe_allow_html=True)
            
            nome = st.text_input("Nome Completo", placeholder="Seu nome", key="cad_nome")
            email = st.text_input("E-mail", placeholder="seu@email.com", key="cad_email")
            senha = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", key="cad_senha")
            confirmar_senha = st.text_input("Confirmar Senha", type="password", placeholder="Digite novamente", key="cad_confirmar")
            
            st.info("ℹ️ **Importante:** Novas contas começam com 0 BuroCreds. Para adquirir créditos, entre em contato com o suporte.")
            
            # Checkbox de consentimento da política de privacidade
            consentimento = st.checkbox("✅ Li e concordo com a [Política de Privacidade](privacidade.html) e autorizo o tratamento dos meus dados conforme descrito.", key="consentimento_privacidade")
            
            if not consentimento:
                st.warning("⚠️ É necessário aceitar a Política de Privacidade para criar uma conta.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎉 Criar Conta", use_container_width=True, key="btn_criar"):
                    if nome and email and senha and confirmar_senha:
                        if not consentimento:
                            st.error("❌ É necessário aceitar a Política de Privacidade para criar uma conta.")
                        elif senha != confirmar_senha:
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
                                    st.error(f"❌ Erro ao fazer login automático: {usuario}")
                            else:
                                st.error(f"❌ {mensagem}")
                    else:
                        st.warning("⚠️ Preencha todos os campos")
            
            with col2:
                if st.button("🔙 Voltar ao Login", use_container_width=True, key="btn_voltar"):
                    st.session_state.modo_auth = 'login'
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Links de política e termos
    st.markdown("""
    <div style="text-align: center; margin-top: 20px; margin-bottom: 10px;">
        <a href="privacidade.html" target="_blank" style="color: #F8D96D; text-decoration: none; margin: 0 10px; font-size: 0.9em;">
            🔒 Política de Privacidade
        </a>
        <span style="color: #a0aec0;">|</span>
        <a href="index.html" target="_blank" style="color: #F8D96D; text-decoration: none; margin: 0 10px; font-size: 0.9em;">
            🏠 Página Inicial
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    mostrar_faq_rodape()

# --------------------------------------------------
# CABEÇALHO DO USUÁRIO
# --------------------------------------------------

def mostrar_cabecalho_usuario():
    """Mostra o cabeçalho simplificado com informações do usuário"""
    usuario = st.session_state.usuario
    
    is_conta_especial = usuario['email'] == "pedrohenriquemarques720@gmail.com"
    
    st.markdown(f"""
    <div class="header-user">
        <div class="user-info">
            <h2>👋 Bem-vindo, {usuario['nome']}!</h2>
            <div class="user-stats">
                <span class="stat-badge">📧 {usuario['email']}</span>
                <span class="stat-badge">💎 {usuario['plano']}</span>
                <span class="stat-badge">🪙 {usuario['burocreds']} BuroCreds</span>
                {'<span class="stat-badge special">👑 CONTA ESPECIAL</span>' if is_conta_especial else ''}
            </div>
        </div>
        <div class="user-actions">
            <button onclick="window.location.reload()" class="btn-small">🔄 Atualizar</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
# SEÇÃO DE ANÁLISES
# --------------------------------------------------

def mostrar_secao_analises():
    """Mostra a seção de análise de documentos"""
    usuario = st.session_state.usuario
    is_conta_especial = usuario['email'] == "pedrohenriquemarques720@gmail.com"
    
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Upload de arquivo
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown('<h3>📄 Análise de Documentos</h3>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Faça upload do seu documento (PDF, DOC, DOCX, TXT)",
        type=['pdf', 'doc', 'docx', 'txt'],
        key="file_uploader"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
        
        # Botão de análise
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🔍 Analisar Documento", use_container_width=True, key="btn_analisar"):
                with st.spinner("🔍 Analisando documento..."):
                    try:
                        # Extrair texto do arquivo
                        if uploaded_file.type == 'pdf':
                            texto = extrair_texto_pdf(uploaded_file)
                        else:
                            texto = uploaded_file.read().decode('utf-8')
                        
                        # Limpar texto
                        texto_limpo = limpar_texto(texto)
                        
                        # Detectar tipo de documento
                        detector = Detector()
                        tipo_doc = detector.detectar_tipo_documento(texto_limpo)
                        
                        # Realizar análise
                        resultado = detector.analisar_documento(texto_limpo, tipo_doc)
                        
                        # Registrar análise
                        registrar_analise(
                            usuario['id'],
                            uploaded_file.name,
                            tipo_doc,
                            resultado['problemas'],
                            resultado['score']
                        )
                        
                        # Atualizar créditos (se não for conta especial)
                        if not is_conta_especial:
                            atualizar_burocreds(usuario['id'], -10)
                        
                        # Mostrar resultados
                        st.success("✅ Análise concluída com sucesso!")
                        mostrar_resultados_analise(resultado, uploaded_file.name, tipo_doc)
                        
                    except Exception as e:
                        st.error(f"❌ Erro na análise: {str(e)}")
        
        with col2:
            if not is_conta_especial:
                st.info(f"💰 **Custo:** 10 BuroCreds\n\nSeu saldo: {usuario['burocreds']} BuroCreds")
            else:
                st.success("👑 **CONTA ESPECIAL**\n\nAnálises gratuitas!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Histórico de análises
    historico = get_historico_usuario(usuario['id'])
    if historico:
        st.markdown('<div class="history-section">', unsafe_allow_html=True)
        st.markdown('<h3>📜 Histórico de Análises</h3>', unsafe_allow_html=True)
        
        for item in historico:
            score_cor = "#27AE60" if item['score'] >= 80 else "#F39C12" if item['score'] >= 60 else "#E74C3C"
            
            st.markdown(f"""
            <div style="background: #1a3658;
                      padding: 15px;
                      border-radius: 10px;
                      margin: 10px 0;
                      border: 1px solid #F8D96D;">
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
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# RESULTADOS DA ANÁLISE
# --------------------------------------------------

def mostrar_resultados_analise(resultado, nome_arquivo, tipo_documento):
    """Mostra os resultados da análise de forma detalhada"""
    
    st.markdown('<div class="results-section">', unsafe_allow_html=True)
    
    # Score geral
    score = resultado['score']
    score_cor = "#27AE60" if score >= 80 else "#F39C12" if score >= 60 else "#E74C3C"
    
    st.markdown(f"""
    <div class="score-card">
        <h3>📊 Score de Conformidade</h3>
        <div class="score-display">
            <div class="score-value" style="color: {score_cor}; font-size: 3em; font-weight: bold;">
                {score:.1f}%
            </div>
            <div class="score-label">
                {'Excelente' if score >= 80 else 'Regular' if score >= 60 else 'Precisa Melhorar'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Problemas detectados
    if resultado['problemas'] > 0:
        st.markdown('<div class="problems-section">', unsafe_allow_html=True)
        st.markdown('<h3>⚠️ Problemas Detectados</h3>', unsafe_allow_html=True)
        
        for problema in resultado['detalhes_problemas']:
            st.markdown(f"""
            <div class="problem-item">
                <div class="problem-title">{problema['titulo']}</div>
                <div class="problem-description">{problema['descricao']}</div>
                <div class="problem-severity">Gravidade: {problema['gravidade']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Recomendações
    if resultado['recomendacoes']:
        st.markdown('<div class="recommendations-section">', unsafe_allow_html=True)
        st.markdown('<h3>💡 Recomendações</h3>', unsafe_allow_html=True)
        
        for rec in resultado['recomendacoes']:
            st.markdown(f"""
            <div class="recommendation-item">
                <div class="recommendation-text">{rec}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# TELA PRINCIPAL
# --------------------------------------------------

def mostrar_tela_principal():
    """Tela principal do usuário logado"""
    mostrar_cabecalho_usuario()
    mostrar_secao_analises()

# --------------------------------------------------
# FAQ E RODAPÉ
# --------------------------------------------------

def mostrar_faq_rodape():
    """Mostra FAQ e rodapé"""
    st.markdown("""
    <div class="faq-section">
        <h3>📋 Perguntas Frequentes</h3>
        
        <div class="faq-item">
            <strong>1. Como funciona a análise?</strong><br>
            Nossa IA analisa seu documento em segundos, identificando cláusulas importantes e possíveis problemas.
        </div>
        
        <div class="faq-item">
            <strong>2. Meus documentos estão seguros?</strong><br>
            Sim! Usamos criptografia e armazenamento seguro local, em conformidade com a LGPD.
        </div>
        
        <div class="faq-item">
            <strong>3. Quais tipos de documentos?</strong><br>
            Analisamos contratos, notas fiscais, termos de serviço e outros documentos jurídicos.
        </div>
    </div>
    
    <div class="footer">
        <p>© 2026 Burocrata de Bolso - Todos os direitos reservados</p>
        <p>Criado por Pedro Graciano</p>
    </div>
    """, unsafe_allow_html=True)
