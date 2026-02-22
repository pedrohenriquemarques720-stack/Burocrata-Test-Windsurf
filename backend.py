from flask import Flask, request, jsonify, render_template
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

# Configurações
ABACATE_API_KEY = os.getenv('ABACATE_API_KEY')
ABACATE_WEBHOOK_ID = os.getenv('ABACATE_WEBHOOK_ID')
DB_PATH = os.getenv('DATABASE_PATH', 'utilizadores_burocrata.db')
APP_URL = os.getenv('APP_URL', 'https://burocratadebolso.com.br')

# Inicializar cliente AbacatePay
abacate = get_abacate_client()

print(f"🚀 Backend iniciado com webhook ID: {ABACATE_WEBHOOK_ID}")

# ===== ROTA PRINCIPAL =====
@app.route('/')
def index():
    return jsonify({
        "status": "API Burocrata de Bolso funcionando!",
        "payment": "AbacatePay integrado",
        "webhook_id": ABACATE_WEBHOOK_ID,
        "webhook_url": f"{APP_URL}/webhook/abacate"
    })

# ===== ROTA PARA CRIAR PAGAMENTO (ABACATEPAY) =====
@app.route('/criar-pagamento', methods=['POST'])
def criar_pagamento():
    """Cria um pagamento no AbacatePay"""
    try:
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

if __name__ == '__main__':
    print("🚀 Servidor Burocrata rodando na porta 5000")
    print(f"🔗 Webhook configurado: {APP_URL}/webhook/abacate")
    print(f"🆔 Webhook ID: {ABACATE_WEBHOOK_ID}")
    print("📌 Lembre-se de rodar também: python webhook_abacate.py (porta 5001)")
    app.run(debug=True, port=5000)
