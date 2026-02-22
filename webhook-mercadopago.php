<?php
// webhook-mercadopago.php - VERSÃO AUTOMÁTICA FINAL
header('Content-Type: application/json');

$db_path = 'utilizadores_burocrata.db';
$access_token = 'SEU_ACCESS_TOKEN_AQUI'; // COLOQUE SEU ACCESS TOKEN

// Receber notificação
$input = file_get_contents('php://input');
$data = json_decode($input, true);

file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Recebido: " . $input . PHP_EOL, FILE_APPEND);

// Verificar se é pagamento
if ($data['type'] !== 'payment') {
    http_response_code(200);
    exit;
}

$payment_id = $data['data']['id'];

// Consultar API do Mercado Pago
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, "https://api.mercadopago.com/v1/payments/$payment_id");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Authorization: Bearer ' . $access_token
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode != 200) {
    file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Erro API: $httpCode" . PHP_EOL, FILE_APPEND);
    http_response_code(200);
    exit;
}

$payment = json_decode($response, true);

// Se pagamento aprovado
if ($payment['status'] === 'approved') {
    $external_ref = $payment['external_reference'] ?? '';
    
    // Extrair email ou ID do usuário da referência externa
    // Você PRECISA passar isso na criação do link
    
    file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Pagamento aprovado: $payment_id" . PHP_EOL, FILE_APPEND);
    
    // Exemplo: se external_ref for o email
    if ($external_ref) {
        $db = new SQLite3($db_path);
        
        // Buscar compra pendente
        $result = $db->query("SELECT * FROM pagamentos WHERE status = 'PENDENTE' ORDER BY id DESC LIMIT 1");
        $compra = $result->fetchArray(SQLITE3_ASSOC);
        
        if ($compra) {
            $usuario_id = $compra['usuario_id'];
            $pacote = $compra['pacote'];
            $creditos = $compra['creditos'];
            
            if ($pacote === 'pro') {
                $db->exec("UPDATE utilizadores SET plano = 'PRO', burocreditos = 999999 WHERE id = $usuario_id");
                file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Usuário $usuario_id virou PRO" . PHP_EOL, FILE_APPEND);
            } else {
                $user = $db->query("SELECT burocreditos FROM utilizadores WHERE id = $usuario_id")->fetchArray();
                $novo_total = $user['burocreditos'] + intval($creditos);
                $db->exec("UPDATE utilizadores SET burocreditos = $novo_total WHERE id = $usuario_id");
                file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Adicionados $creditos créditos ao usuário $usuario_id" . PHP_EOL, FILE_APPEND);
            }
            
            $db->exec("UPDATE pagamentos SET status = 'APROVADO' WHERE id = {$compra['id']}");
        }
        
        $db->close();
    }
}

http_response_code(200);
echo 'OK';
?>
