from db import get_connection

def guardar_pedido_final(telefono: str, precio: float, cliente: str, bodega: str, metodo_envio: str, productos: str, fecha_entrega: str = None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if not fecha_entrega:
                from datetime import datetime
                fecha_entrega = datetime.now().strftime("%Y-%m-%d")
                
            cursor.execute(
                "INSERT INTO pedidos (telefono, precio, cliente, bodega, metodo_envio, productos, fecha_entrega) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (telefono, precio, cliente, bodega, metodo_envio, productos, fecha_entrega)
            )
    finally:
        conn.close()

def obtener_pedidos_del_dia(telefono: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM pedidos WHERE telefono = %s AND fecha_entrega = CURRENT_DATE",
                (telefono,)
            )
            return cursor.fetchall()
    finally:
        conn.close()

def obtener_pedidos_del_dia_todos():
    """Obtiene todos los pedidos que deben entregarse HOY, junto con sus nombres."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.*, u.nombre 
                FROM pedidos p
                JOIN usuarios u ON p.telefono = u.telefono
                WHERE p.fecha_entrega = CURRENT_DATE
                ORDER BY p.metodo_envio, u.nombre
            """)
            return cursor.fetchall()
    finally:
        conn.close()
