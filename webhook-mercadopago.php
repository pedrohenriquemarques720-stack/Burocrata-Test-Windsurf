<?php
// webhook-mercadopago.php
$db_path = 'utilizadores_burocrata.db';

// Log da notificação
file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Notificação recebida\n", FILE_APPEND);

// Receber notificação
$input = file_get_contents('php://input');
$data = json_decode($input, true);

// Simular pagamento aprovado (para testes)
$db = new SQLite3($db_path);

// Buscar compra pendente mais recente
$result = $db->query("SELECT * FROM pagamentos WHERE status = 'PENDENTE' ORDER BY id DESC LIMIT 1");
$compra = $result->fetchArray(SQLITE3_ASSOC);

if ($compra) {
    $usuario_id = $compra['usuario_id'];
    $pacote = $compra['pacote'];
    $creditos = $compra['creditos'];
    
    // Atualizar créditos do usuário
    if ($pacote === 'pro') {
        $db->exec("UPDATE utilizadores SET plano = 'PRO', burocreditos = 999999 WHERE id = $usuario_id");
        file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Usuário $usuario_id atualizado para PRO\n", FILE_APPEND);
    } else {
        $user = $db->query("SELECT burocreditos FROM utilizadores WHERE id = $usuario_id")->fetchArray();
        $novo_total = $user['burocreditos'] + intval($creditos);
        $db->exec("UPDATE utilizadores SET burocreditos = $novo_total WHERE id = $usuario_id");
        file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Adicionados $creditos créditos ao usuário $usuario_id\n", FILE_APPEND);
    }
    
    // Marcar como aprovado
    $db->exec("UPDATE pagamentos SET status = 'APROVADO' WHERE id = {$compra['id']}");
}

$db->close();
http_response_code(200);
echo 'OK';
?>
