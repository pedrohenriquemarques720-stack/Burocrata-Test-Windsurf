# database.py - Funções auxiliares para PostgreSQL
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

def get_db_connection():
    """Retorna uma conexão com o banco PostgreSQL"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None

def test_connection():
    """Testa a conexão com o banco"""
    conn = get_db_connection()
    if conn:
        conn.close()
        return True
    return False
