<?php
// gerar-pix.php
header('Content-Type: application/json');

// CONFIGURAÇÕES
$access_token = 'APP_USR-419498276806507-022123-02e42585338d7e48c6b87c3dfe4b5965-728396417'; // Substitua pelo seu token

// Receber dados
$data = json_decode(file_get_contents('php://input'), true);
$pacote = $data['pacote'] ?? 'bronze';
$email = $data['email'] ?? '';

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

// Criar pagamento Pix na API do Mercado Pago
$payment_data = [
    "transaction_amount" => $valor,
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
curl_close($ch);

if ($httpCode == 201) {
    $payment = json_decode($response, true);
    
    // Extrair dados do Pix
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
        'error' => 'Erro ao gerar Pix: ' . $httpCode
    ]);
}

?>
