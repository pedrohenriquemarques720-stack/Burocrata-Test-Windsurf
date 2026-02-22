import hmac
import hashlib

@app.route('/webhook/abacate', methods=['POST'])
def webhook_abacate():
    """
    Recebe notificações de pagamento do AbacatePay
    """
    try:
        # VERIFICAR SECRET (se o AbacatePay enviar no header)
        # signature = request.headers.get('X-Signature')
        # secret = os.getenv('ABACATE_WEBHOOK_SECRET')
        # if not validar_assinatura(request.data, signature, secret):
        #     return jsonify({"error": "Invalid signature"}), 401
        
        payload = request.json
        print("📩 Webhook AbacatePay recebido:", json.dumps(payload, indent=2))
        
        # O AbacatePay envia os dados dentro de 'data'
        data = payload.get('data', {})
        event = payload.get('event')  # Pode vir o evento também
        status = data.get('status')
        
        # Processa apenas pagamentos confirmados
        if status == 'PAID' or event == 'billing.paid':
            # ... resto do código ...
            
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"❌ Erro no webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500
