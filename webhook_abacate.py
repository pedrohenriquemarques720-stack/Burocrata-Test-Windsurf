from flask import Flask, request, jsonify
import sqlite3
import os
import json
import hmac
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configurações
DB_PATH = os.getenv('DATABASE_PATH', 'utilizadores_burocrata.db')
WEBHOOK_SECRET = os.getenv('ABACATE_WEBHOOK_SECRET', 'burocrata_webhook_secret_2026')
WEBHOOK_ID = os.getenv('ABACATE_WEBHOOK_ID', 'webh_dev_ahdHbQwGkz4qds2aphSsHWtH')

def validar_assinatura(payload, signature, secret):
    """Valida a assinatura do webhook"""
    if not signature or not secret:
        return True  # Pular validação se não configurado
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

@app.route('/webhook/abacate', methods=['POST'])
def webhook_abacate():
    """
    Recebe notificações de pagamento do AbacatePay
    URL: https://burocratadebolso.com.br/webhook/abacate
    Webhook ID: webh_dev_ahdHbQwGkz4qds2aphSsHWtH
    """
    try:
        # Pegar assinatura do header (se o AbacatePay enviar)
        signature = request.headers.get('X-Signature', '')
        
        # Validar assinatura
        if not validar_assinatura(request.data, signature, WEBHOOK_SECRET):
            print("❌ Assinatura inválida")
            return jsonify({"error": "Invalid signature"}), 401
        
        # Recebe o payload
        payload = request.json
        print("📩 Webhook AbacatePay recebido:", json.dumps(payload, indent=2))
        print(f"🔍 Webhook ID: {WEBHOOK_ID}")
        
        # O AbacatePay envia os dados dentro de 'data'
        data = payload.get('data', {})
        event = payload.get('event', 'billing.paid')
        status = data.get('status')
        
        # Processa apenas pagamentos confirmados
        if status == 'PAID' or event == 'billing.paid':
            print("💰 Pagamento confirmado recebido!")
            
            # Pega informações do cliente
            customer = data.get('customer', {})
            email = customer.get('email')
            
            # Pega metadata (informações que enviamos na criação)
            metadata = data.get('metadata', {})
            usuario_id = metadata.get('usuario_id')
            pacote = metadata.get('pacote', 'bronze')
            creditos = metadata.get('creditos', '30')
            
            # Também pode vir do ID da cobrança (se não tiver metadata)
            bill_id = data.get('id')
            
            print(f"📧 Email: {email}")
            print(f"👤 Usuário ID: {usuario_id}")
            print(f"📦 Pacote: {pacote}")
            print(f"💰 Créditos: {creditos}")
            print(f"🆔 Bill ID: {bill_id}")
            
            # Mapeia bill_id para pacote (fallback)
            pacote_por_bill = {
                "bill_B1tw5bwKTqXKnUs3jafruP5j": "bronze",
                "bill_Stt2u0c3uEkaXsbdPGf6Ks0B": "prata",
                "bill_aMNbQaX2EgyZCdtBKLepWDqr": "pro"
            }
            
            if (not pacote or pacote == 'bronze') and bill_id in pacote_por_bill:
                pacote = pacote_por_bill[bill_id]
                # Define créditos baseado no pacote
                creditos_por_pacote = {
                    "bronze": 30,
                    "prata": 60,
                    "pro": "ilimitado"
                }
                creditos = creditos_por_pacote.get(pacote, 30)
                print(f"📦 Pacote mapeado por bill_id: {pacote} com {creditos} créditos")
            
            # Se temos email, podemos buscar usuário no banco
            if email or usuario_id:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                
                # Criar tabela de pagamentos se não existir
                c.execute('''
                    CREATE TABLE IF NOT EXISTS pagamentos_abacate (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bill_id TEXT UNIQUE,
                        usuario_id INTEGER,
                        pacote TEXT,
                        creditos TEXT,
                        valor REAL,
                        status TEXT,
                        data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Se não temos usuario_id, busca pelo email
                if not usuario_id and email:
                    c.execute("SELECT id FROM utilizadores WHERE email = ?", (email,))
                    result = c.fetchone()
                    if result:
                        usuario_id = result[0]
                        print(f"👤 Usuário encontrado por email: ID {usuario_id}")
                
                if usuario_id:
                    # Registrar pagamento
                    c.execute('''
                        INSERT OR IGNORE INTO pagamentos_abacate 
                        (bill_id, usuario_id, pacote, creditos, status)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (bill_id, usuario_id, pacote, str(creditos), 'PAID'))
                    
                    # Atualizar créditos do usuário
                    if pacote == 'pro':
                        c.execute('''
                            UPDATE utilizadores 
                            SET plano = 'PRO', burocreditos = 999999 
                            WHERE id = ?
                        ''', (usuario_id,))
                        print(f"🎉 Usuário {usuario_id} atualizado para PRO via AbacatePay")
                    else:
                        # Converte creditos para inteiro
                        creditos_int = int(creditos) if creditos != 'ilimitado' else 30
                        c.execute('''
                            UPDATE utilizadores 
                            SET burocreditos = burocreditos + ? 
                            WHERE id = ?
                        ''', (creditos_int, usuario_id))
                        print(f"💰 {creditos_int} créditos adicionados ao usuário {usuario_id}")
                    
                    conn.commit()
                    print(f"✅ Pagamento AbacatePay processado: {bill_id}")
                else:
                    print(f"⚠️ Usuário não encontrado para email: {email}")
                
                conn.close()
            
            return jsonify({"status": "success"}), 200
        
        # Outros eventos (disputed, withdraw.done, withdraw.failed)
        print(f"ℹ️ Evento ignorado: {event} / Status: {status}")
        return jsonify({"status": "ignored"}), 200
        
    except Exception as e:
        print(f"❌ Erro no webhook AbacatePay: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/webhook/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok", 
        "service": "AbacatePay Webhook",
        "webhook_id": WEBHOOK_ID,
        "url": "https://burocratadebolso.com.br/webhook/abacate"
    }), 200

@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """Rota para testar o webhook manualmente"""
    try:
        payload = request.json
        print("🧪 Teste manual:", json.dumps(payload, indent=2))
        return jsonify({"status": "test_ok", "received": payload}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', 5001))
    print(f"🚀 Webhook AbacatePay rodando na porta {port}")
    print(f"🔗 URL: https://burocratadebolso.com.br/webhook/abacate")
    print(f"🆔 ID: {WEBHOOK_ID}")
    app.run(host='0.0.0.0', port=port, debug=True)