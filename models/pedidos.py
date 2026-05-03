from db import get_connection

def guardar_pedido_final(telefono: str, precio: float, tienda: str, origen: str, metodo_envio: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO pedidos (telefono, precio, tienda, origen, metodo_envio) VALUES (%s, %s, %s, %s, %s)",
                (telefono, precio, tienda, origen, metodo_envio)
            )
    finally:
        conn.close()

def obtener_pedidos_del_dia(telefono: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM pedidos WHERE telefono = %s AND DATE(fecha) = CURRENT_DATE",
                (telefono,)
            )
            return cursor.fetchall()
    finally:
        conn.close()

def obtener_pedidos_del_dia_todos():
    """Obtiene todos los pedidos del día de todos los vendedores, junto con sus nombres."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.*, u.nombre 
                FROM pedidos p
                JOIN usuarios u ON p.telefono = u.telefono
                WHERE DATE(p.fecha) = CURRENT_DATE
                ORDER BY p.metodo_envio, u.nombre
            """)
            return cursor.fetchall()
    finally:
        conn.close()
