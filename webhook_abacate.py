from flask import Flask, request, jsonify
import pg8000
import pg8000.native
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
DATABASE_URL = os.getenv('DATABASE_URL')
WEBHOOK_SECRET = os.getenv('ABACATE_WEBHOOK_SECRET', 'burocrata_webhook_secret_2026')
WEBHOOK_ID = os.getenv('ABACATE_WEBHOOK_ID', 'webh_dev_ahdHbQwGkz4qds2aphSsHWtH')

print("="*50)
print("🚀 WEBHOOK ABACATEPAY INICIANDO")
print("="*50)
print(f"🔗 Webhook ID: {WEBHOOK_ID}")
print(f"📡 Modo: {'Produção' if DATABASE_URL else 'Teste (sem banco)'}")

# ===== FUNÇÃO DE CONEXÃO COM O BANCO (mesma do backend) =====
def get_db_connection():
    """Retorna uma conexão com o banco PostgreSQL usando pg8000"""
    if not DATABASE_URL:
        print("⚠️ DATABASE_URL não configurada - webhook em modo simulação")
        return None
    
    try:
        # Parse da DATABASE_URL
        # Formato: postgres://usuario:senha@host:porta/banco
        if DATABASE_URL.startswith('postgres://'):
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
            print("❌ Formato de DATABASE_URL inválido")
            return None
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None

# ===== FUNÇÃO PARA ATUALIZAR CRÉDITOS DO USUÁRIO =====
def atualizar_creditos_usuario(usuario_id, pacote, creditos):
    """Atualiza os créditos do usuário no banco PostgreSQL"""
    try:
        conn = get_db_connection()
        if not conn:
            print("⚠️ Sem conexão com banco - simulando atualização")
            return True
        
        # Verificar se é a conta especial
        result = conn.run("SELECT email FROM users WHERE user_id = :user_id", user_id=usuario_id)
        if result and len(result) > 0:
            email = result[0][0]
            if email == "pedrohenriquemarques720@gmail.com":
                print("👑 Conta especial detectada - pulando atualização")
                conn.close()
                return True
        
        if pacote == 'pro':
            # Atualizar para plano PRO
            conn.run("""
                UPDATE users 
                SET plano = 'PRO' 
                WHERE user_id = :user_id
            """, user_id=usuario_id)
            
            # Atualizar ou criar subscription com créditos ilimitados
            conn.run("""
                INSERT INTO subscriptions (user_id, plan_id, burocreditos, status)
                VALUES (
                    :user_id, 
                    (SELECT plan_id FROM plans WHERE plan_code = 'pro'), 
                    999999, 
                    'active'
                )
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    burocreditos = 999999,
                    plan_id = (SELECT plan_id FROM plans WHERE plan_code = 'pro'),
                    status = 'active'
            """, user_id=usuario_id)
            
            print(f"🎉 Usuário {usuario_id} atualizado para PRO")
        else:
            # Converter créditos para inteiro
            creditos_int = int(creditos) if creditos != 'ilimitado' else 30
            
            # Atualizar ou criar subscription com créditos adicionais
            conn.run("""
                INSERT INTO subscriptions (user_id, plan_id, burocreditos, status)
                VALUES (
                    :user_id, 
                    (SELECT plan_id FROM plans WHERE plan_code = 'free'), 
                    :creditos, 
                    'active'
                )
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    burocreditos = subscriptions.burocreditos + :creditos,
                    status = 'active'
            """, user_id=usuario_id, creditos=creditos_int)
            
            print(f"💰 {creditos_int} créditos adicionados ao usuário {usuario_id}")
        
        # Registrar no log de auditoria
        conn.run("""
            INSERT INTO audit_logs (user_id, event_type, event_action, resource_type, new_data)
            VALUES (
                :user_id, 
                'credits_added', 
                'webhook', 
                'subscription',
                :new_data
            )
        """, 
            user_id=usuario_id,
            new_data=json.dumps({
                'pacote': pacote,
                'creditos': creditos,
                'data': datetime.now().isoformat()
            })
        )
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar créditos: {e}")
        return False

# ===== FUNÇÃO PARA REGISTRAR PAGAMENTO =====
def registrar_pagamento(bill_id, usuario_id, pacote, creditos, status='PAID'):
    """Registra o pagamento na tabela de cobranças"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        # Criar tabela se não existir (já deve existir, mas garantimos)
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
        
        # Atualizar status da cobrança
        conn.run("""
            UPDATE cobrancas_abacate 
            SET status = :status, data_pagamento = CURRENT_TIMESTAMP
            WHERE bill_id = :bill_id
        """, status=status, bill_id=bill_id)
        
        conn.close()
        print(f"✅ Pagamento registrado: {bill_id}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao registrar pagamento: {e}")
        return False

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
        print("\n" + "="*50)
        print("📩 WEBHOOK RECEBIDO")
        print("="*50)
        print(json.dumps(payload, indent=2))
        
        # O AbacatePay envia os dados dentro de 'data'
        data = payload.get('data', {})
        event = payload.get('event', 'billing.paid')
        status = data.get('status')
        
        # Processa apenas pagamentos confirmados
        if status == 'PAID' or event == 'billing.paid':
            print("\n💰 PAGAMENTO CONFIRMADO!")
            
            # Pega informações do cliente
            customer = data.get('customer', {})
            email = customer.get('email')
            
            # Pega metadata (informações que enviamos na criação)
            metadata = data.get('metadata', {})
            usuario_id = metadata.get('usuario_id')
            pacote = metadata.get('pacote', 'bronze')
            creditos = metadata.get('creditos', '30')
            
            # Também pode vir do ID da cobrança
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
            
            # Se temos email ou usuario_id, processa no banco
            if email or usuario_id:
                conn = get_db_connection()
                if conn:
                    # Se não temos usuario_id, busca pelo email
                    if not usuario_id and email:
                        result = conn.run("SELECT user_id FROM users WHERE email = :email", email=email)
                        if result and len(result) > 0:
                            usuario_id = result[0][0]
                            print(f"👤 Usuário encontrado por email: {usuario_id}")
                    
                    if usuario_id:
                        # Registrar pagamento
                        registrar_pagamento(bill_id, usuario_id, pacote, creditos)
                        
                        # Atualizar créditos
                        atualizar_creditos_usuario(usuario_id, pacote, creditos)
                        
                        conn.close()
                    else:
                        print(f"⚠️ Usuário não encontrado para email: {email}")
                        if conn:
                            conn.close()
                else:
                    # Modo simulação
                    print(f"\n🔧 MODO SIMULAÇÃO - Pagamento processado:")
                    print(f"   Usuário: {usuario_id or email}")
                    print(f"   Pacote: {pacote}")
                    print(f"   Créditos: {creditos}")
            
            return jsonify({"status": "success"}), 200
        
        # Outros eventos (disputed, withdraw.done, withdraw.failed)
        print(f"\nℹ️ Evento ignorado: {event} / Status: {status}")
        return jsonify({"status": "ignored"}), 200
        
    except Exception as e:
        print(f"\n❌ Erro no webhook AbacatePay: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/webhook/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok", 
        "service": "AbacatePay Webhook",
        "webhook_id": WEBHOOK_ID,
        "database_connected": bool(DATABASE_URL),
        "url": "https://burocratadebolso.com.br/webhook/abacate"
    }), 200

@app.route('/webhook/test', methods=['POST'])
def test_webhook():
    """Rota para testar o webhook manualmente"""
    try:
        payload = request.json
        print("\n🧪 TESTE MANUAL:")
        print(json.dumps(payload, indent=2))
        
        # Simular processamento
        data = payload.get('data', {})
        status = data.get('status')
        
        if status == 'PAID':
            print("💰 Simulando processamento de pagamento...")
            
            metadata = data.get('metadata', {})
            usuario_id = metadata.get('usuario_id', 'teste-123')
            pacote = metadata.get('pacote', 'bronze')
            creditos = metadata.get('creditos', '30')
            
            print(f"   Usuário: {usuario_id}")
            print(f"   Pacote: {pacote}")
            print(f"   Créditos: {creditos}")
            print("✅ Processamento simulado com sucesso!")
        
        return jsonify({"status": "test_ok", "received": payload}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('WEBHOOK_PORT', 5001))
    print(f"\n🚀 Webhook AbacatePay rodando na porta {port}")
    print(f"🔗 URL: https://burocratadebolso.com.br/webhook/abacate")
    print(f"🆔 ID: {WEBHOOK_ID}")
    print("\n📋 Rotas disponíveis:")
    print("   /webhook/abacate - POST (receber notificações)")
    print("   /webhook/health - GET (health check)")
    print("   /webhook/test - POST (teste manual)")
    print("\n✅ Pronto para receber notificações!\n")
    app.run(host='0.0.0.0', port=port, debug=True)
