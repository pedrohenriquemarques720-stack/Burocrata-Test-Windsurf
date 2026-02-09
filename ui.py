import streamlit as st
import time
from datetime import datetime
from detection import SistemaDetecção
from database import autenticar_usuario, criar_usuario, get_usuario_por_id, atualizar_burocreds, registrar_analise, get_historico_usuario
from utils import extrair_texto_pdf

# --------------------------------------------------
# TELA DE POLÍTICA DE PRIVACIDADE (DENTRO DO STREAMLIT)
# --------------------------------------------------

def mostrar_politica_privacidade_streamlit():
    """Exibe a política de privacidade dentro do app Streamlit"""
    
    st.markdown("""
    <div class="header-main">
        <h1>🔒 Política de Privacidade</h1>
        <p>Burocrata de Bolso - Plataforma de IA para Análise Documental Jurídica</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="background: rgba(26, 54, 88, 0.9); padding: 25px; border-radius: 15px; border: 2px solid #F8D96D; margin-bottom: 30px;">
        <h3 style="color: #F8D96D; margin-top: 0;">🛡️ Nosso Compromisso com a Sua Privacidade</h3>
        <p style="color: #FFFFFF;">
            Na <strong>Burocrata de Bolso</strong>, estamos comprometidos em proteger sua privacidade e garantir 
            a segurança dos seus dados pessoais. Esta Política de Privacidade estabelece como coletamos, 
            utilizamos, armazenamos, compartilhamos e protegemos suas informações, em conformidade com a 
            Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018) e o Regulamento Geral de Proteção de Dados (GDPR).
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Informações principais
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: rgba(26, 54, 88, 0.7); padding: 20px; border-radius: 10px; margin-bottom: 15px; height: 100%;">
            <h4 style="color: #F8D96D;">📋 Dados que Coletamos</h4>
            <ul style="color: #FFFFFF; padding-left: 20px;">
                <li>Nome e e-mail para cadastro</li>
                <li>Documentos enviados para análise</li>
                <li>Histórico de uso da plataforma</li>
                <li>Dados técnicos e de conexão</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: rgba(26, 54, 88, 0.7); padding: 20px; border-radius: 10px; margin-bottom: 15px; height: 100%;">
            <h4 style="color: #F8D96D;">🔐 Medidas de Segurança</h4>
            <ul style="color: #FFFFFF; padding-left: 20px;">
                <li>Criptografia AES-256</li>
                <li>Proteção TLS 1.3</li>
                <li>Hash de senhas com bcrypt</li>
                <li>Monitoramento 24/7</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: rgba(26, 54, 88, 0.7); padding: 20px; border-radius: 10px; margin-bottom: 15px; height: 100%;">
            <h4 style="color: #F8D96D;">👤 Seus Direitos (LGPD)</h4>
            <ul style="color: #FFFFFF; padding-left: 20px;">
                <li>Acesso aos seus dados</li>
                <li>Correção de informações</li>
                <li>Eliminação de dados</li>
                <li>Portabilidade de dados</li>
                <li>Revogação de consentimento</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: rgba(26, 54, 88, 0.7); padding: 20px; border-radius: 10px; margin-bottom: 15px; height: 100%;">
            <h4 style="color: #F8D96D;">⚠️ Compartilhamento de Dados</h4>
            <ul style="color: #FFFFFF; padding-left: 20px;">
                <li>NUNCA vendemos seus dados</li>
                <li>Apenas quando exigido por lei</li>
                <li>Com fornecedores essenciais</li>
                <li>Com seu consentimento explícito</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Link para a versão completa
    st.markdown("""
    <div style="text-align: center; background: rgba(248, 217, 109, 0.1); padding: 25px; border-radius: 15px; border: 2px solid #F8D96D; margin: 20px 0;">
        <h4 style="color: #F8D96D;">📄 Versão Completa da Política</h4>
        <p style="color: #FFFFFF;">
            Para ler a versão completa e detalhada com todos os termos legais:
        </p>
        <div style="margin-top: 15px;">
            <a href="https://burocratadebolso.com/politica-privacidade.html" target="_blank" 
               style="background: #F8D96D; color: #10263D; padding: 12px 30px; border-radius: 30px; 
                      text-decoration: none; font-weight: bold; display: inline-block;">
                🔗 Abrir Política Completa
            </a>
        </div>
        <p style="color: #e2e8f0; font-size: 0.9em; margin-top: 10px;">
            (Será aberta em nova aba do navegador)
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Contato do DPO
    st.markdown("""
    <div style="background: rgba(26, 54, 88, 0.9); padding: 25px; border-radius: 15px; border: 2px solid #F8D96D;">
        <h4 style="color: #F8D96D;">📞 Contato para Privacidade</h4>
        <div style="color: #FFFFFF;">
            <p><strong>Encarregado de Proteção de Dados (DPO):</strong><br>contatoburocrata@outlook.com</p>
            <p><strong>E-mail para Exercício de Direitos:</strong><br>contatoburocrata@outlook.com</p>
            <p><strong>Instagram:</strong><br>@burocratadebolso</p>
            <p><strong>Horário de Atendimento:</strong><br>Segunda a Sexta, 9h às 18h (horário de Brasília)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Botões de navegação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔙 Voltar para o Painel", use_container_width=True, key="voltar_privacidade"):
            st.session_state.pagina = "principal"
            st.rerun()
    
    with col2:
        if st.button("🚪 Sair da Conta", use_container_width=True, key="sair_privacidade"):
            for key in list(st.session_state.keys()):
                if key != 'pagina':
                    del st.session_state[key]
            st.session_state.pagina = "login"
            st.rerun()

# --------------------------------------------------
# MODIFICAÇÃO NA FUNÇÃO mostrar_faq_rodape()
# --------------------------------------------------

def mostrar_faq_rodape():
    """Mostra a seção de FAQ no rodapé"""
    st.markdown("---")
    
    with st.container():
        st.markdown('<div class="faq-container">', unsafe_allow_html=True)
        
        st.markdown('<h3 style="color: #F8D96D; text-align: center; margin-bottom: 20px;">❓ Perguntas Frequentes</h3>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">1. Como adquirir BuroCreds?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Assista a videos<strong> ou nos contate pelo contatoburocrata@outlook.com</strong> solicitando créditos. Você receberá instruções para pagamento e ativação.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">2. Quanto custa cada análise?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Cada análise de documento custa <strong>10 BuroCreds</strong>.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">3. Posso analisar vários documentos de uma vez?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Atualmente, o sistema analisa um documento por vez. Cada análise consome 10 BuroCreds.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">4. Quais tipos de documentos são suportados?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Analisamos contratos de locação, emprego, serviços e compra e venda em formato PDF.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">5. Como funciona o Plano PRO?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">O Plano PRO oferece análises profundas e recursos avançados.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="faq-question">6. Precisa de suporte ou tem reclamações?</div>', unsafe_allow_html=True)
        st.markdown('<div class="faq-answer">Entre em contato: <strong>contatoburocrata@outlook.com</strong> - Respondemos em até 24h.</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Links sociais - MODIFICADO PARA INCLUIR POLÍTICA
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center;">
            <a href="https://www.instagram.com/burocratadebolso/" target="_blank" 
               style="color: #F8D96D; text-decoration: none; display: block; padding: 10px;">
                📷 Instagram
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <a href="mailto:contatoburocrata@outlook.com" 
               style="color: #F8D96D; text-decoration: none; display: block; padding: 10px;">
                📧 E-mail
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Botão para política de privacidade DENTRO DO STREAMLIT
        if st.button("🔒 Política de Privacidade", use_container_width=True, key="btn_politica_rodape"):
            st.session_state.pagina = "privacidade"
            st.rerun()
    
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
# MODIFICAÇÃO NA FUNÇÃO mostrar_tela_login()
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
                            st.session_state.pagina = "principal"
                            
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
                                    st.session_state.pagina = "principal"
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
    
    # Adicionar link para política na tela de login
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔒 Política de Privacidade", use_container_width=True, key="btn_politica_login"):
            st.session_state.pagina = "privacidade"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 10px;">
            <a href="https://burocratadebolso.com/politica-privacidade.html" target="_blank" 
               style="color: #F8D96D; text-decoration: none; font-size: 0.9em;">
                📄 Abrir versão completa
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    mostrar_faq_rodape()

# --------------------------------------------------
# MODIFICAÇÃO NA FUNÇÃO mostrar_tela_principal()
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
        # ... (resto do código de análise permanece igual) ...
        
        # (O código de análise do documento permanece igual que você já tem)
        
    # ... (resto do código da função permanece igual) ...

# --------------------------------------------------
# FUNÇÃO MAIN() ATUALIZADA
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
    
    # CSS customizado
    st.markdown("""
    <style>
    /* CSS existente que você já tem... */
    </style>
    """, unsafe_allow_html=True)
    
    # Lógica de navegação baseada no estado
    if not st.session_state.autenticado:
        mostrar_tela_login()
    else:
        mostrar_tela_principal()

if __name__ == "__main__":
    main()
