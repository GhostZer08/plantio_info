import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")

print(os.getenv("DATABASE_URL"))

def get_connection():
    """Retorna uma conexão com o banco de dados PostgreSQL."""
    if not DATABASE_URL:
        raise ValueError("A variável de ambiente DATABASE_URL não está definida.")
    
    conn = psycopg2.connect(DATABASE_URL)
    return conn
