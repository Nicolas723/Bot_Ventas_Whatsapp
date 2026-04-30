from db import get_connection

def obtener_o_crear_usuario(telefono: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE telefono = %s", (telefono,))
            usuario = cursor.fetchone()
            if not usuario:
                cursor.execute("INSERT INTO usuarios (telefono, estado) VALUES (%s, 'inicio')", (telefono,))
                cursor.execute("SELECT * FROM usuarios WHERE telefono = %s", (telefono,))
                usuario = cursor.fetchone()
            return usuario
    finally:
        conn.close()

def actualizar_estado_usuario(telefono: str, nuevo_estado: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET estado = %s WHERE telefono = %s", (nuevo_estado, telefono))
    finally:
        conn.close()
