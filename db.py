import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import config

@contextmanager
def get_db_conn():
    """Context manager para conexiones PostgreSQL."""
    conn = None
    try:
        if config.DATABASE_URL:
            conn = psycopg2.connect(config.DATABASE_URL, cursor_factory=RealDictCursor)
        else:
            conn = psycopg2.connect(
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
                port=config.DB_PORT,
                cursor_factory=RealDictCursor
            )
        conn.autocommit = True
        yield conn
    except Exception as e:
        print(f"Error de base de datos: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def get_connection():
    """Mantenido por compatibilidad legacy pero usa config."""
    if config.DATABASE_URL:
        conn = psycopg2.connect(config.DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        conn = psycopg2.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT,
            cursor_factory=RealDictCursor
        )
    conn.autocommit = True
    return conn

def init_db():
    """Inicialización de tablas (Sintaxis PostgreSQL)."""
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            # Tabla Usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    telefono TEXT PRIMARY KEY,
                    nombre TEXT,
                    rol TEXT DEFAULT 'vendedor',
                    autorizado BOOLEAN DEFAULT FALSE,
                    estado TEXT DEFAULT 'nuevo',
                    contexto_lista JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla Pedidos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos (
                    id SERIAL PRIMARY KEY,
                    telefono TEXT NOT NULL,
                    precio DECIMAL(20, 2),
                    cliente TEXT,
                    bodega TEXT,
                    metodo_envio TEXT,
                    productos TEXT,
                    fecha_entrega DATE,
                    estado TEXT DEFAULT 'pendiente',
                    fecha_entregado TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla Pedidos Temporales
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos_temp (
                    telefono VARCHAR(20) PRIMARY KEY,
                    precio DECIMAL(20, 2),
                    tienda VARCHAR(100),
                    origen VARCHAR(100),
                    metodo_envio VARCHAR(50),
                    productos TEXT,
                    cliente VARCHAR(255),
                    bodega VARCHAR(100),
                    fecha_entrega DATE
                )
            """)
            
            # Migraciones y ajustes de columnas
            cursor.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre VARCHAR(100)")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol VARCHAR(20) DEFAULT 'vendedor'")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS autorizado BOOLEAN DEFAULT FALSE")

            # Tablas de Catálogo
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) UNIQUE NOT NULL,
                    alias TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bodegas (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) UNIQUE NOT NULL,
                    alias TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metodos_envio (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) UNIQUE NOT NULL,
                    alias TEXT
                )
            """)

            # Historial y Otros
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historial_pedidos (
                    id SERIAL PRIMARY KEY,
                    pedido_id INT,
                    datos_previos JSONB,
                    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modificado_por VARCHAR(20)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contexto_grupos (
                    jid VARCHAR(100) PRIMARY KEY,
                    lista_pedidos_ids INT[]
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fechas_bloqueadas (
                    fecha DATE PRIMARY KEY
                )
            """)

