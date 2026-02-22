<?php
// salvar-compra.php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Configuração do banco
$db_path = 'utilizadores_burocrata.db';

// Receber dados
$input = file_get_contents('php://input');
$data = json_decode($input, true);

// Se não recebeu JSON, tenta POST normal
if (!$data) {
    $data = $_POST;
}

// Validar dados
if (!$data || !isset($data['usuario_id']) || !isset($data['pacote'])) {
    echo json_encode(['success' => false, 'error' => 'Dados inválidos']);
    exit;
}

try {
    // Conectar ao banco
    $db = new SQLite3($db_path);
    
    // Criar tabela se não existir (garantia)
    $db->exec('
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            pacote TEXT NOT NULL,
            creditos TEXT NOT NULL,
            valor TEXT,
            status TEXT DEFAULT "PENDENTE",
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_pagamento TIMESTAMP
        )
    ');
    
    // Inserir compra
    $stmt = $db->prepare("
        INSERT INTO pagamentos (usuario_id, pacote, creditos, valor, status) 
        VALUES (:id, :pacote, :creditos, :valor, 'PENDENTE')
    ");
    
    $stmt->bindValue(':id', $data['usuario_id'], SQLITE3_INTEGER);
    $stmt->bindValue(':pacote', $data['pacote'], SQLITE3_TEXT);
    $stmt->bindValue(':creditos', $data['creditos'], SQLITE3_TEXT);
    $stmt->bindValue(':valor', $data['valor'] ?? '', SQLITE3_TEXT);
    
    if ($stmt->execute()) {
        $last_id = $db->lastInsertRowID();
        echo json_encode(['success' => true, 'compra_id' => $last_id]);
    } else {
        echo json_encode(['success' => false, 'error' => 'Erro ao inserir no banco']);
    }
    
    $db->close();
    
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => $e->getMessage()]);
}
?>
