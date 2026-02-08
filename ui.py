import streamlit as st
import time
from datetime import datetime
from detection import Detector

# Import opcional para compatibilidade com produção
try:
    from smart_detector import SmartDetector
    SMART_DETECTOR_AVAILABLE = True
except ImportError:
    SMART_DETECTOR_AVAILABLE = False
    print("Aviso: SmartDetector não disponível - usando modo padrão")

# Import opcional para utils
try:
    from utils import extrair_texto_pdf, formatar_moeda, formatar_data
    UTILS_AVAILABLE = True
except ImportError as e:
    UTILS_AVAILABLE = False
    print(f"Aviso: utils não disponível - {e}")
    
    # Criar função de fallback para extração de PDF
    def extrair_texto_pdf(arquivo):
        """Função de fallback para extração de PDF"""
        try:
            import pdfplumber
            texto_total = ""
            with pdfplumber.open(arquivo) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        texto_total += text + "\n"
            
            if texto_total.strip():
                return texto_total
            else:
                st.error("❌ Não foi possível extrair texto do PDF")
                return None
        except ImportError:
            st.error("❌ pdfplumber não disponível no ambiente")
            return None
        except Exception as e:
            st.error(f"❌ Erro ao extrair texto: {str(e)}")
            return None
    
    def formatar_moeda(valor):
        return f"R$ {valor:.2f}"
    
    def formatar_data(data):
        return data.strftime("%d/%m/%Y")

import database as db
from database import autenticar_usuario, criar_usuario, get_usuario_por_id, atualizar_burocreds, registrar_analise, get_historico_usuario

# --------------------------------------------------
# TELA DE LOGIN
# --------------------------------------------------

def mostrar_tela_login():
    """Tela de login com visual moderno integrado"""
    
    # CSS adicional para o layout moderno
    st.markdown("""
    <style>
    .login-container {
        display: flex;
        flex-direction: column;
        gap: 40px;
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    .features-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 30px;
        margin-bottom: 20px;
    }
    .feature-card-login {
        background: #1a3658;
        padding: 30px;
        border-radius: 15px;
        border: 2px solid #F8D96D;
        text-align: center;
        transition: transform 0.3s;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .feature-card-login:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(248, 217, 109, 0.2);
    }
    .feature-icon {
        font-size: 3em;
        margin-bottom: 20px;
        color: #F8D96D;
    }
    .feature-title {
        color: #F8D96D;
        font-size: 1.5em;
        margin-bottom: 15px;
        font-weight: 700;
    }
    .auth-section {
        background: #2a4a75;
        padding: 40px;
        border-radius: 15px;
        border: 2px solid #F8D96D;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .auth-title {
        color: #F8D96D;
        font-size: 2.2em;
        font-weight: 800;
        margin-bottom: 30px;
    }
    .faq-section {
        background: #1a3658;
        padding: 30px;
        border-radius: 15px;
        border: 2px solid #F8D96D;
        margin-top: 40px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .faq-title {
        color: #F8D96D;
        font-size: 1.5em;
        font-weight: 700;
        margin-bottom: 20px;
        text-align: center;
    }
    .faq-item {
        margin-bottom: 15px;
        padding: 15px;
        background: rgba(248, 217, 109, 0.1);
        border-radius: 10px;
        border-left: 4px solid #F8D96D;
    }
    .faq-question {
        color: #F8D96D;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .faq-answer {
        color: #FFFFFF;
        line-height: 1.5;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="header-main">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>IA de Análise Documental - Proteção Jurídica Inteligente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Container principal
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Cards de Features
    st.markdown("""
    <div class="features-row">
        <div class="feature-card-login">
            <div class="feature-icon">📄</div>
            <div class="feature-title">Análise Inteligente</div>
            <p>IA avançada para análise de contratos, notas fiscais e documentos jurídicos com precisão e rapidez.</p>
        </div>
        
        <div class="feature-card-login">
            <div class="feature-icon">🔒</div>
            <div class="feature-title">Segurança Total</div>
            <p>Seus documentos são protegidos com criptografia de ponta a ponta e armazenamento seguro local, em conformidade com LGPD.</p>
        </div>
        
        <div class="feature-card-login">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Resultado Rápido</div>
            <p>Análises em segundos com relatórios detalhados e recomendações práticas para suas decisões.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de Login/Cadastro
    st.markdown('<div class="auth-section">', unsafe_allow_html=True)
    
    if 'modo_auth' not in st.session_state:
        st.session_state.modo_auth = 'login'
    
    if st.session_state.modo_auth == 'login':
        st.markdown('<div class="auth-title">🔐 Acessar Sistema</div>', unsafe_allow_html=True)
        
        email = st.text_input("E-mail", placeholder="seu@email.com", key="login_email")
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha", key="login_senha")
        
        if email == "pedrohenriquemarques720@gmail.com":
            st.info("🔑 **Conta Especial Detectada:** Use sua senha pessoal para acessar.")
        
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
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            <span style="color: #a0aec0;">Não tem conta? </span>
            <a href="#" onclick="window.location.reload()" style="color: #F8D96D; text-decoration: none; font-weight: bold;">
                Criar Conta
            </a>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        st.markdown('<div class="auth-title">📝 Criar Nova Conta</div>', unsafe_allow_html=True)
        
        nome = st.text_input("Nome Completo", placeholder="Seu nome", key="cad_nome")
        email = st.text_input("E-mail", placeholder="seu@email.com", key="cad_email")
        senha = st.text_input("Senha", type="password", placeholder="Mínimo 6 caracteres", key="cad_senha")
        confirmar_senha = st.text_input("Confirmar Senha", type="password", placeholder="Digite novamente", key="cad_confirmar")
        
        st.info("ℹ️ **Importante:** Novas contas começam com 0 BuroCreds. Para adquirir créditos, entre em contato com o suporte.")
        
        # Checkbox de consentimento da política de privacidade
        consentimento = st.checkbox("✅ Li e concordo com a [Política de Privacidade](privacidade.html) e autorizo o tratamento dos meus dados conforme descrito.", key="consentimento_privacidade")
        
        if not consentimento:
            st.warning("⚠️ É necessário aceitar a Política de Privacidade para criar uma conta.")
        
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
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            <span style="color: #a0aec0;">Já tem conta? </span>
            <a href="#" onclick="window.location.reload()" style="color: #F8D96D; text-decoration: none; font-weight: bold;">
                Fazer Login
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # FAQ Section
    st.markdown('<div class="faq-section">', unsafe_allow_html=True)
    st.markdown('<div class="faq-title">📋 Perguntas Frequentes</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="faq-item">
        <div class="faq-question">1. Como funciona a análise de documentos?</div>
        <div class="faq-answer">Nossa IA analisa seus documentos jurídicos em segundos, identificando cláusulas importantes, riscos e oportunidades. Basta fazer upload do arquivo e receber um relatório completo.</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="faq-item">
        <div class="faq-question">2. Meus documentos estão seguros?</div>
        <div class="faq-answer">Sim! Usamos criptografia de ponta a ponta e armazenamento seguro local. Seus dados são protegidos em conformidade com a LGPD e nunca compartilhamos com terceiros.</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="faq-item">
        <div class="faq-question">3. Quais tipos de documentos analisam?</div>
        <div class="faq-answer">Analisamos contratos de locação, contratos de trabalho, notas fiscais, termos de serviço e outros documentos jurídicos com alta precisão.</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="faq-item">
        <div class="faq-question">4. Quanto tempo demora a análise?</div>
        <div class="faq-answer">A maioria dos documentos é analisada em menos de 1 minuto. Documentos simples podem levar apenas alguns segundos, enquanto contratos complexos levam até 2 minutos.</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="faq-item">
        <div class="faq-question">5. Posso testar antes de comprar?</div>
        <div class="faq-answer">Sim! Novas contas recebem créditos iniciais para testar nossa plataforma. Você pode experimentar todas as funcionalidades antes de adquirir mais créditos.</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# CABEÇALHO DO USUÁRIO
# --------------------------------------------------

def mostrar_cabecalho_usuario():
    """Mostra o cabeçalho simplificado com informações do usuário"""
    usuario = st.session_state.usuario
    
    is_conta_especial = usuario['email'] == "pedrohenriquemarques720@gmail.com"
    
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
            Nossa inteligência artificial verifica os pontos mais importantes dos seus documentos jurídicos
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: #1a3658; border-radius: 15px; padding: 25px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3); border-top: 5px solid #F8D96D; 
                    height: 100%; text-align: center;">
            <div style="font-size: 2.5em; margin-bottom: 15px; color: #F8D96D;">🏠</div>
            <div style="color: #F8D96D; font-size: 1.5em; font-weight: 700; margin-bottom: 20px;">
                Contrato de Locação
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Valor do Aluguel e Reajuste -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">Onde dói no bolso (ou entra o dinheiro).</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Vigência e Prazo -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">Quanto tempo dura o "felizes para sempre".</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Conservação e Reformas -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">Quem paga pelo cano que estourou.</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Multas e Rescisão -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">O preço de sair antes da hora.</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Garantia Locatória -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">O famoso fiador, caução ou seguro.</p>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #1a3658; border-radius: 15px; padding: 25px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3); border-top: 5px solid #F8D96D; 
                    height: 100%; text-align: center;">
            <div style="font-size: 2.5em; margin-bottom: 15px; color: #F8D96D;">💼</div>
            <div style="color: #F8D96D; font-size: 1.5em; font-weight: 700; margin-bottom: 20px;">
                Contrato de Emprego
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Remuneração e Benefícios -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">Salário, VR, VT e os mimos.</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Jornada de Trabalho -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">O horário de bater o ponto.</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Atribuições do Cargo -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">O que, afinal, você foi contratado para fazer.</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Confidencialidade -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">O que acontece na empresa, morre na empresa.</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Aviso Prévio e Rescisão -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">As regras do adeus.</p>', unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: #1a3658; border-radius: 15px; padding: 25px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3); border-top: 5px solid #F8D96D; 
                    height: 100%; text-align: center;">
            <div style="font-size: 2.5em; margin-bottom: 15px; color: #F8D96D;">🧾</div>
            <div style="color: #F8D96D; font-size: 1.5em; font-weight: 700; margin-bottom: 20px;">
                Notas Fiscais
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Dados do Emissor/Destinatário -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">Quem vendeu e quem comprou.</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Itens e Serviços -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">A lista de compras detalhada.</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Impostos e Tributação -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">A fatia que fica para o governo.</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Valor Total e Descontos -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">O número final da conta.</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align: center; color: #FFFFFF; font-size: 1.1em; font-weight: bold;">- Status de Pagamento -</p>', unsafe_allow_html=True)
        st.write('<p style="text-align: center; color: #FFFFFF; font-size: 0.9em;">Se já caiu na conta ou se ainda é promessa.</p>', unsafe_allow_html=True)
    
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
    
    # Links sociais
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="social-links">
            <a href="https://www.instagram.com/burocratadebolso/" target="_blank" class="social-link">
                📷 Instagram
            </a>
            <a href="mailto:contatoburocrata@outlook.com" class="social-link">
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

# --------------------------------------------------
# TELA PRINCIPAL
# --------------------------------------------------

def mostrar_tela_principal():
    """Tela principal após login"""
    
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
        saudacao = "Bem-vindo"
    elif hora < 18:
        saudacao = "Bem-vindo"
    else:
        saudacao = "Bem-vindo"
    
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
    
    detector = Detector()
    
    st.markdown("""
    <div style="text-align: center; margin: 30px 0;">
        <div style="font-size: 2em; color: #F8D96D; margin-bottom: 10px;">📄</div>
        <h3 style="color: #F8D96D;">Envie seu documento para análise</h3>
        <p style="color: #FFFFFF;">Formatos suportados: PDF • Até 10MB</p>
    </div>
    """, unsafe_allow_html=True)
    
    arquivo = st.file_uploader("Selecione um arquivo PDF", type=["pdf"], key="file_uploader")
    
    if arquivo:
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
                    # Usar SmartDetector se disponível, senão usar padrão
                    if SMART_DETECTOR_AVAILABLE:
                        smart_detector = SmartDetector()
                        resultado = smart_detector.analisar_documento_inteligente(texto)
                        
                        # Mostrar informações de aprendizado se houver
                        learning_info = resultado.get('learning_info', {})
                        if learning_info.get('improved_analysis'):
                            st.success(f"🧠 **IA APRENDEU!** +{learning_info.get('improvement', 0)} problemas detectados automaticamente!")
                    else:
                        # Usar detector padrão
                        detector = Detector()
                        resultado = detector.analisar_documento(texto)
                    
                    if st.session_state.usuario['id']:
                        registrar_analise(
                            st.session_state.usuario['id'],
                            arquivo.name,
                            resultado['tipo_documento'],
                            resultado['total'],
                            resultado['score']
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
                                <h3 style="color: {resultado['cor']}; margin: 0;">{resultado['status']}</h3>
                                <p style="color: #FFFFFF; margin: 5px 0 0 0;">
                                    <strong>Documento:</strong> {arquivo.name}
                                    {f"• <strong>Tipo:</strong> {detector.padroes.get(resultado['tipo_documento'], {}).get('nome', 'Documento')}" if resultado['tipo_documento'] != 'DESCONHECIDO' else ''}
                                    • <strong>Nível de Risco:</strong> {resultado['nivel_risco']}
                                </p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Métricas detalhadas
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Problemas Detectados", resultado['total'], delta_color="inverse")
                    
                    with col2:
                        st.metric("Críticos", resultado['criticos'], delta_color="inverse")
                    
                    with col3:
                        st.metric("Altos", resultado['altos'], delta_color="inverse")
                    
                    with col4:
                        st.metric("Score Conformidade", f"{resultado['score']}%")
                    
                    with col5:
                        if is_conta_especial:
                            st.metric("BuroCreds Restantes", "∞")
                        else:
                            st.metric("BuroCreds Restantes", st.session_state.usuario['burocreds'], delta=-10)
                    
                    # Detalhes dos problemas detectados
                    if resultado['problemas']:
                        st.markdown("### ⚖️ Problemas Jurídicos Detectados")
                        
                        # Agrupar por gravidade
                        problemas_criticos = [p for p in resultado['problemas'] if p['gravidade'] == 'CRÍTICA']
                        problemas_altos = [p for p in resultado['problemas'] if p['gravidade'] == 'ALTA']
                        problemas_medios = [p for p in resultado['problemas'] if p['gravidade'] == 'MÉDIA']
                        
                        if problemas_criticos:
                            st.markdown("#### 🔴 Problemas Críticos (Requerem Atenção Imediata)")
                            for i, problema in enumerate(problemas_criticos, 1):
                                st.markdown(f"""
                                <div style="background: rgba(231, 76, 60, 0.15);
                                          border-left: 4px solid #E74C3C;
                                          padding: 20px;
                                          border-radius: 10px;
                                          margin: 10px 0;
                                          box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
                                    <div style="display: flex; align-items: flex-start;">
                                        <div style="font-size: 1.5em; margin-right: 15px; color: #E74C3C;">🔴</div>
                                        <div style="flex: 1;">
                                            <h4 style="margin: 0 0 8px 0; color: #E74C3C;">
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
                        
                        if problemas_altos:
                            st.markdown("#### 🟠 Problemas Altos (Ajustes Necessários)")
                            for i, problema in enumerate(problemas_altos, 1):
                                st.markdown(f"""
                                <div style="background: rgba(243, 156, 18, 0.15);
                                          border-left: 4px solid #F39C12;
                                          padding: 20px;
                                          border-radius: 10px;
                                          margin: 10px 0;
                                          box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
                                    <div style="display: flex; align-items: flex-start;">
                                        <div style="font-size: 1.5em; margin-right: 15px; color: #F39C12;">🟠</div>
                                        <div style="flex: 1;">
                                            <h4 style="margin: 0 0 8px 0; color: #F39C12;">
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
                        
                        if problemas_medios:
                            st.markdown("#### 🟡 Problemas Médios (Revisão Recomendada)")
                            for i, problema in enumerate(problemas_medios, 1):
                                st.markdown(f"""
                                <div style="background: rgba(241, 196, 15, 0.15);
                                          border-left: 4px solid #F1C40F;
                                          padding: 20px;
                                          border-radius: 10px;
                                          margin: 10px 0;
                                          box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
                                    <div style="display: flex; align-items: flex-start;">
                                        <div style="font-size: 1.5em; margin-right: 15px; color: #F1C40F;">🟡</div>
                                        <div style="flex: 1;">
                                            <h4 style="margin: 0 0 8px 0; color: #F1C40F;">
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
                        
                        # Recomendação jurídica
                        if resultado.get('recomendacoes'):
                            st.markdown("""
                            <div style="background: #1a3658;
                                      padding: 20px;
                                      border-radius: 15px;
                                      margin: 20px 0;
                                      border: 2px solid #F8D96D;">
                                <h4 style="color: #F8D96D; margin-top: 0;">⚠️ RECOMENDAÇÕES URGENTES</h4>
                            """, unsafe_allow_html=True)
                            
                            for recomendacao in resultado['recomendacoes']:
                                st.markdown(f"""
                                <p style="color: #FFFFFF; margin: 5px 0; font-weight: bold;">
                                    {recomendacao}
                                </p>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                        
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
    
    if not is_conta_especial:
        st.markdown("---")
        st.markdown("""
        <div style="background: #1a3658;
                    padding: 20px;
                    border-radius: 15px;
                    margin: 20px 0;
                    border: 2px solid #F8D96D;">
            <h4 style="color: #F8D96D; margin-top: 0;">💰 Sobre os BuroCreds</h4>
            <ul style="color: #FFFFFF; margin-bottom: 0;">
                <li>Cada análise custa <strong>10 BuroCreds</strong></li>
                <li>Para adquirir créditos: <strong>Veja vídeos ou nos chame em contatoburocrata@outlook.com</strong></li>
                <li>Plano PRO: Análises profundas + recursos avançados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    mostrar_faq_rodape()

# --------------------------------------------------
# FAQ E RODAPÉ
# --------------------------------------------------

def mostrar_faq_rodape():
    """Mostra seção de FAQ e rodapé"""
    
    st.markdown("---")
    
    # FAQ Section
    st.markdown("""
    <div class="faq-container">
        <h3 style="color: #F8D96D; text-align: center; margin-bottom: 25px; margin-top: 0;">
            ❓ PERGUNTAS FREQUENTES
        </h3>
    """, unsafe_allow_html=True)
    
    # FAQ 1
    with st.expander("🔍 1. Que tipos de documentos o sistema analisa?"):
        st.markdown("""
        <div class="faq-answer">
            Nosso sistema especializado analisa:
            • <strong>Contratos de Trabalho</strong> (CLT, PJ, estágio)
            • <strong>Contratos de Locação</strong> (residencial, comercial)
            • <strong>Notas Fiscais</strong> (serviços, produtos)
            • <strong>Documentos diversos</strong> com cláusulas contratuais
        </div>
        """, unsafe_allow_html=True)
    
    # FAQ 2
    with st.expander("⚖️ 2. Como funciona a análise jurídica?"):
        st.markdown("""
        <div class="faq-answer">
            Nossa IA utiliza:
            • <strong>100+ padrões jurídicos</strong> atualizados
            • <strong>Inteligência Artificial</strong> que aprende
            • <strong>Análise profunda</strong> de cláusulas
            • <strong>Base legal</strong> para cada problema
            • <strong>Recomendações</strong> práticas e específicas
        </div>
        """, unsafe_allow_html=True)
    
    # FAQ 3 - CORRIGIDA
    with st.expander("📄 3. Posso analisar vários documentos de uma vez?"):
        st.markdown("""
        <div class="faq-answer">
            Atualmente, o sistema analisa um documento por vez para uma maior precisão.
        </div>
        """, unsafe_allow_html=True)
    
    # FAQ 4
    with st.expander("🔒 4. Meus documentos são seguros?"):
        st.markdown("""
        <div class="faq-answer">
            Sim! Suas informações estão protegidas:
            • <strong>Privacidade total</strong> dos dados
            • <strong>Armazenamento seguro</strong> local
            • <strong>Compartilhamento opcional</strong> apenas com seu consentimento
            • <strong>Conformidade</strong> com LGPD
            <br><br>
            📋 <strong>Para mais detalhes:</strong> Consulte nossa <a href="privacidade.html" target="_blank" style="color: #F8D96D;">Política de Privacidade</a>
        </div>
        """, unsafe_allow_html=True)
    
    # FAQ 5
    with st.expander("⚡ 5. Quão rápida é a análise?"):
        st.markdown("""
        <div class="faq-answer">
            Nossa análise é ultra-rápida:
            • <strong>Segundos</strong> para documentos simples
            • <strong>Menos de 1 minuto</strong> para contratos complexos
            • <strong>Resultados detalhados</strong> instantâneos
            • <strong>IA aprende</strong> e fica mais rápida com o tempo
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer - Versão Python Streamlit puro
    st.markdown("---")
    
    # Container do rodapé
    st.markdown("""
    <div style="background: #1a3658; 
                padding: 30px; 
                margin-top: 40px; 
                text-align: center; 
                border: 2px solid #F8D96D;
                border-radius: 15px;">
    """, unsafe_allow_html=True)
    
    # Título principal
    st.markdown("""
    <h3 style="color: #F8D96D; font-size: 1.8em; font-weight: bold; margin-bottom: 15px; margin-top: 0; text-align: center;">
        ⚖️ BUROCRATA DE BOLSO
    </h3>
    """, unsafe_allow_html=True)
    
    # Subtítulo
    st.markdown("""
    <p style="color: #FFFFFF; font-size: 1.1em; margin-bottom: 15px; margin-top: 0; text-align: center;">
        IA de Análise Documental - Proteção Jurídica Inteligente
    </p>
    """, unsafe_allow_html=True)
    
    # Descrição
    st.markdown("""
    <p style="color: #e2e8f0; font-size: 0.9em; margin-bottom: 20px; margin-top: 0; text-align: center;">
    </p>
    """, unsafe_allow_html=True)
    
    # Links usando colunas Streamlit
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center;">
            <a href="mailto:contatoburocrata@outlook.com" 
               style="color: #F8D96D; text-decoration: none; font-weight: bold; font-size: 1.1em;">
                📧 contatoburocrata@outlook.com
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <a href="https://instagram.com/burocratadebolso" 
               target="_blank"
               style="color: #F8D96D; text-decoration: none; font-weight: bold; font-size: 1.1em;">
                📷 @burocratadebolso
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center;">
            <a href="privacidade.html" 
               target="_blank"
               style="color: #F8D96D; text-decoration: none; font-weight: bold; font-size: 1.1em;">
                🔒 Política de Privacidade
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    # Linha separadora e copyright
    st.markdown("""
    <div style="border-top: 1px solid #F8D96D; margin-top: 20px; padding-top: 20px;">
        <p style="color: #a0aec0; font-size: 0.8em; margin: 0; text-align: center;">
            © 2026 Burocrata de Bolso - Todos os direitos reservados - Criado por Pedro Graciano
        </p>
    </div>
    </div>
    """, unsafe_allow_html=True)
