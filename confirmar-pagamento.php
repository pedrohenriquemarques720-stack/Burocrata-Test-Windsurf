<?php
// confirmar-pagamento.php
header('Content-Type: application/json');

// Permitir requisições do seu domínio
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// Receber dados
$input = json_decode(file_get_contents('php://input'), true);

if (!$input) {
    echo json_encode(['success' => false, 'error' => 'Dados inválidos']);
    exit;
}

$email = $input['email'] ?? '';
$pacote = $input['pacote'] ?? '';

if (!$email || !$pacote) {
    echo json_encode(['success' => false, 'error' => 'Email ou pacote não informados']);
    exit;
}

// Conectar ao banco
$db = new SQLite3('utilizadores_burocrata.db');

// Buscar usuário
$stmt = $db->prepare("SELECT id, burocreditos FROM utilizadores WHERE email = :email");
$stmt->bindValue(':email', $email, SQLITE3_TEXT);
$result = $stmt->execute();
$user = $result->fetchArray(SQLITE3_ASSOC);

if (!$user) {
    echo json_encode(['success' => false, 'error' => 'Usuário não encontrado']);
    exit;
}

// Definir créditos
switch($pacote) {
    case 'bronze':
        $creditos = 30;
        break;
    case 'prata':
        $creditos = 60;
        break;
    case 'pro':
        $creditos = 999999;
        // Atualizar plano
        $db->exec("UPDATE utilizadores SET plano = 'PRO' WHERE id = {$user['id']}");
        break;
    default:
        echo json_encode(['success' => false, 'error' => 'Pacote inválido']);
        exit;
}

// Atualizar créditos
$novo_total = $user['burocreditos'] + $creditos;
$db->exec("UPDATE utilizadores SET burocreditos = $novo_total WHERE id = {$user['id']}");

$db->close();

echo json_encode([
    'success' => true,
    'creditos_adicionados' => $creditos,
    'novo_total' => $novo_total
]);
?>