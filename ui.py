import streamlit as st
import time
from datetime import datetime

# --------------------------------------------------
# CONFIGURAÇÃO INICIAL
# --------------------------------------------------

# Inicializar estado da sessão
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'pagina' not in st.session_state:
    st.session_state.pagina = "login"
if 'modo_auth' not in st.session_state:
    st.session_state.modo_auth = 'login'

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
body {
    color: #FFFFFF;
}
.stButton > button {
    background: linear-gradient(135deg, #F8D96D, #FFE87C);
    color: #10263D;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(248, 217, 109, 0.4);
}
.header-main {
    text-align: center;
    margin-bottom: 40px;
}
.header-main h1 {
    color: #F8D96D;
    font-size: 3em;
    margin-bottom: 10px;
}
.header-main p {
    color: #e2e8f0;
    font-size: 1.2em;
}
.auth-card {
    background: rgba(26, 54, 88, 0.9);
    padding: 40px;
    border-radius: 20px;
    border: 2px solid #F8D96D;
    max-width: 500px;
    margin: 0 auto;
}
.auth-title {
    color: #F8D96D;
    font-size: 1.8em;
    text-align: center;
    margin-bottom: 30px;
}
.analise-card {
    background: rgba(26, 54, 88, 0.9);
    padding: 25px;
    border-radius: 15px;
    border: 2px solid #F8D96D;
    height: 100%;
    transition: transform 0.3s ease;
}
.analise-card:hover {
    transform: translateY(-5px);
}
.analise-icon {
    font-size: 3em;
    text-align: center;
    margin-bottom: 15px;
    color: #F8D96D;
}
.analise-title {
    color: #F8D96D;
    font-size: 1.4em;
    text-align: center;
    margin-bottom: 20px;
    font-weight: bold;
}
.analise-item {
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px solid rgba(248, 217, 109, 0.2);
}
.analise-item:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}
.analise-item-title {
    color: #FFFFFF;
    font-weight: bold;
    margin-bottom: 5px;
}
.analise-item-desc {
    color: #e2e8f0;
    font-size: 0.9em;
}
.faq-container {
    background: rgba(26, 54, 88, 0.8);
    padding: 30px;
    border-radius: 15px;
    border: 1px solid #F8D96D;
}
.faq-question {
    color: #F8D96D;
    font-weight: bold;
    margin-top: 15px;
    margin-bottom: 5px;
}
.faq-answer {
    color: #FFFFFF;
    margin-bottom: 15px;
    padding-left: 20px;
}
.social-links {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 20px;
}
.social-link {
    color: #F8D96D;
    text-decoration: none;
    padding: 10px 20px;
    border: 1px solid #F8D96D;
    border-radius: 8px;
    transition: all 0.3s ease;
}
.social-link:hover {
    background: #F8D96D;
    color: #10263D;
    text-decoration: none;
}
.user-profile {
    padding: 20px;
    background: rgba(26, 54, 88, 0.8);
    border-radius: 15px;
    border: 2px solid #F8D96D;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# FUNÇÕES AUXILIARES (SIMULADAS PARA TESTE)
# --------------------------------------------------

def simular_autenticacao(email, senha):
    """Função simulada para teste"""
    if email == "teste@teste.com" and senha == "123456":
        return True, {"id": 1, "nome": "Usuário Teste", "email": email, "burocreds": 100}
    return False, "Credenciais inválidas"

def simular_criar_usuario(nome, email, senha):
    """Função simulada para teste"""
    return True, "Conta criada com sucesso!"

def simular_get_usuario_por_id(user_id):
    """Função simulada para teste"""
    return {"id": user_id, "nome": "Usuário Teste", "email": "teste@teste.com", "burocreds": 100}

# --------------------------------------------------
# TELA DE POLÍTICA DE PRIVACIDADE
# --------------------------------------------------

def mostrar_politica_privacidade():
    """Exibe a política de privacidade"""
    
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
            a segurança dos seus dados pessoais.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Informações principais
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: rgba(26, 54, 88, 0.7); padding: 20px; border-radius: 10px; margin-bottom: 15px;">
            <h4 style="color: #F8D96D;">📋 Dados Coletados</h4>
            <ul style="color: #FFFFFF; padding-left: 20px;">
                <li>Nome e e-mail para cadastro</li>
                <li>Documentos enviados para análise</li>
                <li>Histórico de uso da plataforma</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: rgba(26, 54, 88, 0.7); padding: 20px; border-radius: 10px; margin-bottom: 15px;">
            <h4 style="color: #F8D96D;">👤 Seus Direitos (LGPD)</h4>
            <ul style="color: #FFFFFF; padding-left: 20px;">
                <li>Acesso aos seus dados</li>
                <li>Correção de informações</li>
                <li>Eliminação de dados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Link para versão completa
    st.markdown("""
    <div style="text-align: center; background: rgba(248, 217, 109, 0.1); padding: 25px; border-radius: 15px; border: 2px solid #F8D96D; margin: 20px 0;">
        <h4 style="color: #F8D96D;">📄 Versão Completa da Política</h4>
        <p style="color: #FFFFFF;">
            Para ler a versão completa com todos os termos legais:
        </p>
        <div style="margin-top: 15px;">
            <a href="/politica-privacidade.html" target="_blank" 
               style="background: #F8D96D; color: #10263D; padding: 12px 30px; border-radius: 30px; 
                      text-decoration: none; font-weight: bold; display: inline-block;">
                🔗 Abrir Política Completa
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Botões de navegação
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔙 Voltar para o Painel", use_container_width=True):
            st.session_state.pagina = "principal"
            st.rerun()
    
    with col2:
        if st.button("🚪 Sair da Conta", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key != 'pagina':
                    del st.session_state[key]
            st.session_state.autenticado = False
            st.session_state.pagina = "login"
            st.rerun()

# --------------------------------------------------
# CABEÇALHO DO USUÁRIO
# --------------------------------------------------

def mostrar_cabecalho_usuario():
    """Mostra o cabeçalho com informações do usuário"""
    usuario = st.session_state.get('usuario', {})
    
    if not usuario:
        return
    
    st.markdown(f"""
    <div class="user-profile">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="color: #F8D96D; margin: 0; font-size: 1.8em;">
                    👤 {usuario.get('nome', 'Usuário')}
                </h3>
                <p style="color: #FFFFFF; margin: 5px 0 0 0;">{usuario.get('email', '')}</p>
            </div>
            <div style="background: #1a3658; padding: 15px; border-radius: 10px; border: 2px solid #F8D96D;">
                <div style="font-size: 1.8em; color: #F8D96D; font-weight: 700;">
                    {usuario.get('burocreds', 0)}
                </div>
                <div style="color: #FFFFFF; font-size: 0.9em;">BuroCreds</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            # Simular atualização
            usuario['burocreds'] = usuario.get('burocreds', 0)
            st.success("✅ Dados atualizados!")
            time.sleep(0.5)
            st.rerun()
    
    with col2:
        if st.button("🚪 Sair", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.pagina = "login"
            st.rerun()

# --------------------------------------------------
# SEÇÃO: O QUE ANALISAMOS
# --------------------------------------------------

def mostrar_secao_analises():
    """Mostra os tipos de documentos analisados"""
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
    
    tipos_documentos = [
        {
            "icon": "🏠",
            "titulo": "Contrato de Locação",
            "itens": [
                {"titulo": "Valor do Aluguel", "desc": "Onde dói no bolso"},
                {"titulo": "Vigência e Prazo", "desc": "Quanto tempo dura"},
                {"titulo": "Conservação", "desc": "Quem paga pelos reparos"},
                {"titulo": "Multas", "desc": "Preço de sair antes da hora"},
                {"titulo": "Garantia", "desc": "Fiador ou caução"}
            ]
        },
        {
            "icon": "💼",
            "titulo": "Contrato de Emprego",
            "itens": [
                {"titulo": "Salário", "desc": "Remuneração e benefícios"},
                {"titulo": "Jornada", "desc": "Horário de trabalho"},
                {"titulo": "Atribuições", "desc": "Funções do cargo"},
                {"titulo": "Confidencialidade", "desc": "Segredos da empresa"},
                {"titulo": "Rescisão", "desc": "Regras do adeus"}
            ]
        },
        {
            "icon": "🧾",
            "titulo": "Notas Fiscais",
            "itens": [
                {"titulo": "Emitente", "desc": "Quem vendeu"},
                {"titulo": "Itens", "desc": "Lista de compras"},
                {"titulo": "Impostos", "desc": "Tributação aplicada"},
                {"titulo": "Valor Total", "desc": "Montante final"},
                {"titulo": "Pagamento", "desc": "Status financeiro"}
            ]
        }
    ]
    
    for idx, col in enumerate([col1, col2, col3]):
        with col:
            doc = tipos_documentos[idx]
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="analise-icon">{doc["icon"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="analise-title">{doc["titulo"]}</div>', unsafe_allow_html=True)
            
            for item in doc["itens"]:
                st.markdown(f"""
                <div class="analise-item">
                    <div class="analise-item-title">{item['titulo']}</div>
                    <div class="analise-item-desc">{item['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 40px 0;'></div>", unsafe_allow_html=True)

# --------------------------------------------------
# FAQ NO RODAPÉ
# --------------------------------------------------

def mostrar_faq_rodape():
    """Mostra a seção de FAQ"""
    st.markdown("---")
    
    with st.container():
        st.markdown('<div class="faq-container">', unsafe_allow_html=True)
        
        st.markdown('<h3 style="color: #F8D96D; text-align: center; margin-bottom: 20px;">❓ Perguntas Frequentes</h3>', unsafe_allow_html=True)
        
        faq_itens = [
            {"pergunta": "1. Como adquirir BuroCreds?", "resposta": "Entre em contato pelo <strong>contatoburocrata@outlook.com</strong>"},
            {"pergunta": "2. Quanto custa cada análise?", "resposta": "Cada análise custa <strong>10 BuroCreds</strong>"},
            {"pergunta": "3. Quais documentos são suportados?", "resposta": "Contratos de locação, emprego, serviços e compra e venda em PDF"},
            {"pergunta": "4. Precisa de suporte?", "resposta": "Entre em contato: <strong>contatoburocrata@outlook.com</strong> - Respondemos em 24h"}
        ]
        
        for item in faq_itens:
            st.markdown(f'<div class="faq-question">{item["pergunta"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="faq-answer">{item["resposta"]}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Links sociais e política
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
        if st.button("🔒 Política de Privacidade", use_container_width=True, key="btn_politica_faq"):
            st.session_state.pagina = "privacidade"
            st.rerun()
    
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
    
    with st.container():
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        if st.session_state.modo_auth == 'login':
            st.markdown('<div class="auth-title">🔐 Entrar na Conta</div>', unsafe_allow_html=True)
            
            email = st.text_input("E-mail", placeholder="seu@email.com", key="login_email")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha", key="login_senha")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Entrar", use_container_width=True, key="btn_entrar"):
                    if email and senha:
                        # Simular autenticação
                        if email == "teste@teste.com" and senha == "123456":
                            st.session_state.usuario = {
                                "id": 1,
                                "nome": "Usuário Teste",
                                "email": email,
                                "burocreds": 100
                            }
                            st.session_state.autenticado = True
                            st.session_state.pagina = "principal"
                            st.success("✅ Login realizado com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Credenciais inválidas. Use: teste@teste.com / 123456")
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
            
            st.info("ℹ️ **Para testes:** Use qualquer dados. O sistema está em modo de demonstração.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎉 Criar Conta", use_container_width=True, key="btn_criar"):
                    if nome and email and senha and confirmar_senha:
                        if senha != confirmar_senha:
                            st.error("❌ As senhas não coincidem")
                        elif len(senha) < 6:
                            st.error("❌ A senha deve ter no mínimo 6 caracteres")
                        else:
                            # Simular criação
                            st.session_state.usuario = {
                                "id": 2,
                                "nome": nome,
                                "email": email,
                                "burocreds": 0
                            }
                            st.session_state.autenticado = True
                            st.session_state.pagina = "principal"
                            st.success("✅ Conta criada com sucesso!")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("⚠️ Preencha todos os campos")
            
            with col2:
                if st.button("🔙 Voltar ao Login", use_container_width=True, key="btn_voltar"):
                    st.session_state.modo_auth = 'login'
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Link para política
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔒 Política de Privacidade", use_container_width=True, key="btn_politica_login"):
            st.session_state.pagina = "privacidade"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 10px;">
            <a href="/politica-privacidade.html" target="_blank" 
               style="color: #F8D96D; text-decoration: none; font-size: 0.9em;">
                📄 Versão completa
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    mostrar_faq_rodape()

# --------------------------------------------------
# TELA PRINCIPAL
# --------------------------------------------------

def mostrar_tela_principal():
    """Tela principal após login"""
    
    if st.session_state.pagina == "privacidade":
        mostrar_politica_privacidade()
        return
    
    st.markdown("""
    <div class="header-main">
        <h1>⚖️ BUROCRATA DE BOLSO</h1>
        <p>IA de Análise Documental</p>
    </div>
    """, unsafe_allow_html=True)
    
    mostrar_cabecalho_usuario()
    
    usuario = st.session_state.get('usuario', {})
    nome_usuario = usuario.get('nome', 'Usuário').split()[0]
    
    hora = datetime.now().hour
    if hora < 12:
        saudacao = "Bom dia"
    elif hora < 18:
        saudacao = "Boa tarde"
    else:
        saudacao = "Boa noite"
    
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
    
    st.markdown("""
    <div style="text-align: center; margin: 30px 0;">
        <div style="font-size: 2em; color: #F8D96D; margin-bottom: 10px;">📄</div>
        <h3 style="color: #F8D96D;">Envie seu documento para análise</h3>
        <p style="color: #FFFFFF;">Formatos suportados: PDF • Até 10MB</p>
    </div>
    """, unsafe_allow_html=True)
    
    arquivo = st.file_uploader("Selecione um arquivo PDF", type=["pdf"], key="file_uploader")
    
    if arquivo:
        burocreds = usuario.get('burocreds', 0)
        
        if burocreds < 10:
            st.error("""
            ❌ **Saldo insuficiente!** 
            
            Você precisa de pelo menos **10 BuroCreds** para realizar uma análise.
            
            **Solução:** Entre em contato com o suporte para adquirir créditos.
            """)
        else:
            with st.spinner(f"🔍 Analisando juridicamente '{arquivo.name}'..."):
                time.sleep(2)  # Simular análise
                
                # Simular resultado
                st.success("✅ Análise concluída!")
                
                # Simular redução de créditos
                usuario['burocreds'] = max(0, burocreds - 10)
                
                st.markdown("### 📊 Resultados da Análise Jurídica")
                
                st.markdown("""
                <div style="background: rgba(26, 54, 88, 0.9); padding: 25px; border-radius: 15px; border: 2px solid #27AE60; margin: 20px 0;">
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <div style="font-size: 2em; margin-right: 15px;">✅</div>
                        <div>
                            <h3 style="color: #27AE60; margin: 0;">Documento Regular</h3>
                            <p style="color: #FFFFFF; margin: 5px 0 0 0;">
                                <strong>Documento:</strong> {arquivo.name} • <strong>Tipo:</strong> Contrato de Locação • <strong>Risco:</strong> Baixo
                            </p>
                        </div>
                    </div>
                </div>
                """.format(arquivo.name=arquivo.name), unsafe_allow_html=True)
                
                # Métricas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Problemas Detectados", "2")
                
                with col2:
                    st.metric("Score Conformidade", "85%")
                
                with col3:
                    st.metric("BuroCreds Restantes", usuario['burocreds'], delta=-10)
                
                # Recomendação
                st.markdown("""
                <div style="background: #1a3658; padding: 20px; border-radius: 15px; margin: 20px 0; border: 2px solid #F8D96D;">
                    <h4 style="color: #F8D96D; margin-top: 0;">💡 Recomendação Jurídica</h4>
                    <p style="color: #FFFFFF; margin-bottom: 0;">
                        <strong>Documento analisado com sucesso!</strong> 
                        Para validação completa e assessoria jurídica personalizada, 
                        recomenda-se a consulta com um advogado especializado.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Botão para nova análise
                st.markdown("---")
                if st.button("🔄 Realizar Nova Análise", use_container_width=True, type="primary"):
                    st.rerun()
    
    # Informações sobre créditos
    st.markdown("---")
    st.markdown("""
    <div style="background: #1a3658; padding: 20px; border-radius: 15px; margin: 20px 0; border: 2px solid #F8D96D;">
        <h4 style="color: #F8D96D; margin-top: 0;">💰 Sobre os BuroCreds</h4>
        <ul style="color: #FFFFFF; margin-bottom: 0;">
            <li>Cada análise custa <strong>10 BuroCreds</strong></li>
            <li>Para adquirir créditos: <strong>contatoburocrata@outlook.com</strong></li>
            <li>Plano PRO: Análises profundas + recursos avançados</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    mostrar_faq_rodape()

# --------------------------------------------------
# FUNÇÃO PRINCIPAL
# --------------------------------------------------

def main():
    """Função principal do app"""
    
    # Lógica de navegação
    if not st.session_state.autenticado:
        mostrar_tela_login()
    else:
        mostrar_tela_principal()

if __name__ == "__main__":
    main()
