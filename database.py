import sqlite3
import hashlib
import os

# --------------------------------------------------
# CONFIGURAÇÃO DO BANCO DE DADOS SQLITE
# --------------------------------------------------
DB_PATH = os.path.join(os.getcwd(), 'usuarios_burocrata.db')

def hash_senha(senha):
    """Gera hash da senha usando SHA-256"""
    return hashlib.sha256(senha.encode()).hexdigest()

def init_database():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            plano TEXT DEFAULT 'FREE',
            burocreds INTEGER DEFAULT 0,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'ATIVO'
        )
    ''')
    
    # Tabela de histórico de análises
    c.execute('''
        CREATE TABLE IF NOT EXISTS historico_analises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            nome_arquivo TEXT,
            tipo_documento TEXT,
            problemas_detectados INTEGER,
            score_conformidade REAL,
            data_analise TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    # Criar conta especial com créditos infinitos
    conta_especial_email = "pedrohenriquemarques720@gmail.com"
    senha_especial_hash = hash_senha("Liz1808#")
    
    # Verificar se a conta especial já existe
    c.execute("SELECT COUNT(*) FROM usuarios WHERE email = ?", (conta_especial_email,))
    resultado = c.fetchone()
    
    if resultado and resultado[0] == 0:
        # Criar conta especial com créditos altíssimos
        c.execute('''
            INSERT INTO usuarios (nome, email, senha_hash, plano, burocreds)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Pedro Henrique (Conta Especial)", conta_especial_email, senha_especial_hash, 'PRO', 999999))
        print(f"[OK] Conta especial criada: {conta_especial_email}")
    else:
        # Atualizar senha da conta existente
        c.execute('''
            UPDATE usuarios 
            SET senha_hash = ?
            WHERE email = ?
        ''', (senha_especial_hash, conta_especial_email))
        print(f"[OK] Senha da conta especial atualizada")
    
    conn.commit()
    conn.close()

# --------------------------------------------------
# FUNÇÕES DE AUTENTICAÇÃO
# --------------------------------------------------

def criar_usuario(nome, email, senha):
    """Cria um novo usuário no sistema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Verifica se email já existe
        c.execute("SELECT COUNT(*) FROM usuarios WHERE email = ?", (email,))
        if c.fetchone()[0] > 0:
            conn.close()
            return False, "E-mail já cadastrado"
        
        # Cria usuário com 0 BuroCreds iniciais
        senha_hash = hash_senha(senha)
        burocreds_iniciais = 0
        
        c.execute('''
            INSERT INTO usuarios (nome, email, senha_hash, plano, burocreds)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, email, senha_hash, 'FREE', burocreds_iniciais))
        
        conn.commit()
        conn.close()
        return True, "Usuário criado com sucesso!"
        
    except Exception as e:
        return False, f"Erro ao criar usuário: {str(e)}"

def autenticar_usuario(email, senha):
    """Autentica um usuário pelo email e senha"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        senha_hash = hash_senha(senha)
        
        c.execute('''
            SELECT id, nome, email, plano, burocreds, estado 
            FROM usuarios 
            WHERE email = ? AND senha_hash = ? AND estado = 'ATIVO'
        ''', (email, senha_hash))
        
        resultado = c.fetchone()
        conn.close()
        
        if resultado:
            return True, {
                'id': resultado[0],
                'nome': resultado[1],
                'email': resultado[2],
                'plano': resultado[3],
                'burocreds': resultado[4],
                'estado': resultado[5]
            }
        else:
            return False, "E-mail ou senha incorretos"
            
    except Exception as e:
        return False, f"Erro na autenticação: {str(e)}"

def get_usuario_por_id(usuario_id):
    """Obtém informações do usuário pelo ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, nome, email, plano, burocreds, estado 
            FROM usuarios 
            WHERE id = ?
        ''', (usuario_id,))
        
        resultado = c.fetchone()
        conn.close()
        
        if resultado:
            return {
                'id': resultado[0],
                'nome': resultado[1],
                'email': resultado[2],
                'plano': resultado[3],
                'burocreds': resultado[4],
                'estado': resultado[5]
            }
        else:
            return None
            
    except Exception as e:
        import streamlit as st
        st.error(f"Erro ao obter usuário: {e}")
        return None

def atualizar_burocreds(usuario_id, quantidade):
    """Atualiza os BuroCreds do usuário"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Para conta especial, não debita créditos
        c.execute("SELECT email FROM usuarios WHERE id = ?", (usuario_id,))
        usuario = c.fetchone()
        
        if usuario and usuario[0] == "pedrohenriquemarques720@gmail.com":
            conn.close()
            return True
        
        # Para usuários normais, atualiza normalmente
        c.execute('''
            UPDATE usuarios 
            SET burocreds = burocreds + ? 
            WHERE id = ?
        ''', (quantidade, usuario_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"Erro ao atualizar BuroCreds: {e}")
        return False

# --------------------------------------------------
# FUNÇÕES DO SISTEMA DE ANÁLISE
# --------------------------------------------------

def registrar_analise(usuario_id, nome_arquivo, tipo_documento, problemas, score):
    """Registra uma análise no histórico"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO historico_analises 
            (usuario_id, nome_arquivo, tipo_documento, problemas_detectados, score_conformidade)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario_id, nome_arquivo, tipo_documento, problemas, score))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        import streamlit as st
        st.error(f"Erro ao registrar análise: {e}")
        return False

def get_historico_usuario(usuario_id, limit=5):
    """Obtém histórico de análises do usuário"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            SELECT nome_arquivo, tipo_documento, problemas_detectados, 
                   score_conformidade, data_analise
            FROM historico_analises
            WHERE usuario_id = ?
            ORDER BY data_analise DESC
            LIMIT ?
        ''', (usuario_id, limit))
        
        historico = []
        for row in c.fetchall():
            historico.append({
                'arquivo': row[0],
                'tipo': row[1],
                'problemas': row[2],
                'score': row[3],
                'data': row[4]
            })
        
        conn.close()
        return historico
    except:
        return []
