from db import get_db_conn
import json

def obtener_o_crear_usuario(telefono: str):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE telefono = %s", (telefono,))
            usuario = cursor.fetchone()
            if not usuario:
                cursor.execute("INSERT INTO usuarios (telefono, estado) VALUES (%s, 'inicio')", (telefono,))
                cursor.execute("SELECT * FROM usuarios WHERE telefono = %s", (telefono,))
                usuario = cursor.fetchone()
            return usuario

def actualizar_estado_usuario(telefono: str, nuevo_estado: str):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET estado = %s WHERE telefono = %s", (nuevo_estado, telefono))

def actualizar_nombre_usuario(telefono: str, nombre: str):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET nombre = %s WHERE telefono = %s", (nombre, telefono))

def autorizar_usuario(telefono: str, rol: str = 'vendedor', nombre: str = None):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO usuarios (telefono, rol, autorizado, nombre, estado) 
                VALUES (%s, %s, TRUE, %s, 'inicio')
                ON CONFLICT (telefono) DO UPDATE SET rol = %s, autorizado = TRUE, nombre = COALESCE(%s, usuarios.nombre)
            """, (telefono, rol, nombre, rol, nombre))

def desautorizar_usuario(telefono: str):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET autorizado = FALSE WHERE telefono = %s", (telefono,))

def cambiar_rol_usuario(telefono: str, nuevo_rol: str):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET rol = %s WHERE telefono = %s", (nuevo_rol, telefono))

def guardar_contexto_usuario(telefono: str, lista_ids: list):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET contexto_lista = %s WHERE telefono = %s", (json.dumps(lista_ids), telefono))

def obtener_contexto_usuario(telefono: str):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT contexto_lista FROM usuarios WHERE telefono = %s", (telefono,))
            res = cursor.fetchone()
            return res['contexto_lista'] if res and res['contexto_lista'] else []

def obtener_todos_los_usuarios():
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios ORDER BY nombre NULLS LAST")
            return cursor.fetchall()
