"""
Módulo de banco de dados do Burocrata de Bolso
"""
import sqlite3
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from config import DB_PATH, USER_CONFIG
from utils import hash_senha

class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Obtém conexão com o banco de dados"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self) -> None:
        """Inicializa o banco de dados SQLite"""
        conn = self.get_connection()
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
        self._criar_conta_especial(c)
        
        conn.commit()
        conn.close()
    
    def _criar_conta_especial(self, cursor) -> None:
        """Cria ou atualiza conta especial do desenvolvedor"""
        conta_especial = USER_CONFIG['special_account']
        senha_especial_hash = hash_senha(conta_especial['password'])
        
        # Verificar se a conta especial já existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE email = ?", (conta_especial['email'],))
        resultado = cursor.fetchone()
        
        if resultado and resultado[0] == 0:
            # Criar conta especial
            cursor.execute('''
                INSERT INTO usuarios (nome, email, senha_hash, plano, burocreds)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                conta_especial['name'],
                conta_especial['email'],
                senha_especial_hash,
                conta_especial['plan'],
                conta_especial['credits']
            ))
            print(f"✅ Conta especial criada: {conta_especial['email']}")
        else:
            # Atualizar senha da conta existente
            cursor.execute('''
                UPDATE usuarios 
                SET senha_hash = ?
                WHERE email = ?
            ''', (senha_especial_hash, conta_especial['email']))
            print(f"✅ Senha da conta especial atualizada")

# Instância global do gerenciador de banco de dados
db_manager = DatabaseManager()

def criar_usuario(nome: str, email: str, senha: str) -> Tuple[bool, str]:
    """
    Cria um novo usuário no sistema
    
    Args:
        nome: Nome do usuário
        email: E-mail do usuário
        senha: Senha do usuário
        
    Returns:
        Tupla (sucesso, mensagem)
    """
    try:
        conn = db_manager.get_connection()
        c = conn.cursor()
        
        # Verifica se email já existe
        c.execute("SELECT COUNT(*) FROM usuarios WHERE email = ?", (email,))
        if c.fetchone()[0] > 0:
            conn.close()
            return False, "E-mail já cadastrado"
        
        # Cria usuário com 0 BuroCreds iniciais
        senha_hash = hash_senha(senha)
        burocreds_iniciais = USER_CONFIG['default_credits']
        
        c.execute('''
            INSERT INTO usuarios (nome, email, senha_hash, plano, burocreds)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, email, senha_hash, 'FREE', burocreds_iniciais))
        
        conn.commit()
        conn.close()
        return True, "Usuário criado com sucesso!"
        
    except Exception as e:
        return False, f"Erro ao criar usuário: {str(e)}"

def autenticar_usuario(email: str, senha: str) -> Tuple[bool, Optional[Dict]]:
    """
    Autentica um usuário pelo email e senha
    
    Args:
        email: E-mail do usuário
        senha: Senha do usuário
        
    Returns:
        Tupla (sucesso, dados_do_usuario)
    """
    try:
        conn = db_manager.get_connection()
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
            return False, None
            
    except Exception as e:
        return False, None

def get_usuario_por_id(usuario_id: int) -> Optional[Dict]:
    """
    Obtém informações do usuário pelo ID
    
    Args:
        usuario_id: ID do usuário
        
    Returns:
        Dicionário com dados do usuário ou None
    """
    try:
        conn = db_manager.get_connection()
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
        st.error(f"Erro ao obter usuário: {e}")
        return None

def atualizar_burocreds(usuario_id: int, quantidade: int) -> bool:
    """
    Atualiza os BuroCreds do usuário
    
    Args:
        usuario_id: ID do usuário
        quantidade: Quantidade a ser adicionada (positivo) ou debitada (negativo)
        
    Returns:
        True se sucesso
    """
    try:
        conn = db_manager.get_connection()
        c = conn.cursor()
        
        # Para conta especial, não debita créditos
        c.execute("SELECT email FROM usuarios WHERE id = ?", (usuario_id,))
        usuario = c.fetchone()
        
        if usuario and usuario[0] == USER_CONFIG['special_account']['email']:
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
        st.error(f"Erro ao atualizar BuroCreds: {e}")
        return False

def registrar_analise(usuario_id: int, nome_arquivo: str, tipo_documento: str, 
                    problemas: int, score: float) -> bool:
    """
    Registra uma análise no histórico
    
    Args:
        usuario_id: ID do usuário
        nome_arquivo: Nome do arquivo analisado
        tipo_documento: Tipo do documento
        problemas: Número de problemas detectados
        score: Score de conformidade
        
    Returns:
        True se sucesso
    """
    try:
        conn = db_manager.get_connection()
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
        st.error(f"Erro ao registrar análise: {e}")
        return False

def get_historico_usuario(usuario_id: int, limit: int = 5) -> List[Dict]:
    """
    Obtém histórico de análises do usuário
    
    Args:
        usuario_id: ID do usuário
        limit: Limite de registros
        
    Returns:
        Lista de dicionários com histórico
    """
    try:
        conn = db_manager.get_connection()
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
