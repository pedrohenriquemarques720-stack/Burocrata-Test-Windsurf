<?php
// salvar-compra.php - VERSÃO SIMPLIFICADA
header('Content-Type: application/json');

// Caminho do banco
$db_path = 'utilizadores_burocrata.db';

// Receber dados
$input = file_get_contents('php://input');
$data = json_decode($input, true);

// Se não conseguiu ler JSON, retorna erro
if (!$data) {
    echo json_encode(['success' => false, 'error' => 'Dados não recebidos']);
    exit;
}

// Conectar ao banco
$db = new SQLite3($db_path);

// Criar tabela se não existir
$db->exec("
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        pacote TEXT NOT NULL,
        creditos TEXT NOT NULL,
        valor TEXT,
        status TEXT DEFAULT 'PENDENTE',
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
");

// Inserir compra
$stmt = $db->prepare("
    INSERT INTO pagamentos (usuario_id, pacote, creditos, valor) 
    VALUES (:id, :pacote, :creditos, :valor)
");

$stmt->bindValue(':id', $data['usuario_id'], SQLITE3_INTEGER);
$stmt->bindValue(':pacote', $data['pacote'], SQLITE3_TEXT);
$stmt->bindValue(':creditos', $data['creditos'], SQLITE3_TEXT);
$stmt->bindValue(':valor', $data['valor'], SQLITE3_TEXT);

if ($stmt->execute()) {
    echo json_encode(['success' => true]);
} else {
    echo json_encode(['success' => false, 'error' => 'Erro no banco de dados']);
}

$db->close();
?>
