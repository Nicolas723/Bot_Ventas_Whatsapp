from db import get_connection

def guardar_pedido_final(telefono: str, precio: float, tienda: str, origen: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO pedidos (telefono, precio, tienda, origen) VALUES (%s, %s, %s, %s)",
                (telefono, precio, tienda, origen)
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
