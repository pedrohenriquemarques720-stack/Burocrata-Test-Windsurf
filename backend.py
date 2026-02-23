from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import uuid
import io
import pdfplumber

# IMPORTAR o Core Engine Jurídico do arquivo core_juridico.py
from core_juridico import CoreEngineJuridico

# Carregar variáveis de ambiente
load_dotenv()

# Importar cliente AbacatePay
from abacatepay import get_abacate_client

app = Flask(__name__)
CORS(app)

# Configurações - usando variáveis de ambiente
ABACATE_API_KEY = os.getenv('ABACATE_API_KEY', 'abc_dev_apB2fqGwQFb0bPsUBGmAuHeC')
ABACATE_WEBHOOK_ID = os.getenv('ABACATE_WEBHOOK_ID', 'webh_dev_ahdHbQwGKz4qds2aphSsHWtH')
DATABASE_URL = os.getenv('DATABASE_URL')
APP_URL = os.getenv('APP_URL', 'https://burocratadebolso.com.br')

# Verificar se a DATABASE_URL está configurada
if not DATABASE_URL:
    print("❌ ERRO CRÍTICO: DATABASE_URL não configurada!")
    print("❌ Configure a variável DATABASE_URL no Render com a Internal Database URL")
    DATABASE_URL = "postgresql://usuario:senha@localhost:5432/burocrata_db"  # fallback para desenvolvimento local

# Verificar se a chave da API está configurada
if not ABACATE_API_KEY:
    print("⚠️  AVISO: ABACATE_API_KEY não configurada. Usando valor padrão de teste.")
    print("⚠️  Para produção, configure a chave no arquivo .env")

# Inicializar cliente AbacatePay
try:
    abacate = get_abacate_client()
    print("✅ Cliente AbacatePay inicializado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao inicializar cliente AbacatePay: {e}")
    abacate = None

print(f"🚀 Backend iniciado com webhook ID: {ABACATE_WEBHOOK_ID}")
print(f"🔑 API Key configurada: {'Sim' if ABACATE_API_KEY else 'Não'}")
print(f"🗄️  Banco de dados: PostgreSQL configurado")

# ===== FUNÇÕES DE CONEXÃO COM O BANCO =====

def get_db_connection():
    """Retorna uma conexão com o banco PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None

def init_db():
    """Verifica se as tabelas existem (já devem ter sido criadas pelo schema.sql)"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cur = conn.cursor()
        
        # Verificar se a tabela users existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """)
        users_exists = cur.fetchone()[0]
        
        if not users_exists:
            print("⚠️  Tabela 'users' não encontrada! Execute o schema.sql primeiro.")
            return False
        
        print("✅ Banco de dados verificado - todas as tabelas existem")
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco de dados: {e}")
        return False

# Inicializar banco de dados
init_db()

# ===== FUNÇÕES DE AUTENTICAÇÃO =====

def hash_senha(senha):
    """Gera hash da senha usando SHA-256 (compatível com o sistema anterior)"""
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_usuario(nome, email, senha):
    """Cria um novo usuário no banco PostgreSQL"""
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Erro de conexão com o banco de dados"
        
        cur = conn.cursor()
        
        # Verificar se email já existe
        cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return False, "E-mail já registrado"
        
        # Gerar UUID para o usuário
        user_id = str(uuid.uuid4())
        senha_hash = hash_senha(senha)
        
        # Inserir usuário
        cur.execute("""
            INSERT INTO users (user_id, email, full_name, password_hash, account_status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id
        """, (user_id, email, nome, senha_hash, 'active'))
        
        # Atribuir papel de usuário comum (free_user)
        cur.execute("SELECT role_id FROM roles WHERE role_name = 'free_user'")
        role_result = cur.fetchone()
        if role_result:
            cur.execute("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
            """, (user_id, role_result[0]))
        
        # Registrar no log de auditoria
        cur.execute("""
            INSERT INTO audit_logs (user_id, event_type, event_action, resource_type, resource_id)
            VALUES (%s, 'user_created', 'create', 'users', %s)
        """, (user_id, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, {
            'id': user_id,
            'nome': nome,
            'email': email,
            'plano': 'free_user',
            'burocreditos': 0
        }
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        return False, f"Erro ao criar usuário: {str(e)}"

def autenticar_usuario(email, senha):
    """Autentica um usuário"""
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Erro de conexão com o banco de dados"
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        senha_hash = hash_senha(senha)
        
        # Buscar usuário
        cur.execute("""
            SELECT u.user_id, u.email, u.full_name, u.account_status,
                   array_agg(r.role_name) as roles
            FROM users u
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.role_id
            WHERE u.email = %s AND u.password_hash = %s AND u.account_status = 'active'
            GROUP BY u.user_id
        """, (email, senha_hash))
        
        user = cur.fetchone()
        
        if user:
            # Registrar login
            cur.execute("""
                INSERT INTO login_history (user_id, ip_address, user_agent, login_success)
                VALUES (%s, %s, %s, %s)
                RETURNING login_id
            """, (user['user_id'], request.remote_addr, request.headers.get('User-Agent'), True))
            
            login_id = cur.fetchone()['login_id']
            
            # Atualizar last_login
            cur.execute("""
                UPDATE users SET last_login = NOW() WHERE user_id = %s
            """, (user['user_id'],))
            
            conn.commit()
            
            # Buscar créditos (vindo da tabela subscriptions, simplificado)
            cur.execute("""
                SELECT COALESCE(s.burocreditos, 0) as burocreditos
                FROM users u
                LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.status = 'active'
                WHERE u.user_id = %s
            """, (user['user_id'],))
            
            creditos_result = cur.fetchone()
            burocreditos = creditos_result['burocreditos'] if creditos_result else 0
            
            cur.close()
            conn.close()
            
            return True, {
                'id': user['user_id'],
                'nome': user['full_name'],
                'email': user['email'],
                'plano': user['roles'][0] if user['roles'] else 'free_user',
                'burocreditos': burocreditos,
                'estado': user['account_status']
            }
        else:
            # Registrar tentativa falha
            cur.execute("""
                INSERT INTO login_history (user_id, ip_address, user_agent, login_success)
                VALUES (NULL, %s, %s, %s)
            """, (request.remote_addr, request.headers.get('User-Agent'), False))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return False, "E-mail ou senha incorretos"
            
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return False, f"Erro na autenticação: {str(e)}"

def obter_usuario_por_id(usuario_id):
    """Obtém informações do usuário pelo ID"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT u.user_id as id, u.email, u.full_name as nome, u.account_status as estado,
                   array_agg(r.role_name) as roles,
                   COALESCE(s.burocreditos, 0) as burocreditos
            FROM users u
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.role_id
            LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.status = 'active'
            WHERE u.user_id = %s
            GROUP BY u.user_id, s.burocreditos
        """, (usuario_id,))
        
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        
        if resultado:
            return {
                'id': resultado['id'],
                'nome': resultado['nome'],
                'email': resultado['email'],
                'plano': resultado['roles'][0] if resultado['roles'] else 'free_user',
                'burocreditos': resultado['burocreditos'],
                'estado': resultado['estado']
            }
        else:
            return None
            
    except Exception as e:
        print(f"❌ Erro ao obter usuário: {e}")
        return None

def atualizar_burocreditos(usuario_id, quantidade):
    """Atualiza os BuroCréditos do usuário (na tabela subscriptions)"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cur = conn.cursor()
        
        # Verificar se é conta especial
        cur.execute("SELECT email FROM users WHERE user_id = %s", (usuario_id,))
        user = cur.fetchone()
        
        if user and user[0] == "pedrohenriquemarques720@gmail.com":
            conn.close()
            return True
        
        # Atualizar ou criar subscription
        cur.execute("""
            INSERT INTO subscriptions (user_id, plan_id, burocreditos, status)
            VALUES (%s, (SELECT plan_id FROM plans WHERE plan_code = 'free'), %s, 'active')
            ON CONFLICT (user_id) 
            DO UPDATE SET burocreditos = subscriptions.burocreditos + %s
        """, (usuario_id, quantidade, quantidade))
        
        # Registrar no log de auditoria
        cur.execute("""
            INSERT INTO audit_logs (user_id, event_type, event_action, resource_type, resource_id)
            VALUES (%s, 'credits_updated', 'update', 'subscriptions', %s)
        """, (usuario_id, usuario_id))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar créditos: {e}")
        return False

def registar_analise(utilizador_id, nome_ficheiro, tipo_documento, problemas, pontuacao):
    """Regista uma análise no histórico (usando audit_logs)"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cur = conn.cursor()
        
        # Registrar no audit_logs (simplificado)
        cur.execute("""
            INSERT INTO audit_logs (user_id, event_type, event_action, resource_type, resource_id, new_data)
            VALUES (%s, 'document_analysis', 'create', 'document', %s, %s)
        """, (utilizador_id, str(uuid.uuid4()), json.dumps({
            'filename': nome_ficheiro,
            'tipo': tipo_documento,
            'problemas': problemas,
            'pontuacao': pontuacao,
            'data': datetime.now().isoformat()
        })))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao registrar análise: {e}")
        return False

def salvar_cobranca(usuario_id, bill_id, pacote, valor, creditos, url):
    """Salva cobrança no banco de dados"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cur = conn.cursor()
        
        # Criar tabela de cobranças se não existir (já deve existir, mas garantimos)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cobrancas_abacate (
                id SERIAL PRIMARY KEY,
                bill_id TEXT UNIQUE,
                usuario_id UUID,
                pacote TEXT,
                valor REAL,
                creditos TEXT,
                url_pagamento TEXT,
                status TEXT DEFAULT 'PENDENTE',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_pagamento TIMESTAMP
            )
        """)
        
        cur.execute("""
            INSERT INTO cobrancas_abacate (bill_id, usuario_id, pacote, valor, creditos, url_pagamento)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (bill_id) DO NOTHING
        """, (bill_id, usuario_id, pacote, valor, str(creditos), url))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"💾 Cobrança salva: {bill_id}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar cobrança: {e}")
        return False

def obter_historico_utilizador(utilizador_id, limite=5):
    """Obtém histórico de análises do usuário"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT new_data->>'filename' as nome_ficheiro,
                   new_data->>'tipo' as tipo_documento,
                   (new_data->>'problemas')::int as problemas_detetados,
                   (new_data->>'pontuacao')::float as pontuacao_conformidade,
                   data_pagamento as data_analise
            FROM audit_logs
            WHERE user_id = %s AND event_type = 'document_analysis'
            ORDER BY data_pagamento DESC
            LIMIT %s
        """, (utilizador_id, limite))
        
        historico = []
        for row in cur.fetchall():
            historico.append({
                'ficheiro': row['nome_ficheiro'],
                'tipo': row['tipo_documento'],
                'problemas': row['problemas_detetados'],
                'pontuacao': row['pontuacao_conformidade'],
                'data': row['data_analise'].isoformat() if row['data_analise'] else None
            })
        
        cur.close()
        conn.close()
        return historico
        
    except Exception as e:
        print(f"❌ Erro ao obter histórico: {e}")
        return []

# ===== FUNÇÕES AUXILIARES PARA ANÁLISE DE DOCUMENTOS =====

def extrair_texto_pdf_bytes(bytes_pdf):
    """Extrai texto de bytes de PDF"""
    try:
        with pdfplumber.open(io.BytesIO(bytes_pdf)) as pdf:
            texto = ""
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina + "\n"
            return texto if texto.strip() else None
    except Exception as e:
        print(f"❌ Erro ao extrair PDF: {e}")
        return None

def registrar_auditoria(usuario_id, evento, dados):
    """Registra ação no log de auditoria"""
    try:
        conn = get_db_connection()
        if not conn:
            return
        
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_logs (user_id, event_type, event_action, new_data)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, evento, 'document_analysis', json.dumps(dados)))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao registrar auditoria: {e}")

# ===== ROTA PARA ANÁLISE JURÍDICA DE DOCUMENTOS =====
@app.route('/analisar-documento', methods=['POST'])
def analisar_documento():
    """Recebe um PDF e retorna análise jurídica completa"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        usuario_id = request.form.get('usuario_id')
        
        if file.filename == '':
            return jsonify({"success": False, "error": "Nome de arquivo vazio"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"success": False, "error": "Formato não suportado. Envie PDF."}), 400
        
        # Extrair texto do PDF
        texto = extrair_texto_pdf_bytes(file.read())
        
        if not texto:
            return jsonify({"success": False, "error": "Não foi possível extrair texto do PDF"}), 400
        
        # Inicializar detector jurídico (importado do core_juridico.py)
        detector = CoreEngineJuridico()
        
        # Analisar documento
        resultado = detector.analisar_documento_completo(texto)
        
        # Registrar análise no banco
        if usuario_id:
            registar_analise(
                usuario_id, 
                file.filename, 
                resultado['tipo_documento'],
                resultado['metricas']['total'],
                resultado['metricas']['pontuacao']
            )
        
        # Registrar no audit_logs
        registrar_auditoria(
            usuario_id=usuario_id,
            evento='document_analysis',
            dados={
                'filename': file.filename,
                'tipo': resultado['tipo_documento'],
                'violacoes': resultado['metricas']['total'],
                'exposicao': resultado['exposicao_risco']
            }
        )
        
        return jsonify({
            "success": True,
            "resultado": resultado
        })
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ===== ROTAS DA API (já existentes) =====

@app.route('/')
def index():
    return jsonify({
        "status": "API Burocrata de Bolso funcionando!",
        "payment": "AbacatePay integrado",
        "webhook_id": ABACATE_WEBHOOK_ID,
        "webhook_url": f"{APP_URL}/webhook/abacate",
        "api_key_configured": bool(ABACATE_API_KEY),
        "database": "PostgreSQL configurado"
    })

@app.route('/criar-pagamento', methods=['POST'])
def criar_pagamento():
    """Cria um pagamento no AbacatePay"""
    try:
        if not abacate:
            return jsonify({
                "success": False, 
                "error": "Cliente AbacatePay não inicializado. Verifique a chave da API."
            }), 500

        dados = request.json
        print("📦 Dados recebidos:", json.dumps(dados, indent=2))
        
        pacote = dados.get('pacote')
        valor = float(dados.get('valor'))
        creditos = dados.get('creditos')
        usuario_id = dados.get('usuario_id')
        usuario_email = dados.get('usuario_email')
        usuario_nome = dados.get('usuario_nome', 'Cliente')
        usuario_cpf = dados.get('usuario_cpf', '')
        
        if not all([pacote, valor, usuario_id, usuario_email]):
            return jsonify({"success": False, "error": "Dados incompletos"}), 400
        
        print(f"💳 Criando pagamento para {usuario_email} - Pacote: {pacote}")
        
        sucesso, url_pagamento, dados_cobranca = abacate.criar_cobranca(
            email=usuario_email,
            nome=usuario_nome,
            cpf=usuario_cpf,
            pacote=pacote,
            valor=valor,
            creditos=creditos,
            usuario_id=usuario_id
        )
        
        if sucesso and url_pagamento:
            salvar_cobranca(
                usuario_id=usuario_id,
                bill_id=dados_cobranca.get('id', f"temp_{pacote}"),
                pacote=pacote,
                valor=valor,
                creditos=creditos,
                url=url_pagamento
            )
            
            print(f"✅ Pagamento AbacatePay criado para usuário {usuario_id}")
            print(f"🔗 URL: {url_pagamento}")
            
            return jsonify({
                "success": True,
                "url_pagamento": url_pagamento,
                "bill_id": dados_cobranca.get('id')
            })
        else:
            print("❌ Erro ao criar pagamento AbacatePay")
            return jsonify({"success": False, "error": "Erro ao criar pagamento"}), 400
            
    except Exception as e:
        print("❌ Erro:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/pagamento')
def pagina_pagamento():
    """Serve a página de pagamento"""
    try:
        pacote = request.args.get('pacote', 'bronze')
        valor = request.args.get('valor', '15')
        creditos = request.args.get('creditos', '30')
        email = request.args.get('email', '')
        
        html_path = os.path.join(os.path.dirname(__file__), 'pagamento.html')
        
        if not os.path.exists(html_path):
            html_content = f"""<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Burocrata de Bolso - Pagamento</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #10263D;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{ max-width: 500px; width: 90%; margin: 20px; }}
        .card {{
            background: #1a3658;
            border-radius: 20px;
            padding: 30px;
            border: 3px solid #F8D96D;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }}
        h1 {{
            color: #F8D96D;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
        }}
        .dados-compra {{
            background: #0f2a40;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .dados-compra p {{ margin: 10px 0; font-size: 1.1em; }}
        .dados-compra strong {{ color: #F8D96D; }}
        .btn-pagar {{
            background: linear-gradient(135deg, #F8D96D, #d4b747);
            color: #10263D;
            border: none;
            padding: 20px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 1.3em;
            width: 100%;
            cursor: pointer;
            margin: 20px 0;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }}
        .btn-pagar:hover {{
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(248, 217, 109, 0.4);
        }}
        .btn-voltar {{
            background: transparent;
            color: #F8D96D;
            border: 2px solid #F8D96D;
            padding: 12px;
            border-radius: 10px;
            font-weight: 600;
            width: 100%;
            cursor: pointer;
            margin-top: 20px;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }}
        .btn-voltar:hover {{ background: rgba(248, 217, 109, 0.1); }}
        .loading {{
            text-align: center;
            padding: 20px;
            display: none;
        }}
        .spinner {{
            border: 4px solid rgba(248, 217, 109, 0.2);
            border-top: 4px solid #F8D96D;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .info-webhook {{
            font-size: 0.8em;
            color: #a0aec0;
            text-align: center;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>⚖️ Finalizar Compra</h1>
            
            <div class="dados-compra">
                <p><strong>Pacote:</strong> <span id="pacote-nome">{pacote.capitalize()}</span></p>
                <p><strong>Valor:</strong> R$ <span id="pacote-valor">{valor}</span></p>
                <p><strong>Créditos:</strong> <span id="pacote-creditos">{creditos}</span></p>
                <p><strong>E-mail:</strong> <span id="usuario-email">{email or 'Não informado'}</span></p>
            </div>

            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>🔍 Criando pagamento...</p>
            </div>

            <button id="btn-pagar" class="btn-pagar" onclick="criarPagamento()">
                💳 Ir para o AbacatePay
            </button>
            
            <div class="info-webhook">
                Webhook ID: {ABACATE_WEBHOOK_ID}<br>
                URL: {APP_URL}/webhook/abacate
            </div>
            
            <a href="/" class="btn-voltar">← Voltar para Loja</a>
        </div>
    </div>

    <script>
        function criarPagamento() {{
            const btn = document.getElementById('btn-pagar');
            const loading = document.getElementById('loading');
            
            btn.style.display = 'none';
            loading.style.display = 'block';
            
            let usuario_id = localStorage.getItem('usuario_id') || '1';
            let usuario_nome = localStorage.getItem('usuario_nome') || 'Cliente';
            
            const dados = {{
                pacote: '{pacote}',
                valor: {valor},
                creditos: '{creditos}',
                usuario_id: usuario_id,
                usuario_email: '{email}',
                usuario_nome: usuario_nome,
                usuario_cpf: ''
            }};
            
            console.log('📤 Enviando dados:', dados);
            
            fetch('/criar-pagamento', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(dados)
            }})
            .then(response => response.json())
            .then(data => {{
                console.log('📥 Resposta:', data);
                if (data.success && data.url_pagamento) {{
                    window.location.href = data.url_pagamento;
                }} else {{
                    alert('Erro ao criar pagamento: ' + (data.error || 'Tente novamente'));
                    btn.style.display = 'block';
                    loading.style.display = 'none';
                }}
            }})
            .catch(error => {{
                console.error('❌ Erro:', error);
                alert('Erro de conexão com o servidor. Verifique se o backend está rodando.');
                btn.style.display = 'block';
                loading.style.display = 'none';
            }});
        }}
    </script>
</body>
</html>"""
            
            return html_content
        
        return send_file(html_path)
        
    except Exception as e:
        print(f"❌ Erro ao servir página de pagamento: {e}")
        return f"Erro: {e}", 500

@app.route('/retorno')
def retorno_pagamento():
    """Página para onde o usuário volta após o pagamento"""
    bill_id = request.args.get('bill_id')
    status = request.args.get('status', 'pending')
    
    print(f"🔄 Retorno de pagamento: bill_id={bill_id}, status={status}")
    
    if status == 'PAID' or status == 'approved':
        return render_template('sucesso.html')
    elif status == 'failed':
        return render_template('falha.html')
    else:
        return render_template('pendente.html')

@app.route('/status-pagamento/<string:usuario_id>')
def status_pagamento(usuario_id):
    """Verifica se o usuário tem créditos atualizados"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "Erro de conexão"}), 500
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("""
            SELECT COALESCE(s.burocreditos, 0) as burocreditos,
                   array_agg(r.role_name) as plano
            FROM users u
            LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.status = 'active'
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.role_id
            WHERE u.user_id = %s
            GROUP BY s.burocreditos
        """, (usuario_id,))
        
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        
        if resultado:
            plano_str = resultado['plano'][0] if resultado['plano'] else 'free_user'
            return jsonify({
                "success": True,
                "burocreditos": resultado['burocreditos'],
                "plano": plano_str,
                "provider": "abacatepay"
            })
        else:
            return jsonify({"success": False}), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/teste-abacate')
def teste_abacate():
    """Rota para testar a integração"""
    return jsonify({
        "status": "AbacatePay integrado",
        "api_key_configured": bool(ABACATE_API_KEY),
        "webhook_id": ABACATE_WEBHOOK_ID,
        "webhook_url": f"{APP_URL}/webhook/abacate"
    })

@app.route('/criar-conta', methods=['POST'])
def criar_conta():
    """Rota para criar nova conta de usuário"""
    try:
        dados = request.json
        nome = dados.get('nome')
        email = dados.get('email')
        senha = dados.get('senha')
        
        if not all([nome, email, senha]):
            return jsonify({"success": False, "error": "Dados incompletos"}), 400
        
        if len(senha) < 6:
            return jsonify({"success": False, "error": "Senha deve ter no mínimo 6 caracteres"}), 400
        
        sucesso, resultado = criar_usuario(nome, email, senha)
        
        if sucesso:
            return jsonify({
                "success": True,
                "usuario": resultado,
                "mensagem": "Usuário criado com sucesso!"
            })
        else:
            return jsonify({"success": False, "error": resultado}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """Rota para login de usuário"""
    try:
        dados = request.json
        email = dados.get('email')
        senha = dados.get('senha')
        
        if not email or not senha:
            return jsonify({"success": False, "error": "E-mail e senha obrigatórios"}), 400
        
        sucesso, resultado = autenticar_usuario(email, senha)
        
        if sucesso:
            return jsonify({
                "success": True,
                "usuario": resultado
            })
        else:
            return jsonify({"success": False, "error": resultado}), 401
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===== NO FINAL DO ARQUIVO =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('ENV') != 'production'
    
    print("🚀 Servidor Burocrata iniciando...")
    print(f"🔗 Webhook configurado: {APP_URL}/webhook/abacate")
    print(f"🆔 Webhook ID: {ABACATE_WEBHOOK_ID}")
    print(f"🔑 API Key: {'Configurada' if ABACATE_API_KEY else 'NÃO CONFIGURADA'}")
    print(f"🗄️  Banco: PostgreSQL")
    print(f"🌐 Modo: {'Produção' if not debug_mode else 'Desenvolvimento'}")
    print(f"📡 Porta: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
