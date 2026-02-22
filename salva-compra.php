<?php
// salvar-compra.php com logs
header('Content-Type: application/json');

// Ativar exibição de erros (temporário)
ini_set('display_errors', 1);
error_reporting(E_ALL);

$db_path = 'utilizadores_burocrata.db';

// Log para debug
file_put_contents('debug_log.txt', date('Y-m-d H:i:s') . " - POST recebido: " . file_get_contents('php://input') . PHP_EOL, FILE_APPEND);

// Receber dados
$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data || !isset($data['usuario_id']) || !isset($data['pacote'])) {
    file_put_contents('debug_log.txt', date('Y-m-d H:i:s') . " - ERRO: Dados inválidos" . PHP_EOL, FILE_APPEND);
    echo json_encode(['success' => false, 'error' => 'Dados inválidos']);
    exit;
}

try {
    // Verificar se o arquivo do banco existe
    if (!file_exists($db_path)) {
        file_put_contents('debug_log.txt', date('Y-m-d H:i:s') . " - ERRO: Banco não encontrado em $db_path" . PHP_EOL, FILE_APPEND);
        echo json_encode(['success' => false, 'error' => 'Banco não encontrado']);
        exit;
    }
    
    $db = new SQLite3($db_path);
    
    // Verificar se a tabela pagamentos existe
    $check = $db->query("SELECT name FROM sqlite_master WHERE type='table' AND name='pagamentos'");
    if (!$check->fetchArray()) {
        file_put_contents('debug_log.txt', date('Y-m-d H:i:s') . " - ERRO: Tabela pagamentos não existe" . PHP_EOL, FILE_APPEND);
        echo json_encode(['success' => false, 'error' => 'Tabela pagamentos não existe. Execute criar-tabela-pagamentos.php']);
        exit;
    }
    
    // Inserir compra pendente
    $stmt = $db->prepare("
        INSERT INTO pagamentos (usuario_id, pacote, creditos, valor, status) 
        VALUES (:id, :pacote, :creditos, :valor, 'PENDENTE')
    ");
    
    $stmt->bindValue(':id', $data['usuario_id'], SQLITE3_INTEGER);
    $stmt->bindValue(':pacote', $data['pacote'], SQLITE3_TEXT);
    $stmt->bindValue(':creditos', $data['creditos'], SQLITE3_TEXT);
    $stmt->bindValue(':valor', $data['valor'], SQLITE3_TEXT);
    
    $result = $stmt->execute();
    
    if ($result) {
        $last_id = $db->lastInsertRowID();
        file_put_contents('debug_log.txt', date('Y-m-d H:i:s') . " - ✅ Compra salva com ID: $last_id" . PHP_EOL, FILE_APPEND);
        echo json_encode(['success' => true, 'compra_id' => $last_id]);
    } else {
        file_put_contents('debug_log.txt', date('Y-m-d H:i:s') . " - ❌ Erro ao inserir: " . $db->lastErrorMsg() . PHP_EOL, FILE_APPEND);
        echo json_encode(['success' => false, 'error' => $db->lastErrorMsg()]);
    }
    
    $db->close();
    
} catch (Exception $e) {
    file_put_contents('debug_log.txt', date('Y-m-d H:i:s') . " - ❌ Exceção: " . $e->getMessage() . PHP_EOL, FILE_APPEND);
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>
