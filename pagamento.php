<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Burocrata de Bolso - Pagamento</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #10263D;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container { max-width: 500px; width: 90%; margin: 20px; }
        .card {
            background: #1a3658;
            border-radius: 20px;
            padding: 30px;
            border: 3px solid #F8D96D;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }
        h1 {
            color: #F8D96D;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
        }
        .dados-compra {
            background: #0f2a40;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
        }
        .dados-compra p { margin: 10px 0; font-size: 1.1em; }
        .dados-compra strong { color: #F8D96D; }
        .btn-pagar {
            background: linear-gradient(135deg, #F8D96D, #d4b747);
            color: #10263D;
            border: none;
            padding: 20px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 1.3em;
            width: 100%;
            cursor: pointer;
            margin: 20px 0;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        .btn-pagar:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(248, 217, 109, 0.4);
        }
        .btn-voltar {
            background: transparent;
            color: #F8D96D;
            border: 2px solid #F8D96D;
            padding: 12px;
            border-radius: 10px;
            font-weight: 600;
            width: 100%;
            cursor: pointer;
            margin-top: 20px;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        .btn-voltar:hover { background: rgba(248, 217, 109, 0.1); }
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        .spinner {
            border: 4px solid rgba(248, 217, 109, 0.2);
            border-top: 4px solid #F8D96D;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .info-webhook {
            font-size: 0.8em;
            color: #a0aec0;
            text-align: center;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>⚖️ Finalizar Compra</h1>
            
            <?php
            // PEGAR DADOS DA URL
            $pacote = isset($_GET['pacote']) ? $_GET['pacote'] : 'bronze';
            $valor = isset($_GET['valor']) ? $_GET['valor'] : '15';
            $creditos = isset($_GET['creditos']) ? $_GET['creditos'] : '30';
            $email = isset($_GET['email']) ? $_GET['email'] : '';
            
            // Para teste - pegar usuário da sessão se disponível
            session_start();
            $usuario_id = isset($_SESSION['usuario_id']) ? $_SESSION['usuario_id'] : 1;
            $usuario_nome = isset($_SESSION['usuario_nome']) ? $_SESSION['usuario_nome'] : 'Cliente';
            
            // Webhook configurado
            $webhook_id = 'webh_dev_ahdHbQwGkz4qds2aphSsHWtH';
            $webhook_url = 'https://burocratadebolso.com.br/webhook/abacate';
            ?>

            <div class="dados-compra">
                <p><strong>Pacote:</strong> <?php echo ucfirst($pacote); ?></p>
                <p><strong>Valor:</strong> R$ <?php echo htmlspecialchars($valor); ?></p>
                <p><strong>Créditos:</strong> <?php echo htmlspecialchars($creditos); ?></p>
                <p><strong>E-mail:</strong> <?php echo htmlspecialchars($email) ?: 'Não informado'; ?></p>
            </div>

            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>🔍 Criando pagamento...</p>
            </div>

            <button id="btn-pagar" class="btn-pagar" onclick="criarPagamento()">
                💳 Ir para o AbacatePay
            </button>
            
            <p style="text-align: center; margin: 20px 0; color: #a0aec0;">
                Você será redirecionado para o ambiente seguro do AbacatePay
            </p>
            
            <div class="info-webhook">
                Webhook ID: <?php echo $webhook_id; ?><br>
                URL: <?php echo $webhook_url; ?>
            </div>
            
            <a href="index.html" class="btn-voltar">← Voltar para Loja</a>
        </div>
    </div>

    <script>
        function criarPagamento() {
            const btn = document.getElementById('btn-pagar');
            const loading = document.getElementById('loading');
            
            // Mostrar loading
            btn.style.display = 'none';
            loading.style.display = 'block';
            
            // Dados para enviar ao backend
            const dados = {
                pacote: '<?php echo $pacote; ?>',
                valor: <?php echo $valor; ?>,
                creditos: '<?php echo $creditos; ?>',
                usuario_id: <?php echo $usuario_id; ?>,
                usuario_email: '<?php echo $email; ?>',
                usuario_nome: '<?php echo $usuario_nome; ?>',
                usuario_cpf: '' // Opcional
            };
            
            console.log('📤 Enviando dados:', dados);
            
            // Chamar API do backend
            fetch('http://localhost:5000/criar-pagamento', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(dados)
            })
            .then(response => response.json())
            .then(data => {
                console.log('📥 Resposta:', data);
                if (data.success && data.url_pagamento) {
                    // Redirecionar para o AbacatePay
                    window.location.href = data.url_pagamento;
                } else {
                    alert('Erro ao criar pagamento: ' + (data.error || 'Tente novamente'));
                    btn.style.display = 'block';
                    loading.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('❌ Erro:', error);
                alert('Erro de conexão com o servidor. Verifique se o backend está rodando.');
                btn.style.display = 'block';
                loading.style.display = 'none';
            });
        }
    </script>
</body>
</html>
