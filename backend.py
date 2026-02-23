from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import pg8000
import pg8000.dbapi
import pg8000.native
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import hashlib
import uuid
import io
import pdfplumber

# Importar o Core Engine Jurídico
from core_juridico import CoreEngineJuridico

# Importar cliente AbacatePay
from abacatepay import get_abacate_client

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app, origins="*")

# Configurações
ABACATE_API_KEY = os.getenv('ABACATE_API_KEY', '')
ABACATE_WEBHOOK_ID = os.getenv('ABACATE_WEBHOOK_ID', '')
DATABASE_URL = os.getenv('DATABASE_URL')
APP_URL = os.getenv('APP_URL', 'https://burocrata-backend.onrender.com')

print("="*50)
print("🚀 SERVIDOR BUROCRATA INICIANDO")
print("="*50)

# ===== FUNÇÕES DE CONEXÃO COM O BANCO (AGORA USANDO pg8000) =====
def get_db_connection():
    """Retorna uma conexão com o banco PostgreSQL usando pg8000"""
    try:
        # Extrair dados da DATABASE_URL
        # Formato: postgres://usuario:senha@host:porta/banco
        if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
            # Parse da URL
            partes = DATABASE_URL.replace('postgres://', '').split('@')
            usuario_senha = partes[0].split(':')
            host_porta_banco = partes[1].split('/')
            host_porta = host_porta_banco[0].split(':')
            
            usuario = usuario_senha[0]
            senha = usuario_senha[1]
            host = host_porta[0]
            porta = int(host_porta[1]) if len(host_porta) > 1 else 5432
            banco = host_porta_banco[1]
            
            conn = pg8000.native.Connection(
                user=usuario,
                password=senha,
                host=host,
                port=porta,
                database=banco
            )
            print("✅ Conexão com banco de dados estabelecida")
            return conn
        else:
            print("⚠️ DATABASE_URL não configurada corretamente")
            return None
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None

# ===== FUNÇÕES DE AUTENTICAÇÃO E BANCO =====
def hash_senha(senha):
    """Gera hash da senha usando SHA-256"""
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_usuario(nome, email, senha):
    """Cria um novo usuário no banco PostgreSQL"""
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Erro de conexão com o banco de dados"
        
        # Verificar se email já existe
        result = conn.run("SELECT user_id FROM users WHERE email = :email", email=email)
        if result and len(result) > 0:
            conn.close()
            return False, "E-mail já registrado"
        
        # Gerar UUID para o usuário
        user_id = str(uuid.uuid4())
        senha_hash = hash_senha(senha)
        
        # Inserir usuário
        conn.run("""
            INSERT INTO users (user_id, email, full_name, password_hash, account_status)
            VALUES (:user_id, :email, :full_name, :password_hash, :account_status)
        """, 
            user_id=user_id, 
            email=email, 
            full_name=nome, 
            password_hash=senha_hash, 
            account_status='active'
        )
        
        # Atribuir papel de usuário comum (free_user)
        role_result = conn.run("SELECT role_id FROM roles WHERE role_name = :role_name", role_name='free_user')
        if role_result and len(role_result) > 0:
            role_id = role_result[0][0]
            conn.run("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
            """, user_id=user_id, role_id=role_id)
        
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
        
        senha_hash = hash_senha(senha)
        
        # Buscar usuário
        result = conn.run("""
            SELECT u.user_id, u.email, u.full_name, u.account_status,
                   array_agg(r.role_name) as roles
            FROM users u
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.role_id
            WHERE u.email = :email AND u.password_hash = :password_hash AND u.account_status = 'active'
            GROUP BY u.user_id
        """, email=email, password_hash=senha_hash)
        
        if result and len(result) > 0:
            user_data = result[0]
            user_id = user_data[0]
            
            # Buscar créditos
            creditos_result = conn.run("""
                SELECT COALESCE(s.burocreditos, 0) as burocreditos
                FROM users u
                LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.status = 'active'
                WHERE u.user_id = :user_id
            """, user_id=user_id)
            
            burocreditos = creditos_result[0][0] if creditos_result and len(creditos_result) > 0 else 0
            
            conn.close()
            
            return True, {
                'id': user_id,
                'nome': user_data[2],
                'email': user_data[1],
                'plano': user_data[4][0] if user_data[4] else 'free_user',
                'burocreditos': burocreditos,
                'estado': user_data[3]
            }
        else:
            conn.close()
            return False, "E-mail ou senha incorretos"
            
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return False, f"Erro na autenticação: {str(e)}"

def salvar_cobranca(usuario_id, bill_id, pacote, valor, creditos, url):
    """Salva cobrança no banco de dados"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # Criar tabela de cobranças se não existir
        conn.run("""
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
        
        conn.run("""
            INSERT INTO cobrancas_abacate (bill_id, usuario_id, pacote, valor, creditos, url_pagamento)
            VALUES (:bill_id, :usuario_id, :pacote, :valor, :creditos, :url_pagamento)
            ON CONFLICT (bill_id) DO NOTHING
        """, 
            bill_id=bill_id, 
            usuario_id=usuario_id, 
            pacote=pacote, 
            valor=valor, 
            creditos=str(creditos), 
            url_pagamento=url
        )
        
        conn.close()
        print(f"💾 Cobrança salva: {bill_id}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar cobrança: {e}")
        return False

# ===== FUNÇÕES AUXILIARES PARA PDF =====
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

# ===== ROTA PRINCIPAL =====
@app.route('/')
def index():
    return jsonify({
        "status": "API Burocrata de Bolso funcionando!",
        "payment": "AbacatePay integrado",
        "webhook_id": ABACATE_WEBHOOK_ID,
        "webhook_url": f"{APP_URL}/webhook/abacate",
        "api_key_configured": bool(ABACATE_API_KEY),
        "database_driver": "pg8000 (100% Python)",
        "rotas_disponiveis": [
            "/", 
            "/ping", 
            "/analisar-documento",
            "/criar-pagamento",
            "/pagamento",
            "/retorno",
            "/status-pagamento/<usuario_id>",
            "/criar-conta",
            "/login"
        ]
    })

# ===== ROTA DE TESTE =====
@app.route('/ping')
def ping():
    return jsonify({"pong": True, "timestamp": datetime.now().isoformat()})

# ===== ROTA PARA ANÁLISE JURÍDICA =====
@app.route('/analisar-documento', methods=['POST'])
def analisar_documento():
    """Recebe um PDF e retorna análise jurídica completa"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"success": False, "error": "Nome de arquivo vazio"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"success": False, "error": "Formato não suportado. Envie PDF."}), 400
        
        # Extrair texto
        texto = extrair_texto_pdf_bytes(file.read())
        
        if not texto:
            return jsonify({"success": False, "error": "Não foi possível extrair texto do PDF"}), 400
        
        # Analisar
        detector = CoreEngineJuridico()
        resultado = detector.analisar_documento_completo(texto)
        
        return jsonify({
            "success": True,
            "resultado": resultado
        })
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ===== ROTA PARA CRIAR PAGAMENTO =====
@app.route('/criar-pagamento', methods=['POST'])
def criar_pagamento():
    """Cria um pagamento no AbacatePay"""
    try:
        # Inicializar cliente AbacatePay
        abacate = get_abacate_client()
        
        if not abacate:
            return jsonify({
                "success": False, 
                "error": "Cliente AbacatePay não inicializado"
            }), 500

        dados = request.json
        print("📦 Dados de pagamento recebidos:", json.dumps(dados, indent=2))
        
        # Extrair dados
        pacote = dados.get('pacote')
        valor = float(dados.get('valor', 0))
        creditos = dados.get('creditos', '30')
        usuario_id = dados.get('usuario_id')
        usuario_email = dados.get('usuario_email')
        usuario_nome = dados.get('usuario_nome', 'Cliente')
        usuario_cpf = dados.get('usuario_cpf', '')
        
        # Validar dados mínimos
        if not all([pacote, usuario_id, usuario_email]):
            return jsonify({"success": False, "error": "Dados incompletos"}), 400
        
        # Mapear pacotes para links fixos
        links_fixos = {
            "bronze": "https://app.abacatepay.com/pay/bill_B1tw5bwKTqXKnUs3jafruP5j",
            "prata": "https://app.abacatepay.com/pay/bill_Stt2u0c3uEkaXsbdPGf6Ks0B",
            "pro": "https://app.abacatepay.com/pay/bill_aMNbQaX2EgyZCdtBKLepWDqr"
        }
        
        # Se temos link fixo, retorna direto
        if pacote in links_fixos:
            url_pagamento = links_fixos[pacote]
            bill_id = f"bill_fixo_{pacote}"
            
            # Salvar cobrança
            salvar_cobranca(
                usuario_id=usuario_id,
                bill_id=bill_id,
                pacote=pacote,
                valor=valor,
                creditos=creditos,
                url=url_pagamento
            )
            
            return jsonify({
                "success": True,
                "url_pagamento": url_pagamento,
                "bill_id": bill_id
            })
        
        # Se não tem link fixo, tenta criar via API
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
            
            return jsonify({
                "success": True,
                "url_pagamento": url_pagamento,
                "bill_id": dados_cobranca.get('id')
            })
        else:
            return jsonify({"success": False, "error": "Erro ao criar pagamento"}), 400
            
    except Exception as e:
        print(f"❌ Erro no pagamento: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ===== ROTA PARA PÁGINA DE PAGAMENTO =====
@app.route('/pagamento')
def pagina_pagamento():
    """Serve a página de pagamento"""
    try:
        # Extrair parâmetros da URL
        pacote = request.args.get('pacote', 'bronze')
        valor = request.args.get('valor', '15')
        creditos = request.args.get('creditos', '30')
        email = request.args.get('email', '')
        
        # Caminho para o arquivo HTML
        html_path = os.path.join(os.path.dirname(__file__), 'pagamento.html')
        
        # Se o arquivo não existir, criar HTML básico
        if not os.path.exists(html_path):
            html_content = f"""
<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Burocrata de Bolso - Pagamento</title>
    <style>
        body {{
            background: #10263D;
            font-family: Arial, sans-serif;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .card {{
            background: #1a3658;
            border-radius: 20px;
            padding: 40px;
            border: 3px solid #F8D96D;
            max-width: 500px;
            width: 100%;
        }}
        h1 {{ color: #F8D96D; text-align: center; }}
        .dados {{ background: #0f2a40; padding: 20px; border-radius: 15px; margin: 20px 0; }}
        .btn {{
            background: linear-gradient(135deg, #F8D96D, #d4b747);
            color: #10263D;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            font-size: 1.2em;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(248, 217, 109, 0.4);
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>⚖️ Finalizar Compra</h1>
        <div class="dados">
            <p><strong>Pacote:</strong> {pacote.capitalize()}</p>
            <p><strong>Valor:</strong> R$ {valor}</p>
            <p><strong>Créditos:</strong> {creditos}</p>
            <p><strong>E-mail:</strong> {email or 'Não informado'}</p>
        </div>
        <button class="btn" onclick="window.location.href='/'">Voltar para Loja</button>
    </div>
</body>
</html>
"""
            return html_content
        
        return send_file(html_path)
        
    except Exception as e:
        return f"Erro: {e}", 500

# ===== ROTA DE RETORNO DO PAGAMENTO =====
@app.route('/retorno')
def retorno_pagamento():
    """Página para onde o usuário volta após o pagamento"""
    status = request.args.get('status', 'pending')
    
    if status == 'PAID' or status == 'approved':
        return """
        <html>
        <head><title>Pagamento Confirmado</title>
        <style>
            body { background: #10263D; color: white; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .card { background: #1a3658; padding: 40px; border-radius: 20px; border: 3px solid #F8D96D; text-align: center; }
            h1 { color: #27AE60; }
            a { color: #F8D96D; text-decoration: none; }
        </style>
        </head>
        <body>
            <div class="card">
                <h1>✅ Pagamento Confirmado!</h1>
                <p>Seus créditos foram adicionados à sua conta.</p>
                <p><a href="/">Voltar para o Burocrata de Bolso</a></p>
            </div>
        </body>
        </html>
        """
    elif status == 'failed':
        return """
        <html>
        <head><title>Pagamento Falhou</title>
        <style>
            body { background: #10263D; color: white; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .card { background: #1a3658; padding: 40px; border-radius: 20px; border: 3px solid #F8D96D; text-align: center; }
            h1 { color: #E74C3C; }
            a { color: #F8D96D; text-decoration: none; }
        </style>
        </head>
        <body>
            <div class="card">
                <h1>❌ Pagamento Falhou</h1>
                <p>Tente novamente ou escolha outra forma de pagamento.</p>
                <p><a href="/">Voltar para Loja</a></p>
            </div>
        </body>
        </html>
        """
    else:
        return """
        <html>
        <head><title>Pagamento Pendente</title>
        <style>
            body { background: #10263D; color: white; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .card { background: #1a3658; padding: 40px; border-radius: 20px; border: 3px solid #F8D96D; text-align: center; }
            h1 { color: #F39C12; }
            a { color: #F8D96D; text-decoration: none; }
        </style>
        </head>
        <body>
            <div class="card">
                <h1>⏳ Pagamento Pendente</h1>
                <p>Aguardando confirmação do pagamento.</p>
                <p><a href="/">Voltar para o Burocrata de Bolso</a></p>
            </div>
        </body>
        </html>
        """

# ===== ROTA DE STATUS DO PAGAMENTO =====
@app.route('/status-pagamento/<string:usuario_id>')
def status_pagamento(usuario_id):
    """Verifica status do usuário"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": True, "burocreditos": 30, "plano": "free_user"})
        
        # Buscar créditos do usuário
        result = conn.run("""
            SELECT COALESCE(s.burocreditos, 0) as burocreditos,
                   array_agg(r.role_name) as plano
            FROM users u
            LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.status = 'active'
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.role_id
            WHERE u.user_id = :user_id
            GROUP BY s.burocreditos
        """, user_id=usuario_id)
        
        conn.close()
        
        if result and len(result) > 0:
            return jsonify({
                "success": True,
                "burocreditos": result[0][0],
                "plano": result[0][1][0] if result[0][1] else 'free_user',
                "provider": "abacatepay"
            })
        else:
            return jsonify({"success": True, "burocreditos": 30, "plano": "free_user"})
            
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        return jsonify({"success": True, "burocreditos": 30, "plano": "free_user"})

# ===== ROTA DE CRIAÇÃO DE CONTA =====
@app.route('/criar-conta', methods=['POST'])
def criar_conta():
    """Cria nova conta de usuário"""
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
            return jsonify({"success": True, "usuario": resultado})
        else:
            return jsonify({"success": False, "error": resultado}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===== ROTA DE LOGIN =====
@app.route('/login', methods=['POST'])
def login():
    """Login de usuário"""
    try:
        dados = request.json
        email = dados.get('email')
        senha = dados.get('senha')
        
        if not email or not senha:
            return jsonify({"success": False, "error": "E-mail e senha obrigatórios"}), 400
        
        sucesso, resultado = autenticar_usuario(email, senha)
        
        if sucesso:
            return jsonify({"success": True, "usuario": resultado})
        else:
            return jsonify({"success": False, "error": resultado}), 401
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===== LISTAR ROTAS =====
print("\n📋 Rotas disponíveis:")
for rule in app.url_map.iter_rules():
    print(f"   {rule}")

# ===== INICIALIZAR SERVIDOR =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('ENV') != 'production'
    
    print(f"\n🚀 Servidor iniciando na porta {port}")
    print(f"🌐 URL base: {APP_URL}")
    print(f"🐘 Driver de banco: pg8000 (compatível com Python 3.14+)")
    print("✅ Pronto para receber requisições!\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
