<?php
// criar-tabela.php
$db_path = 'utilizadores_burocrata.db';
$db = new SQLite3($db_path);

$result = $db->exec('
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

if ($result) {
    echo "✅ Tabela 'pagamentos' criada com sucesso!<br>";
    
    // Listar tabelas
    $tables = $db->query("SELECT name FROM sqlite_master WHERE type='table'");
    echo "Tabelas existentes:<br>";
    while ($table = $tables->fetchArray()) {
        echo " - " . $table['name'] . "<br>";
    }
} else {
    echo "❌ Erro ao criar tabela: " . $db->lastErrorMsg();
}

$db->close();
?>
