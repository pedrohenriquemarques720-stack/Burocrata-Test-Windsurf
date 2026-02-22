from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import sqlite3
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Importar cliente AbacatePay
from abacatepay import get_abacate_client

app = Flask(__name__)
CORS(app)

# Configurações - usando variáveis de ambiente
ABACATE_API_KEY = os.getenv('ABACATE_API_KEY', 'abc_dev_apB2fqGwQFb0bPsUBGmAuHeC')
ABACATE_WEBHOOK_ID = os.getenv('ABACATE_WEBHOOK_ID', 'webh_dev_ahdHbQwGKz4qds2aphSsHWtH')
DB_PATH = os.getenv('DATABASE_PATH', 'utilizadores_burocrata.db')
APP_URL = os.getenv('APP_URL', 'https://burocratadebolso.com.br')

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

# ===== ROTA PRINCIPAL =====
@app.route('/')
def index():
    return jsonify({
        "status": "API Burocrata de Bolso funcionando!",
        "payment": "AbacatePay integrado",
        "webhook_id": ABACATE_WEBHOOK_ID,
        "webhook_url": f"{APP_URL}/webhook/abacate",
        "api_key_configured": bool(ABACATE_API_KEY)
    })

# ===== ROTA PARA CRIAR PAGAMENTO (ABACATEPAY) =====
@app.route('/criar-pagamento', methods=['POST'])
def criar_pagamento():
    """Cria um pagamento no AbacatePay"""
    try:
        # Verificar se o cliente AbacatePay está inicializado
        if not abacate:
            return jsonify({
                "success": False, 
                "error": "Cliente AbacatePay não inicializado. Verifique a chave da API."
            }), 500

        dados = request.json
        print("📦 Dados recebidos:", json.dumps(dados, indent=2))
        
        # Dados do produto
        pacote = dados.get('pacote')
        valor = float(dados.get('valor'))
        creditos = dados.get('creditos')
        usuario_id = dados.get('usuario_id')
        usuario_email = dados.get('usuario_email')
        usuario_nome = dados.get('usuario_nome', 'Cliente')
        usuario_cpf = dados.get('usuario_cpf', '')  # CPF opcional
        
        # Validar dados
        if not all([pacote, valor, usuario_id, usuario_email]):
            return jsonify({"success": False, "error": "Dados incompletos"}), 400
        
        print(f"💳 Criando pagamento para {usuario_email} - Pacote: {pacote}")
        
        # Criar pagamento no AbacatePay
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
            # Salvar no banco
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

# ===== ROTA PARA PÁGINA DE PAGAMENTO =====
@app.route('/pagamento')
def pagina_pagamento():
    """Serve a página de pagamento"""
    try:
        # Pega parâmetros da URL
        pacote = request.args.get('pacote', 'bronze')
        valor = request.args.get('valor', '15')
        creditos = request.args.get('creditos', '30')
        email = request.args.get('email', '')
        
        # Caminho para o arquivo HTML
        html_path = os.path.join(os.path.dirname(__file__), 'pagamento.html')
        
        # Se o arquivo não existir, cria um HTML básico
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
            
            // Pegar usuário do sessionStorage (se existir)
            let usuario_id = 1;
            let usuario_nome = 'Cliente';
            try {{
                const usuarioLogado = sessionStorage.getItem('usuarioLogado');
                if (usuarioLogado) {{
                    const user = JSON.parse(usuarioLogado);
                    usuario_id = user.id || 1;
                    usuario_nome = user.nome || 'Cliente';
                }}
            }} catch(e) {{}}
            
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
        
        # Se o arquivo existe, serve ele
        return send_file(html_path)
        
    except Exception as e:
        print(f"❌ Erro ao servir página de pagamento: {e}")
        return f"Erro: {e}", 500

# ===== ROTA DE RETORNO (APÓS PAGAMENTO) =====
@app.route('/retorno')
def retorno_pagamento():
    """Página para onde o usuário volta após o pagamento"""
    # Pega parâmetros da URL
    bill_id = request.args.get('bill_id')
    status = request.args.get('status', 'pending')
    
    print(f"🔄 Retorno de pagamento: bill_id={bill_id}, status={status}")
    
    if status == 'PAID' or status == 'approved':
        return render_template('sucesso.html')
    elif status == 'failed':
        return render_template('falha.html')
    else:
        return render_template('pendente.html')

# ===== ROTA PARA VERIFICAR STATUS (POLLING) =====
@app.route('/status-pagamento/<int:usuario_id>')
def status_pagamento(usuario_id):
    """Verifica se o usuário tem créditos atualizados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Criar tabela de cobranças se não existir
        c.execute('''
            CREATE TABLE IF NOT EXISTS cobrancas_abacate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id TEXT UNIQUE,
                usuario_id INTEGER,
                pacote TEXT,
                valor REAL,
                creditos TEXT,
                url_pagamento TEXT,
                status TEXT DEFAULT 'PENDENTE',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_pagamento TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES utilizadores (id)
            )
        ''')
        
        # Buscar créditos do usuário
        c.execute('''
            SELECT burocreditos, plano FROM utilizadores WHERE id = ?
        ''', (usuario_id,))
        
        resultado = c.fetchone()
        conn.close()
        
        if resultado:
            return jsonify({
                "success": True,
                "burocreditos": resultado[0],
                "plano": resultado[1],
                "provider": "abacatepay"
            })
        else:
            return jsonify({"success": False}), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===== FUNÇÕES AUXILIARES =====
def salvar_cobranca(usuario_id, bill_id, pacote, valor, creditos, url):
    """Salva cobrança no banco de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Criar tabela se não existir
        c.execute('''
            CREATE TABLE IF NOT EXISTS cobrancas_abacate (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id TEXT UNIQUE,
                usuario_id INTEGER,
                pacote TEXT,
                valor REAL,
                creditos TEXT,
                url_pagamento TEXT,
                status TEXT DEFAULT 'PENDENTE',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_pagamento TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES utilizadores (id)
            )
        ''')
        
        c.execute('''
            INSERT OR IGNORE INTO cobrancas_abacate 
            (bill_id, usuario_id, pacote, valor, creditos, url_pagamento)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (bill_id, usuario_id, pacote, valor, str(creditos), url))
        
        conn.commit()
        conn.close()
        print(f"💾 Cobrança salva: {bill_id}")
        
    except Exception as e:
        print("❌ Erro ao salvar cobrança:", e)

# ===== ROTA DE TESTE =====
@app.route('/teste-abacate')
def teste_abacate():
    """Rota para testar a integração"""
    return jsonify({
        "status": "AbacatePay integrado",
        "api_key_configured": bool(ABACATE_API_KEY),
        "webhook_id": ABACATE_WEBHOOK_ID,
        "webhook_url": f"{APP_URL}/webhook/abacate"
    })

# ===== NO FINAL DO ARQUIVO =====
if __name__ == '__main__':
    # Render define a porta automaticamente na variável PORT
    port = int(os.environ.get('PORT', 5000))
    
    # Em produção, debug=False é importante
    debug_mode = os.environ.get('ENV') != 'production'
    
    print("🚀 Servidor Burocrata iniciando...")
    print(f"🔗 Webhook configurado: {APP_URL}/webhook/abacate")
    print(f"🆔 Webhook ID: {ABACATE_WEBHOOK_ID}")
    print(f"🔑 API Key: {'Configurada' if ABACATE_API_KEY else 'NÃO CONFIGURADA'}")
    print(f"🌐 Modo: {'Produção' if not debug_mode else 'Desenvolvimento'}")
    print(f"📡 Porta: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
