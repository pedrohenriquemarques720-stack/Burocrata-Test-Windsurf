from flask import Flask, request, jsonify
import mercadopago
import sqlite3
import json

app = Flask(__name__)

# Configuração do Mercado Pago
# IMPORTANTE: Use suas credenciais reais
ACCESS_TOKEN = "APP_USR-12345678-1234-1234-1234-123456789012"  # Token de produção
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Configurações
DB_PATH = 'utilizadores_burocrata.db'
URL_BASE = "https://seudominio.com"  # Substitua pelo seu domínio

@app.route('/api/criar-preferencia', methods=['POST'])
def criar_preferencia():
    """Cria uma preferência de pagamento no Mercado Pago"""
    try:
        dados = request.json
        
        # Dados do comprador
        usuario_id = dados.get('usuario_id')
        usuario_email = dados.get('usuario_email')
        
        # Buscar dados do usuário no banco
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT nome FROM utilizadores WHERE id = ?", (usuario_id,))
        resultado = c.fetchone()
        nome_usuario = resultado[0] if resultado else "Cliente"
        conn.close()
        
        # Criar itens da preferência
        items = []
        
        if dados.get('pacote') == 'pro':
            # Assinatura PRO
            items.append({
                "title": "Plano PRO Burocrata",
                "description": "Acesso ilimitado a análises de documentos",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(dados.get('preco', 80))
            })
            
            # Configuração de assinatura
            preapproval_data = {
                "payer_email": usuario_email,
                "back_url": f"{URL_BASE}/sucesso.html",
                "reason": "Plano PRO Burocrata",
                "external_reference": f"user_{usuario_id}_pro",
                "auto_recurring": {
                    "frequency": 1,
                    "frequency_type": "months",
                    "transaction_amount": float(dados.get('preco', 80)),
                    "currency_id": "BRL"
                }
            }
            
            # Criar assinatura
            preapproval = sdk.preapproval().create(preapproval_data)
            
            if preapproval["status"] == 201:
                return jsonify({
                    "preference_id": preapproval["response"]["id"],
                    "init_point": preapproval["response"]["init_point"]
                })
            else:
                return jsonify({"error": "Erro ao criar assinatura"}), 400
        
        else:
            # Pagamento único
            items.append({
                "title": f"Pacote {dados.get('pacote', '').title()}",
                "description": f"{dados.get('creditos', 0)} BuroCréditos",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(dados.get('preco', 0))
            })
            
            # Dados do comprador
            payer = {
                "name": nome_usuario.split()[0] if nome_usuario else "Cliente",
                "surname": " ".join(nome_usuario.split()[1:]) if nome_usuario and len(nome_usuario.split()) > 1 else "",
                "email": usuario_email
            }
            
            # URLs de retorno
            back_urls = {
                "success": f"{URL_BASE}/sucesso.html",
                "failure": f"{URL_BASE}/falha.html",
                "pending": f"{URL_BASE}/pendente.html"
            }
            
            # Criar preferência
            preference_data = {
                "items": items,
                "payer": payer,
                "back_urls": back_urls,
                "auto_return": "approved",
                "external_reference": f"user_{usuario_id}_{dados.get('pacote')}_{dados.get('creditos')}",
                "statement_descriptor": "BUROCRATA DE BOLSO"
            }
            
            preference = sdk.preference().create(preference_data)
            
            if preference["status"] == 201:
                # Salvar preferência no banco (opcional)
                salvar_preferencia(usuario_id, preference["response"]["id"], dados)
                
                return jsonify({
                    "preference_id": preference["response"]["id"],
                    "init_point": preference["response"]["init_point"],
                    "sandbox_init_point": preference["response"]["sandbox_init_point"]
                })
            else:
                return jsonify({"error": "Erro ao criar preferência"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/webhook', methods=['POST'])
def webhook():
    """Webhook para receber notificações de pagamento"""
    try:
        data = request.json
        print("Webhook recebido:", data)
        
        # Verificar tipo de notificação
        if data.get("type") == "payment":
            payment_id = data.get("data", {}).get("id")
            
            # Buscar detalhes do pagamento
            payment_info = sdk.payment().get(payment_id)
            
            if payment_info["status"] == 200:
                payment = payment_info["response"]
                
                # Processar pagamento
                external_ref = payment.get("external_reference", "")
                
                if external_ref.startswith("user_"):
                    partes = external_ref.split("_")
                    usuario_id = partes[1]
                    pacote = partes[2] if len(partes) > 2 else None
                    creditos = partes[3] if len(partes) > 3 else None
                    
                    if payment["status"] == "approved":
                        # Adicionar créditos ao usuário
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        
                        if pacote == "pro":
                            # Atualizar para PRO
                            c.execute("""
                                UPDATE utilizadores 
                                SET plano = 'PRO', burocreditos = 999999 
                                WHERE id = ?
                            """, (usuario_id,))
                        else:
                            # Adicionar créditos
                            c.execute("""
                                UPDATE utilizadores 
                                SET burocreditos = burocreditos + ? 
                                WHERE id = ?
                            """, (creditos, usuario_id))
                        
                        conn.commit()
                        conn.close()
                        
                        print(f"Créditos adicionados para usuário {usuario_id}")
        
        return jsonify({"status": "ok"}), 200
    
    except Exception as e:
        print("Erro no webhook:", str(e))
        return jsonify({"error": str(e)}), 500

def salvar_preferencia(usuario_id, preference_id, dados):
    """Salva preferência de pagamento no banco"""
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
                FOREIGN KEY (usuario_id) REFERENCES utilizadores (id)
            )
        ''')
        
        c.execute('''
            INSERT INTO pagamentos (usuario_id, preference_id, pacote, valor, creditos)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario_id, preference_id, dados.get('pacote'), dados.get('preco'), dados.get('creditos')))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print("Erro ao salvar preferência:", e)

if __name__ == '__main__':
    app.run(debug=True, port=5000)