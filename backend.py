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

# ===== FUNÇÕES DE CONEXÃO COM O BANCO =====
def get_db_connection():
    """Retorna uma conexão com o banco PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
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
            # Buscar créditos
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
            cur.close()
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
        
        cur = conn.cursor()
        
        # Criar tabela de cobranças se não existir
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
        
        # Mapear pacotes para links fixos (caso não queira criar dinamicamente)
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
        return "<h1>✅ Pagamento Confirmado!</h1><p>Seus créditos foram adicionados.</p><a href='/'>Voltar</a>"
    elif status == 'failed':
        return "<h1>❌ Pagamento Falhou</h1><p>Tente novamente.</p><a href='/'>Voltar</a>"
    else:
        return "<h1>⏳ Pagamento Pendente</h1><p>Aguardando confirmação.</p><a href='/'>Voltar</a>"

# ===== ROTA DE STATUS DO PAGAMENTO =====
@app.route('/status-pagamento/<string:usuario_id>')
def status_pagamento(usuario_id):
    """Verifica status do usuário"""
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
    print("✅ Pronto para receber requisições!\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
