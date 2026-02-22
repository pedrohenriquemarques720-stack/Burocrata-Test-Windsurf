#!/bin/bash

echo "🚀 Iniciando Burocrata de Bolso - Sistema de Pagamentos AbacatePay"
echo "================================================================="

# Iniciar servidor webhook na porta 5001 (em background)
echo "📡 Iniciando servidor webhook AbacatePay na porta 5001..."
python webhook_abacate.py &
WEBHOOK_PID=$!

# Aguardar 2 segundos
sleep 2

# Iniciar servidor principal na porta 5000
echo "⚙️  Iniciando servidor principal na porta 5000..."
python backend.py

# Quando o servidor principal for encerrado, matar o webhook
kill $WEBHOOK_PID