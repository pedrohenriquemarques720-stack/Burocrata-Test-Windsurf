<?php
header('Content-Type: application/json');
$db_path = 'utilizadores_burocrata.db';

$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data || !isset($data['usuario_id'])) {
    echo json_encode(['success' => false, 'error' => 'Dados inválidos']);
    exit;
}

$db = new SQLite3($db_path);

// Criar tabela se não existir
$db->exec("CREATE TABLE IF NOT EXISTS pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    pacote TEXT NOT NULL,
    creditos TEXT NOT NULL,
    status TEXT DEFAULT 'PENDENTE',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)");

$stmt = $db->prepare("INSERT INTO pagamentos (usuario_id, pacote, creditos) VALUES (:id, :pacote, :creditos)");
$stmt->bindValue(':id', $data['usuario_id'], SQLITE3_INTEGER);
$stmt->bindValue(':pacote', $data['pacote'], SQLITE3_TEXT);
$stmt->bindValue(':creditos', $data['creditos'], SQLITE3_TEXT);
$stmt->execute();

echo json_encode(['success' => true]);
$db->close();
?>
