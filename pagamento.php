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
            
            // LINKS DO MERCADO PAGO
            $links = [
                'bronze' => 'https://mpago.la/2ss4rSt',
                'prata' => 'https://mpago.la/1UFjmFD',
                'pro' => 'https://mpago.la/32FZG95'
            ];
            
            // PEGAR LINK CORRETO
            $link_atual = isset($links[$pacote]) ? $links[$pacote] : $links['bronze'];
            ?>

            <div class="dados-compra">
                <p><strong>Pacote:</strong> <?php echo ucfirst($pacote); ?></p>
                <p><strong>Valor:</strong> R$ <?php echo htmlspecialchars($valor); ?></p>
                <p><strong>Créditos:</strong> <?php echo htmlspecialchars($creditos); ?></p>
                <p><strong>E-mail:</strong> <?php echo htmlspecialchars($email) ?: 'Não informado'; ?></p>
            </div>

            <a href="<?php echo $link_atual; ?>" target="_blank" class="btn-pagar">
                💳 Ir para o Mercado Pago
            </a>
            
            <p style="text-align: center; margin: 20px 0; color: #a0aec0;">
                Você será redirecionado para o ambiente seguro do Mercado Pago
            </p>
            
            <a href="index.html" class="btn-voltar">← Voltar para Loja</a>
        </div>
    </div>
</body>
</html>
