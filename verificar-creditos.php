<?php
// verificar-creditos.php
header('Content-Type: application/json');

$db_path = 'utilizadores_burocrata.db';
$usuario_id = $_GET['usuario_id'] ?? 0;

if (!$usuario_id) {
    echo json_encode(['success' => false]);
    exit;
}

try {
    $db = new SQLite3($db_path);
    
    $stmt = $db->prepare("SELECT burocreditos, plano FROM utilizadores WHERE id = :id");
    $stmt->bindValue(':id', $usuario_id, SQLITE3_INTEGER);
    $result = $stmt->execute();
    $user = $result->fetchArray(SQLITE3_ASSOC);
    
    if ($user) {
        echo json_encode([
            'success' => true,
            'burocreditos' => $user['burocreditos'],
            'plano' => $user['plano'] ?? 'GRATUITO'
        ]);
    } else {
        echo json_encode(['success' => false]);
    }
    
    $db->close();
    
} catch (Exception $e) {
    echo json_encode(['success' => false]);
}
?>