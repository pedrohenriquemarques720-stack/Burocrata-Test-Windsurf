<?php
// gerar-pix.php
header('Content-Type: application/json');

// CONFIGURAÇÕES
$access_token = 'APP_USR-419498276806507-022123-02e42585338d7e48c6b87c3dfe4b5965-728396417'; // SEU TOKEN AQUI

// Log para debug
file_put_contents('pix_log.txt', date('Y-m-d H:i:s') . " - Requisição recebida\n", FILE_APPEND);

// Receber dados
$input = file_get_contents('php://input');
file_put_contents('pix_log.txt', date('Y-m-d H:i:s') . " - Input: " . $input . "\n", FILE_APPEND);

$data = json_decode($input, true);

if (!$data) {
    file_put_contents('pix_log.txt', date('Y-m-d H:i:s') . " - Erro: dados inválidos\n", FILE_APPEND);
    echo json_encode(['success' => false, 'error' => 'Dados inválidos']);
    exit;
}

$pacote = $data['pacote'] ?? 'bronze';
$email = $data['email'] ?? '';

if (!$email) {
    file_put_contents('pix_log.txt', date('Y-m-d H:i:s') . " - Erro: email não fornecido\n", FILE_APPEND);
    echo json_encode(['success' => false, 'error' => 'Email não fornecido']);
    exit;
}

// Definir valor e descrição
switch($pacote) {
    case 'bronze':
        $valor = 15.00;
        $descricao = 'Pacote Bronze - 30 BuroCréditos';
        break;
    case 'prata':
        $valor = 30.00;
        $descricao = 'Pacote Prata - 60 BuroCréditos';
        break;
    case 'pro':
        $valor = 80.00;
        $descricao = 'Plano PRO - Acesso Ilimitado';
        break;
    default:
        $valor = 15.00;
        $descricao = 'Pacote Bronze - 30 BuroCréditos';
}

file_put_contents('pix_log.txt', date('Y-m-d H:i:s') . " - Gerando Pix: $pacote, $valor, $email\n", FILE_APPEND);

// Criar pagamento Pix na API do Mercado Pago
$payment_data = [
    "transaction_amount" => (float)$valor,
    "description" => $descricao,
    "payment_method_id" => "pix",
    "payer" => [
        "email" => $email
    ]
];

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, "https://api.mercadopago.com/v1/payments");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payment_data));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Authorization: Bearer ' . $access_token,
    'X-Idempotency-Key: ' . uniqid()
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlError = curl_error($ch);
curl_close($ch);

file_put_contents('pix_log.txt', date('Y-m-d H:i:s') . " - HTTP Code: $httpCode\n", FILE_APPEND);
file_put_contents('pix_log.txt', date('Y-m-d H:i:s') . " - Response: $response\n", FILE_APPEND);
file_put_contents('pix_log.txt', date('Y-m-d H:i:s') . " - CURL Error: $curlError\n", FILE_APPEND);

if ($httpCode == 201) {
    $payment = json_decode($response, true);
    
    $qr_code = $payment['point_of_interaction']['transaction_data']['qr_code'];
    $qr_code_base64 = $payment['point_of_interaction']['transaction_data']['qr_code_base64'];
    $payment_id = $payment['id'];
    
    echo json_encode([
        'success' => true,
        'qr_code' => $qr_code,
        'qr_code_base64' => $qr_code_base64,
        'payment_id' => $payment_id,
        'valor' => $valor,
        'descricao' => $descricao
    ]);
} else {
    echo json_encode([
        'success' => false,
        'error' => 'Erro ao gerar Pix: ' . $httpCode . ' - ' . $response
    ]);
}
?>
