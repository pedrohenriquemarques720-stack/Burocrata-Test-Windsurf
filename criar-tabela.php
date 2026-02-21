<?php
// criar-tabela-pagamentos.php
// Execute este arquivo uma única vez para criar a tabela

$db_path = 'utilizadores_burocrata.db';

try {
    $db = new SQLite3($db_path);
    
    // Criar tabela de pagamentos
    $result = $db->exec('
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            pacote TEXT NOT NULL,
            creditos TEXT NOT NULL,
            valor TEXT,
            status TEXT DEFAULT "PENDENTE",
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_pagamento TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES utilizadores (id) ON DELETE CASCADE
        )
    ');
    
    if ($result) {
        echo "✅ Tabela 'pagamentos' criada com sucesso!<br>";
        
        // Verificar se a tabela foi criada
        $check = $db->query("SELECT name FROM sqlite_master WHERE type='table' AND name='pagamentos'");
        $table = $check->fetchArray();
        
        if ($table) {
            echo "✅ Confirmação: Tabela existe no banco de dados.<br>";
            
            // Mostrar estrutura da tabela
            echo "<br>📋 Estrutura da tabela:<br>";
            $columns = $db->query("PRAGMA table_info(pagamentos)");
            while ($col = $columns->fetchArray()) {
                echo "- {$col['name']} ({$col['type']})<br>";
            }
        }
    } else {
        echo "❌ Erro ao criar tabela: " . $db->lastErrorMsg();
    }
    
    $db->close();
    
} catch (Exception $e) {
    echo "❌ Erro: " . $e->getMessage();
}
?>