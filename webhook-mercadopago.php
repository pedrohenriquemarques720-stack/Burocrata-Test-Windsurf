<?php
// webhook-mercadopago.php - VERSÃO ATUALIZADA

// Configuração do banco de dados
$db_path = 'utilizadores_burocrata.db';

// SEU ACCESS TOKEN DO MERCADO PAGO (COLOQUE AQUI)
$access_token = 'SEU_ACCESS_TOKEN_AQUI'; // Substitua pelo seu token real

// Log para debug
file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . ' - Recebido: ' . file_get_contents('php://input') . PHP_EOL, FILE_APPEND);

// Receber notificação
$input = file_get_contents('php://input');
$data = json_decode($input, true);

// Verificar se é uma notificação de pagamento
if (isset($data['type']) && $data['type'] === 'payment') {
    $payment_id = $data['data']['id'];
    
    // CONSULTAR API DO MERCADO PAGO para obter detalhes do pagamento
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, "https://api.mercadopago.com/v1/payments/$payment_id");
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . $access_token
    ]);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode == 200) {
        $payment = json_decode($response, true);
        
        // Log da resposta
        file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . ' - Payment details: ' . json_encode($payment) . PHP_EOL, FILE_APPEND);
        
        // Verificar se o pagamento foi aprovado
        if ($payment['status'] === 'approved') {
            
            // Você PRECISA de uma forma de identificar o usuário
            // Opção 1: Usar external_reference (recomendado)
            $external_reference = $payment['external_reference'] ?? '';
            
            // Opção 2: Extrair do description ou outro campo
            // Exemplo: se você passou o email na descrição
            $description = $payment['description'] ?? '';
            $email = ''; // Extrair email da description se necessário
            
            file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - External reference: $external_reference" . PHP_EOL, FILE_APPEND);
            
            // Aqui você precisa identificar o usuário
            // Por enquanto, vamos usar um valor fixo para teste
            // DEPOIS você precisa modificar para identificar corretamente
            
            // Exemplo: se external_reference tiver o ID do usuário
            if ($external_reference) {
                $usuario_id = $external_reference;
                
                // Conectar ao banco SQLite
                $db = new SQLite3($db_path);
                
                // Aqui você precisa saber qual pacote foi comprado
                // Por enquanto, vamos buscar a compra pendente mais recente
                $stmt = $db->prepare("SELECT id, pacote, creditos FROM pagamentos WHERE usuario_id = :id AND status = 'PENDENTE' ORDER BY id DESC LIMIT 1");
                $stmt->bindValue(':id', $usuario_id, SQLITE3_INTEGER);
                $result = $stmt->execute();
                $compra = $result->fetchArray(SQLITE3_ASSOC);
                
                if ($compra) {
                    $pacote = $compra['pacote'];
                    $creditos = $compra['creditos'];
                    
                    file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Compra encontrada: $pacote, $creditos créditos" . PHP_EOL, FILE_APPEND);
                    
                    if ($pacote === 'pro') {
                        $update = $db->prepare("UPDATE utilizadores SET plano = 'PRO', burocreditos = 999999 WHERE id = :id");
                        $update->bindValue(':id', $usuario_id, SQLITE3_INTEGER);
                        $update->execute();
                        file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Usuário $usuario_id atualizado para PRO" . PHP_EOL, FILE_APPEND);
                    } else {
                        // Adicionar créditos
                        $creditos_num = ($creditos === 'ilimitado') ? 999999 : (int)$creditos;
                        
                        // Primeiro buscar créditos atuais
                        $stmt_user = $db->prepare("SELECT burocreditos FROM utilizadores WHERE id = :id");
                        $stmt_user->bindValue(':id', $usuario_id, SQLITE3_INTEGER);
                        $user_result = $stmt_user->execute();
                        $user = $user_result->fetchArray(SQLITE3_ASSOC);
                        
                        if ($user) {
                            $novo_total = $user['burocreditos'] + $creditos_num;
                            $update = $db->prepare("UPDATE utilizadores SET burocreditos = :novo WHERE id = :id");
                            $update->bindValue(':novo', $novo_total, SQLITE3_INTEGER);
                            $update->bindValue(':id', $usuario_id, SQLITE3_INTEGER);
                            $update->execute();
                            file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - $creditos_num créditos adicionados ao usuário $usuario_id" . PHP_EOL, FILE_APPEND);
                        }
                    }
                    
                    // Atualizar status do pagamento
                    $update_pag = $db->prepare("UPDATE pagamentos SET status = 'APROVADO', data_pagamento = CURRENT_TIMESTAMP WHERE usuario_id = :id AND status = 'PENDENTE'");
                    $update_pag->bindValue(':id', $usuario_id, SQLITE3_INTEGER);
                    $update_pag->execute();
                    
                    file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Pagamento processado para usuário $usuario_id" . PHP_EOL, FILE_APPEND);
                } else {
                    file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Nenhuma compra pendente encontrada para usuário $usuario_id" . PHP_EOL, FILE_APPEND);
                }
                
                $db->close();
            } else {
                file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - External reference vazia" . PHP_EOL, FILE_APPEND);
            }
        }
    } else {
        file_put_contents('webhook_log.txt', date('Y-m-d H:i:s') . " - Erro ao consultar API: HTTP $httpCode" . PHP_EOL, FILE_APPEND);
    }
}

// Responder que recebeu
http_response_code(200);
echo 'OK';
?>
