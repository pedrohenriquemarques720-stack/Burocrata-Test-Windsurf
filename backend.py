from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mercadopago
import sqlite3
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)  # Permite requisições do seu frontend

# Configurações
ACCESS_TOKEN = os.getenv('MERCADO_PAGO_ACCESS_TOKEN')
DB_PATH = os.getenv('DATABASE_PATH', 'utilizadores_burocrata.db')
APP_URL = os.getenv('APP_URL', 'http://localhost:5000')

# Inicializar SDK do Mercado Pago
sdk = mercadopago.SDK(ACCESS_TOKEN)

# ===== ROTA PRINCIPAL =====
@app.route('/')
def index():
    return jsonify({"status": "API do Mercado Pago funcionando!"})

# ===== ROTA PARA CRIAR PREFERÊNCIA DE PAGAMENTO =====
@app.route('/criar-preferencia', methods=['POST'])
def criar_preferencia():
    """Cria uma preferência de pagamento no Mercado Pago"""
    try:
        dados = request.json
        print("📦 Dados recebidos:", dados)
        
        # Dados do produto
        pacote = dados.get('pacote')
        valor = float(dados.get('valor'))
        creditos = dados.get('creditos')
        usuario_id = dados.get('usuario_id')
        usuario_email = dados.get('usuario_email')
        usuario_nome = dados.get('usuario_nome', 'Cliente')
        
        # Nome do pacote
        nomes_pacote = {
            'bronze': 'Pacote Bronze',
            'prata': 'Pacote Prata',
            'pro': 'Plano PRO'
        }
        
        # Descrição do produto
        if pacote == 'pro':
            titulo = 'Plano PRO Burocrata'
            descricao = 'Acesso ilimitado a análises de documentos'
        else:
            titulo = f'Pacote {nomes_pacote[pacote]}'
            descricao = f'{creditos} BuroCréditos para análises'
        
        # Criar preferência
        preference_data = {
            "items": [
                {
                    "title": titulo,
                    "description": descricao,
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": valor
                }
            ],
            "payer": {
                "name": usuario_nome.split()[0] if usuario_nome else "Cliente",
                "email": usuario_email
            },
            "back_urls": {
                "success": f"{APP_URL}/sucesso",
                "failure": f"{APP_URL}/falha",
                "pending": f"{APP_URL}/pendente"
            },
            "auto_return": "approved",
            "external_reference": str(usuario_id),
            "notification_url": f"{APP_URL}/webhook",  # Webhook para notificações
            "statement_descriptor": "BUROCRATA DE BOLSO"
        }
        
        # Enviar para o Mercado Pago
        preference_response = sdk.preference().create(preference_data)
        
        if preference_response["status"] == 201:
            preference = preference_response["response"]
            
            # Salvar preferência no banco
            salvar_preferencia(
                usuario_id=usuario_id,
                preference_id=preference["id"],
                pacote=pacote,
                valor=valor,
                creditos=creditos
            )
            
            print("✅ Preferência criada:", preference["id"])
            
            return jsonify({
                "success": True,
                "preference_id": preference["id"],
                "init_point": preference["init_point"],
                "sandbox_init_point": preference.get("sandbox_init_point")
            })
        else:
            print("❌ Erro ao criar preferência:", preference_response)
            return jsonify({"success": False, "error": "Erro ao criar preferência"}), 400
            
    except Exception as e:
        print("❌ Erro:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

# ===== WEBHOOK PARA NOTIFICAÇÕES DE PAGAMENTO =====
@app.route('/webhook', methods=['POST'])
def webhook():
    """Recebe notificações de pagamento do Mercado Pago"""
    try:
        data = request.json
        print("🔔 Webhook recebido:", data)
        
        # Verificar tipo de notificação
        if data.get("type") == "payment":
            payment_id = data.get("data", {}).get("id")
            
            if payment_id:
                # Buscar detalhes do pagamento
                payment_info = sdk.payment().get(payment_id)
                
                if payment_info["status"] == 200:
                    payment = payment_info["response"]
                    
                    # Processar pagamento aprovado
                    if payment["status"] == "approved":
                        processar_pagamento_aprovado(payment)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print("❌ Erro no webhook:", str(e))
        return jsonify({"error": str(e)}), 500

# ===== ROTAS DE RETORNO (após pagamento) =====
@app.route('/sucesso')
def pagamento_sucesso():
    """Página de sucesso após pagamento"""
    payment_id = request.args.get('payment_id')
    status = request.args.get('status')
    external_ref = request.args.get('external_reference')
    
    # Buscar informações do pagamento
    if payment_id:
        payment_info = sdk.payment().get(payment_id)
        if payment_info["status"] == 200:
            payment = payment_info["response"]
            processar_pagamento_aprovado(payment)
    
    return render_template('sucesso.html')  # Opcional

@app.route('/falha')
def pagamento_falha():
    return render_template('falha.html')

@app.route('/pendente')
def pagamento_pendente():
    return render_template('pendente.html')

# ===== FUNÇÕES AUXILIARES =====
def salvar_preferencia(usuario_id, preference_id, pacote, valor, creditos):
    """Salva a preferência de pagamento no banco"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Criar tabela se não existir
        c.execute('''
            CREATE TABLE IF NOT EXISTS pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                preference_id TEXT UNIQUE,
                pacote TEXT,
                valor REAL,
                creditos TEXT,
                status TEXT DEFAULT 'PENDENTE',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_pagamento TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES utilizadores (id)
            )
        ''')
        
        c.execute('''
            INSERT INTO pagamentos (usuario_id, preference_id, pacote, valor, creditos)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario_id, preference_id, pacote, valor, creditos))
        
        conn.commit()
        conn.close()
        print(f"💾 Preferência salva: {preference_id}")
        
    except Exception as e:
        print("❌ Erro ao salvar preferência:", e)

def processar_pagamento_aprovado(payment):
    """Processa um pagamento aprovado"""
    try:
        # Pegar ID do usuário do external_reference
        usuario_id = payment.get("external_reference")
        if not usuario_id:
            return
        
        # Buscar preferência original
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT pacote, creditos FROM pagamentos 
            WHERE usuario_id = ? AND status = 'PENDENTE'
            ORDER BY data_criacao DESC LIMIT 1
        ''', (usuario_id,))
        
        pagamento = c.fetchone()
        
        if pagamento:
            pacote, creditos = pagamento
            
            # Atualizar status do pagamento
            c.execute('''
                UPDATE pagamentos 
                SET status = 'APROVADO', data_pagamento = CURRENT_TIMESTAMP
                WHERE usuario_id = ? AND status = 'PENDENTE'
            ''', (usuario_id,))
            
            # Adicionar créditos ao usuário
            if pacote == 'pro':
                c.execute('''
                    UPDATE utilizadores 
                    SET plano = 'PRO', burocreditos = 999999 
                    WHERE id = ?
                ''', (usuario_id,))
                print(f"🎉 Usuário {usuario_id} atualizado para PRO")
            else:
                c.execute('''
                    UPDATE utilizadores 
                    SET burocreditos = burocreditos + ? 
                    WHERE id = ?
                ''', (creditos, usuario_id))
                print(f"💰 {creditos} créditos adicionados ao usuário {usuario_id}")
            
            conn.commit()
            print(f"✅ Pagamento processado para usuário {usuario_id}")
        
        conn.close()
        
    except Exception as e:
        print("❌ Erro ao processar pagamento:", e)

# ===== ROTA PARA VERIFICAR STATUS (usada pelo frontend) =====
@app.route('/status-pagamento/<int:usuario_id>')
def status_pagamento(usuario_id):
    """Verifica se o usuário tem créditos atualizados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT burocreditos, plano FROM utilizadores WHERE id = ?
        ''', (usuario_id,))
        
        resultado = c.fetchone()
        conn.close()
        
        if resultado:
            return jsonify({
                "success": True,
                "burocreditos": resultado[0],
                "plano": resultado[1]
            })
        else:
            return jsonify({"success": False}), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Servidor iniciado em http://localhost:5000")
    app.run(debug=True, port=5000)