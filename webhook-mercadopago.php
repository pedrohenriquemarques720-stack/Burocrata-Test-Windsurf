<?php
// webhook-mercadopago.php
// Este arquivo recebe notificações do Mercado Pago

// Configuração do banco de dados
$db_path = 'utilizadores_burocrata.db';

// Log para debug
file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . ' - ' . file_get_contents('php://input') . PHP_EOL, FILE_APPEND);

// Receber notificação
$input = file_get_contents('php://input');
$data = json_decode($input, true);

// Verificar se é uma notificação de pagamento
if (isset($data['type']) && $data['type'] === 'payment') {
    $payment_id = $data['data']['id'];
    
    // Aqui você precisa consultar a API do Mercado Pago para obter detalhes
    // Mas por enquanto, vamos simular baseado no e-mail que veio na URL
    
    // Exemplo: se você passar o e-mail como parâmetro no link
    // https://www.mercadopago.com.br/link/...?email=usuario@email.com
    
    // Por enquanto, usaremos dados de exemplo
    $email = $_GET['email'] ?? '';
    $pacote = $_GET['pacote'] ?? '';
    
    if ($email && $pacote) {
        // Conectar ao banco SQLite
        $db = new SQLite3($db_path);
        
        // Buscar usuário pelo e-mail
        $stmt = $db->prepare("SELECT id, burocreditos FROM utilizadores WHERE email = :email");
        $stmt->bindValue(':email', $email, SQLITE3_TEXT);
        $result = $stmt->execute();
        $user = $result->fetchArray(SQLITE3_ASSOC);
        
        if ($user) {
            // Definir créditos baseado no pacote
            $creditos = 0;
            if ($pacote === 'bronze') $creditos = 30;
            if ($pacote === 'prata') $creditos = 60;
            if ($pacote === 'pro') {
                // Usuário PRO
                $update = $db->prepare("UPDATE utilizadores SET plano = 'PRO', burocreditos = 999999 WHERE id = :id");
                $update->bindValue(':id', $user['id'], SQLITE3_INTEGER);
                $update->execute();
            } else {
                // Adicionar créditos
                $novo_total = $user['burocreditos'] + $creditos;
                $update = $db->prepare("UPDATE utilizadores SET burocreditos = :novo WHERE id = :id");
                $update->bindValue(':novo', $novo_total, SQLITE3_INTEGER);
                $update->bindValue(':id', $user['id'], SQLITE3_INTEGER);
                $update->execute();
            }
            
            file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Créditos adicionados para $email" . PHP_EOL, FILE_APPEND);
        }
        
        $db->close();
    }
}

// Responder que recebeu
http_response_code(200);
echo 'OK';
?>