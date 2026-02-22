# Sistema de Pagamentos com AbacatePay

## 📋 Arquivos do Sistema

- `abacatepay.py` - Cliente para API do AbacatePay
- `webhook_abacate.py` - Servidor que recebe notificações de pagamento
- `backend.py` - API principal (modificada para AbacatePay)
- `pagamento.php` - Página de checkout (modificada)
- `credenciais.env` - Configurações (ATUALIZADO)

## 🚀 Como Executar

### Desenvolvimento Local
```bash
# 1. Instalar dependências
pip install requests flask python-dotenv

# 2. Configurar credenciais no arquivo .env
# ABACATE_API_KEY=sua_chave_aqui

# 3. Iniciar servidor webhook (porta 5001)
python webhook_abacate.py

# 4. Em outro terminal, iniciar servidor principal (porta 5000)
python backend.py

# 5. Acessar o site
# Abra index.html no navegador