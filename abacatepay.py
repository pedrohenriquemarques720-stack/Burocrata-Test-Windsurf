import requests
import json
import os
from datetime import datetime

class AbacatePayClient:
    """Cliente para integração com a API do AbacatePay"""
    
    def __init__(self, api_key, webhook_id=None):
        self.api_key = api_key
        self.webhook_id = webhook_id or os.getenv('ABACATE_WEBHOOK_ID')
        self.base_url = "https://api.abacatepay.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def criar_cobranca(self, email, nome, cpf, pacote, valor, creditos, usuario_id):
        """
        Cria uma cobrança no AbacatePay
        Retorna: (sucesso, url_pagamento, dados_cobranca)
        """
        try:
            # Mapeamento de pacotes para IDs (links fixos)
            links_fixos = {
                "bronze": "https://app.abacatepay.com/pay/bill_B1tw5bwKTqXKnUs3jafruP5j",
                "prata": "https://app.abacatepay.com/pay/bill_Stt2u0c3uEkaXsbdPGf6Ks0B",
                "pro": "https://app.abacatepay.com/pay/bill_aMNbQaX2EgyZCdtBKLepWDqr"
            }
            
            # Se já tem link fixo, retorna direto
            if pacote in links_fixos:
                return True, links_fixos[pacote], {
                    "id": f"bill_fixo_{pacote}",
                    "url": links_fixos[pacote]
                }
            
            # Caso contrário, cria nova cobrança
            url = f"{self.base_url}/billing/create"
            
            payload = {
                "frequency": "ONE_TIME",
                "methods": ["PIX", "CARD"],
                "products": [
                    {
                        "externalId": f"plan_{pacote}",
                        "name": f"Burocrata de Bolso - {self._nome_pacote(pacote)}",
                        "quantity": 1,
                        "price": int(float(valor) * 100)  # Converte para centavos
                    }
                ],
                "returnUrl": f"{os.getenv('APP_URL', 'https://burocratadebolso.com.br')}/retorno",
                "customer": {
                    "email": email,
                    "taxId": cpf,
                    "name": nome
                },
                "metadata": {
                    "usuario_id": usuario_id,
                    "pacote": pacote,
                    "creditos": str(creditos),
                    "email": email
                },
                "webhookId": self.webhook_id  # Usar o webhook configurado
            }
            
            print(f"📤 Enviando para AbacatePay: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, json=payload, headers=self.headers)
            
            if response.status_code == 200:
                dados = response.json()
                print(f"✅ Resposta AbacatePay: {json.dumps(dados, indent=2)}")
                return True, dados['data']['url'], dados['data']
            else:
                print(f"❌ Erro AbacatePay: {response.status_code} - {response.text}")
                return False, None, None
                
        except Exception as e:
            print(f"❌ Exceção AbacatePay: {str(e)}")
            return False, None, None
    
    def _nome_pacote(self, pacote):
        """Retorna nome formatado do pacote"""
        nomes = {
            "bronze": "Pacote Bronze",
            "prata": "Pacote Prata", 
            "pro": "Plano PRO"
        }
        return nomes.get(pacote, pacote.capitalize())

# Singleton para usar em toda a aplicação
_abacate_client = None

def get_abacate_client():
    """Retorna instância do cliente AbacatePay"""
    global _abacate_client
    if _abacate_client is None:
        api_key = os.getenv('ABACATE_API_KEY')
        webhook_id = os.getenv('ABACATE_WEBHOOK_ID')
        if not api_key:
            raise ValueError("ABACATE_API_KEY não configurada")
        _abacate_client = AbacatePayClient(api_key, webhook_id)
    return _abacate_client
