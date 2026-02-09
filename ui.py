import streamlit as st
import time
from datetime import datetime
from detection import SistemaDetecção
from database import autenticar_usuario, criar_usuario, get_usuario_por_id, atualizar_burocreds, registrar_analise, get_historico_usuario
from utils import extrair_texto_pdf

# --------------------------------------------------
# TELA DE LOGIN
# --------------------------------------------------

def mostrar_tela_login():
    """Tela de login"""
    st.markdown("""
    <div class="header-main">
        <h1>BUROCRATA DE BOLSO</h1>
        <p>IA de Analise Documental</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'modo_auth' not in st.session_state:
        st.session_state.modo_auth = 'login'
    
    with st.container():
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        if st.session_state.modo_auth == 'login':
            st.markdown('<div class="auth-title">Entrar na Conta</div>', unsafe_allow_html=True)
            
            email = st.text_input("E-mail", placeholder="seu@email.com", key="login_email")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha", key="login_senha")
            
            if email == "pedrohenriquemarques720@gmail.com":
                st.info("Conta Especial Detectada: Use sua senha pessoal para acessar.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Entrar", use_container_width=True, key="btn_entrar"):
                    if email and senha:
                        sucesso, resultado = autenticar_usuario(email, senha)
                        if sucesso:
                            st.session_state.usuario = resultado
                            st.session_state.autenticado = True
                            
                            if email == "pedrohenriquemarques720@gmail.com":
                                st.success("Conta Especial: Acesso concedido com creditos ilimitados!")
                            else:
                                st.success("Login realizado com sucesso!")
                            
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"{resultado}")
                    else:
                        st.warning("Preencha todos os campos")
            
            with col2:
                if st.button("Criar Conta", use_container_width=True, key="btn_criar_conta_login"):
                    st.session_state.modo_auth = 'cadastro'
                    st.rerun()
        
        else:
            st.markdown('<div class="auth-title">Criar Nova Conta</div>', unsafe_allow_html=True)
            
            nome = st.text_input("Nome Completo", placeholder="Seu nome", key="cad_nome")
            email = st.text_input("E-mail", placeholder="seu@email.com", key="cad_email")
            senha = st.text_input("Senha", type="password", placeholder="Minimo 6 caracteres", key="cad_senha")
            confirmar_senha = st.text_input("Confirmar Senha", type="password", placeholder="Digite novamente", key="cad_confirmar")
            
            st.info("Importante: Novas contas comecam com 0 BuroCreds. Para adquirir creditos, entre em contato com o suporte.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Criar Conta", use_container_width=True, key="btn_criar"):
                    if nome and email and senha and confirmar_senha:
                        if senha != confirmar_senha:
                            st.error("As senhas nao coincidem")
                        elif len(senha) < 6:
                            st.error("A senha deve ter no minimo 6 caracteres")
                        else:
                            sucesso, mensagem = criar_usuario(nome, email, senha)
                            if sucesso:
                                st.success(f"{mensagem}")
                                sucesso_login, usuario = autenticar_usuario(email, senha)
                                if sucesso_login:
                                    st.session_state.usuario = usuario
                                    st.session_state.autenticado = True
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.error(f"{mensagem}")
                    else:
                        st.warning("Preencha todos os campos")
            
            with col2:
                if st.button("Voltar ao Login", use_container_width=True, key="btn_voltar"):
                    st.session_state.modo_auth = 'login'
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    mostrar_faq_rodape()

# --------------------------------------------------
# CABECALHO DO USUARIO
# --------------------------------------------------

def mostrar_cabecalho_usuario():
    """Mostra o cabecalho simplificado com informacoes do usuario"""
    usuario = st.session_state.usuario
    
    is_conta_especial = usuario['email'] == "pedrohenriquemarques720@gmail.com"
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div class="user-profile">
                <h3 style="color: #F8D96D; margin: 0; font-size: 1.8em;">
                    {usuario['nome']}
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
                    {'ILIMITADO' if is_conta_especial else usuario['burocreds']}
                </div>
                <div style="color: #FFFFFF; font-size: 0.9em;">BuroCreds</div>
            </div>
            """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Atualizar Dados", use_container_width=True, key="btn_atualizar"):
            usuario_atualizado = get_usuario_por_id(usuario['id'])
            if usuario_atualizado:
                st.session_state.usuario = usuario_atualizado
                st.success("Dados atualizados!")
                time.sleep(0.5)
                st.rerun()
    
    with col2:
        if st.button("Sair", use_container_width=True, key="btn_sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# --------------------------------------------------
# SECAO: O QUE ANALISAMOS
# --------------------------------------------------

def mostrar_secao_analises():
    """Mostra a secao com os tipos de documentos que analisamos"""
    st.markdown("""
    <div style="text-align: center; margin: 40px 0 30px 0;">
        <h2 style="color: #F8D96D; font-size: 2.2em; margin-bottom: 10px;">
            O QUE ANALISAMOS
        </h2>
        <p style="color: #FFFFFF; font-size: 1.1em; max-width: 800px; margin: 0 auto;">
            Nossa inteligencia artificial verifica os pontos mais importantes dos seus documentos juridicos
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">CASA</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Contrato de Locacao</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Valor do Aluguel e Reajuste</div>
                <div class="analise-item-desc">Verificacao de valores e periodos permitidos.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Vigencia e Prazo</div>
                <div class="analise-item-desc">Analise do prazo contratual.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Conservacao e Reformas</div>
                <div class="analise-item-desc">Responsabilidades de manutencao.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">TRABALHO</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Contrato de Emprego</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Remuneracao e Beneficios</div>
                <div class="analise-item-desc">Salario e beneficios contratados.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Jornada de Trabalho</div>
                <div class="analise-item-desc">Horarios e carga horaria.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Atribuicoes do Cargo</div>
                <div class="analise-item-desc">Funcoes e responsabilidades.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        with st.container():
            st.markdown('<div class="analise-card">', unsafe_allow_html=True)
            st.markdown('<div class="analise-icon">DOCUMENTO</div>', unsafe_allow_html=True)
            st.markdown('<div class="analise-title">Outros Documentos</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Notas Fiscais</div>
                <div class="analise-item-desc">Validacao de documentos fiscais.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Contratos em Geral</div>
                <div class="analise-item-desc">Analise de clausulas contratuais.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analise-item">
                <div class="analise-item-title">Documentos Juridicos</div>
                <div class="analise-item-desc">Verificacao de legalidade.</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# TELA PRINCIPAL
# --------------------------------------------------

def mostrar_tela_principal():
    """Tela principal do aplicativo"""
    mostrar_cabecalho_usuario()
    
    mostrar_secao_analises()
    
    detector = SistemaDetecção()
    
    st.markdown("""
    <div style="text-align: center; margin: 30px 0;">
        <div style="font-size: 2em; color: #F8D96D; margin-bottom: 10px;">PDF</div>
        <h3 style="color: #F8D96D;">Envie seu documento para analise</h3>
        <p style="color: #FFFFFF;">Formatos suportados: PDF • Ate 10MB</p>
    </div>
    """, unsafe_allow_html=True)
    
    arquivo = st.file_uploader("Selecione um arquivo PDF", type=["pdf"])
    
    if arquivo:
        is_conta_especial = st.session_state.usuario['email'] == "pedrohenriquemarques720@gmail.com"
        
        if not is_conta_especial and st.session_state.usuario['burocreds'] < 10:
            st.error("""
            Saldo insuficiente! 
            
            Voce precisa de pelo menos 10 BuroCreds para realizar uma analise.
            
            Solucao: Entre em contato com o suporte para adquirir creditos.
            """)
        else:
            with st.spinner(f"Analisando juridicamente '{arquivo.name}'..."):
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
                    
                    # Mostrar resumo da analise
                    st.markdown("### Resultados da Analise Juridica")
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <div style="font-size: 2em; margin-right: 15px;">&nbsp;</div>
                            <div>
                                <h3 style="color: {metricas['cor']}; margin: 0;">{metricas['status']}</h3>
                                <p style="color: #FFFFFF; margin: 5px 0 0 0;">
                                    <strong>Documento:</strong> {arquivo.name}
                                    {f"• <strong>Tipo:</strong> {detector.padroes.get(tipo_doc, {}).get('nome', 'Documento')}" if tipo_doc != 'DESCONHECIDO' else ''}
                                    • <strong>Nivel de Risco:</strong> {metricas['nivel_risco']}
                                </p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Metricas detalhadas
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Problemas Detectados", metricas['total'], delta_color="inverse")
                    
                    with col2:
                        st.metric("Criticos", metricas['criticos'], delta_color="inverse")
                    
                    with col3:
                        st.metric("Altos", metricas['altos'], delta_color="inverse")
                    
                    with col4:
                        st.metric("Medios", metricas['medios'], delta_color="inverse")
                    
                    with col5:
                        st.metric("Score", f"{metricas['score']:.1f}%", delta_color="inverse")
                    
                    # Problemas detalhados
                    problemas_criticos = [p for p in problemas if p['nivel'] == 'CRITICO']
                    problemas_altos = [p for p in problemas if p['nivel'] == 'ALTO']
                    problemas_medios = [p for p in problemas if p['nivel'] == 'MEDIO']
                    
                    if problemas_criticos:
                        st.markdown("#### Problemas Criticos (Acao Imediata)")
                        for i, problema in enumerate(problemas_criticos, 1):
                            st.markdown(f"""
                            <div style="background: rgba(231, 76, 60, 0.15);
                                      border-left: 4px solid #E74C3C;
                                      padding: 20px;
                                      border-radius: 10px;
                                      margin: 10px 0;">
                                <h4 style="color: #E74C3C; margin-top: 0;">
                                    {i}. {problema['titulo']}
                                </h4>
                                <p style="margin: 5px 0; color: #FFFFFF;">
                                    <strong>Base Legal:</strong> {problema['lei']}
                                </p>
                                <p style="margin: 5px 0; color: #e2e8f0; font-size: 0.9em;">
                                    {problema.get('detalhe', '')}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    if problemas_altos:
                        st.markdown("#### Problemas Altos (Atencao Necessaria)")
                        for i, problema in enumerate(problemas_altos, 1):
                            st.markdown(f"""
                            <div style="background: rgba(243, 156, 18, 0.15);
                                      border-left: 4px solid #F39C12;
                                      padding: 20px;
                                      border-radius: 10px;
                                      margin: 10px 0;">
                                <h4 style="color: #F39C12; margin-top: 0;">
                                    {i}. {problema['titulo']}
                                </h4>
                                <p style="margin: 5px 0; color: #FFFFFF;">
                                    <strong>Base Legal:</strong> {problema['lei']}
                                </p>
                                <p style="margin: 5px 0; color: #e2e8f0; font-size: 0.9em;">
                                    {problema.get('detalhe', '')}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    if problemas_medios:
                        st.markdown("#### Problemas Medios (Revisao Recomendada)")
                        for i, problema in enumerate(problemas_medios, 1):
                            st.markdown(f"""
                            <div style="background: rgba(241, 196, 15, 0.15);
                                      border-left: 4px solid #F1C40F;
                                      padding: 20px;
                                      border-radius: 10px;
                                      margin: 10px 0;">
                                <h4 style="color: #F1C40F; margin-top: 0;">
                                    {i}. {problema['titulo']}
                                </h4>
                                <p style="margin: 5px 0; color: #FFFFFF;">
                                    <strong>Base Legal:</strong> {problema['lei']}
                                </p>
                                <p style="margin: 5px 0; color: #e2e8f0; font-size: 0.9em;">
                                    {problema.get('detalhe', '')}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    if not problemas:
                        st.success("""
                        Parabens! Nenhum problema significativo foi detectado neste documento.
                        
                        O documento parece estar em conformidade com a legislacao vigente.
                        """)
                    
                    # Acoes recomendadas
                    if problemas:
                        st.markdown("---")
                        st.markdown("### Acoes Recomendadas")
                        
                        if problemas_criticos:
                            st.warning("""
                            **Urgente:** Procure um advogado imediatamente para regularizar os pontos criticos.
                            """)
                        
                        if problemas_altos:
                            st.info("""
                            **Recomendado:** Revise os pontos destacados com um profissional juridico.
                            """)
                        
                        if problemas_medios:
                            st.info("""
                            **Sugestao:** Considere ajustar os itens de medio risco para maior seguranca.
                            """)
                else:
                    st.error("""
                    Nao foi possivel analisar o documento
                    
                    Possiveis causas:
                    - O arquivo PDF esta corrompido
                    - O PDF esta protegido por senha
                    - O arquivo esta em formato de imagem (nao contem texto)
                    - O arquivo esta muito grande
                    
                    Solucao: Certifique-se de que o PDF contem texto selecionavel.
                    """)
    
    # Historico de analises
    historico = get_historico_usuario(st.session_state.usuario['id'])
    if historico:
        with st.expander("Historico de Analises (Ultimas 5)", expanded=False):
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
                                <span>Problemas: {item['problemas']}</span>
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
    
    is_conta_especial = st.session_state.usuario['email'] == "pedrohenriquemarques720@gmail.com"
    
    if not is_conta_especial:
        st.markdown("---")
        st.markdown("""
        <div style="background: #1a3658;
                    padding: 20px;
                    border-radius: 15px;
                    margin: 20px 0;
                    border: 2px solid #F8D96D;">
            <h4 style="color: #F8D96D; margin-top: 0;">Sobre os BuroCreds</h4>
            <ul style="color: #FFFFFF; margin-bottom: 0;">
                <li>Cada analise custa <strong>10 BuroCreds</strong></li>
                <li>Para adquirir creditos: <strong>Veja videos ou nos chame em contatoburocrata@outlook.com</strong></li>
                <li>Plano PRO: Analises profundas + recursos avancados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    mostrar_faq_rodape()

# --------------------------------------------------
# FAQ E RODAPE
# --------------------------------------------------

def mostrar_faq_rodape():
    """Mostra o FAQ e rodape"""
    st.markdown("---")
    
    with st.expander("❓ Perguntas Frequentes", expanded=False):
        st.markdown("""
        <div class="faq-container">
            <div class="faq-question">O que sao BuroCreds?</div>
            <div class="faq-answer">
                BuroCreds sao creditos utilizados para realizar analises de documentos. Cada analise consome 10 creditos.
            </div>
            
            <div class="faq-question">Como adquirir mais BuroCreds?</div>
            <div class="faq-answer">
                Entre em contato com nosso suporte pelo email contatoburocrata@outlook.com ou assista aos videos disponiveis.
            </div>
            
            <div class="faq-question">O app substitui um advogado?</div>
            <div class="faq-answer">
                Nao. Nosso app fornece uma analise preliminar e nao substitui a consulta com um profissional qualificado.
            </div>
            
            <div class="faq-question">Quais tipos de documentos analisam?</div>
            <div class="faq-answer">
                Analisamos contratos de locacao, contratos de trabalho, notas fiscais e outros documentos juridicos.
            </div>
            
            <div class="faq-question">Meus dados estao seguros?</div>
            <div class="faq-answer">
                Sim. Utilizamos criptografia e seguidores as melhores praticas de seguranca para proteger suas informacoes.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin: 40px 0 20px 0; padding: 20px; background: #1a3658; border-radius: 15px; border: 2px solid #F8D96D;">
        <h3 style="color: #F8D96D; margin-top: 0;">Fale Conosco</h3>
        <p style="color: #FFFFFF; margin: 10px 0;">
            <strong>Email:</strong> contatoburocrata@outlook.com<br>
            <strong>Instagram:</strong> @burocratadebolso
        </p>
        <p style="color: #e2e8f0; font-size: 0.9em; margin: 15px 0 0 0;">
            Resposta em ate 24 horas uteis
        </p>
    </div>
    
    <div style="text-align: center; margin: 20px 0; color: #a0aec0; font-size: 0.8em;">
        <p>&copy; 2026 Burocrata de Bolso. Todos os direitos reservados.</p>
        <p style="margin: 5px 0;">
            Esta aplicacao fornece analise preliminar e nao substitui a consulta com um advogado qualificado.
        </p>
    </div>
    """, unsafe_allow_html=True)
