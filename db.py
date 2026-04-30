import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de la base de datos (Priorizar DATABASE_URL si existe)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Retorna una conexión a la base de datos PostgreSQL (Supabase)."""
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
        cursor_factory=RealDictCursor
    )

def init_db():
    """Crea las tablas necesarias si no existen (Sintaxis PostgreSQL)."""
    conn = get_connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cursor:
            # Tabla Usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    telefono VARCHAR(20) UNIQUE NOT NULL,
                    estado VARCHAR(50) DEFAULT 'inicio'
                )
            """)
            
            # Tabla Pedidos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id SERIAL PRIMARY KEY,
                    telefono VARCHAR(20) NOT NULL,
                    precio DECIMAL(10, 2),
                    tienda VARCHAR(100),
                    origen VARCHAR(100),
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla Pedidos Temporales
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos_temp (
                    telefono VARCHAR(20) PRIMARY KEY,
                    precio DECIMAL(10, 2),
                    tienda VARCHAR(100),
                    origen VARCHAR(100)
                )
            """)
    finally:
        conn.close()
