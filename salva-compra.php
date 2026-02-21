<?php
// salvar-compra.php
$db_path = 'utilizadores_burocrata.db';
$data = json_decode(file_get_contents('php://input'), true);

$db = new SQLite3($db_path);
$stmt = $db->prepare("INSERT INTO pagamentos (usuario_id, pacote, creditos) VALUES (:id, :pacote, :creditos)");
$stmt->bindValue(':id', $data['usuario_id'], SQLITE3_INTEGER);
$stmt->bindValue(':pacote', $data['pacote'], SQLITE3_TEXT);
$stmt->bindValue(':creditos', $data['creditos'], SQLITE3_TEXT);
$stmt->execute();

echo json_encode(['success' => true]);
?>