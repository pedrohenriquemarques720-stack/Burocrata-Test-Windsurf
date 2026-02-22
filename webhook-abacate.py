from flask import Flask, request, jsonify
import sqlite3
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DB_PATH = os.getenv('DATABASE_PATH', 'utilizadores_burocrata.db')

@app.route('/webhook/abacate', methods=['POST'])
def webhook_abacate():
    """
    Recebe notificações de pagamento do AbacatePay
    O AbacatePay envia POST para esta URL quando o pagamento é confirmado
    """
    try:
        # Recebe o payload
        payload = request.json
        print("📩 Webhook AbacatePay recebido:", json.dumps(payload, indent=2))
        
        # O AbacatePay envia os dados dentro de 'data'
        data = payload.get('data', {})
        status = data.get('status')
        
        # Processa apenas pagamentos confirmados
        if status == 'PAID':
            # Pega informações do cliente
            customer = data.get('customer', {})
            email = customer.get('email')
            
            # Pega metadata (informações que enviamos na criação)
            metadata = data.get('metadata', {})
            usuario_id = metadata.get('usuario_id')
            pacote = metadata.get('pacote', 'bronze')
            creditos = metadata.get('creditos', 30)
            
            # Também pode vir do ID da cobrança (se não tiver metadata)
            bill_id = data.get('id')
            
            # Mapeia bill_id para pacote (fallback)
            pacote_por_bill = {
                "bill_B1tw5bwKTqXKnUs3jafruP5j": "bronze",
                "bill_Stt2u0c3uEkaXsbdPGf6Ks0B": "prata",
                "bill_aMNbQaX2EgyZCdtBKLepWDqr": "pro"
            }
            
            if not pacote and bill_id in pacote_por_bill:
                pacote = pacote_por_bill[bill_id]
                # Define créditos baseado no pacote
                creditos_por_pacote = {
                    "bronze": 30,
                    "prata": 60,
                    "pro": "ilimitado"
                }
                creditos = creditos_por_pacote.get(pacote, 30)
            
            # Se temos email, podemos buscar usuário no banco
            if email or usuario_id:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                
                # Se não temos usuario_id, busca pelo email
                if not usuario_id and email:
                    c.execute("SELECT id FROM utilizadores WHERE email = ?", (email,))
                    result = c.fetchone()
                    if result:
                        usuario_id = result[0]
                
                if usuario_id:
                    # Registrar pagamento
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
                    
                    # Inserir registro do pagamento
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
                
                conn.close()
            
            return jsonify({"status": "success"}), 200
        
        return jsonify({"status": "ignored"}), 200
        
    except Exception as e:
        print(f"❌ Erro no webhook AbacatePay: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "AbacatePay Webhook"}), 200

if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', 5001))
    print(f"🚀 Webhook AbacatePay rodando na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=True)