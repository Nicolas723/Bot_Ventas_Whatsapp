from db import get_db_conn

def obtener_pedido_temporal(telefono: str):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM pedidos_temp WHERE telefono = %s", (telefono,))
            return cursor.fetchone()

def actualizar_pedido_temporal(telefono: str, datos: dict):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pedidos_temp WHERE telefono = %s", (telefono,))
            if cursor.fetchone():
                fields = [f"{k} = %s" for k in datos.keys() if datos[k] is not None]
                if fields:
                    query = f"UPDATE pedidos_temp SET {', '.join(fields)} WHERE telefono = %s"
                    cursor.execute(query, [datos[k] for k in datos.keys() if datos[k] is not None] + [telefono])
            else:
                cursor.execute(
                    "INSERT INTO pedidos_temp (telefono, precio, cliente, bodega, metodo_envio, productos, fecha_entrega) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (telefono, datos.get('precio'), datos.get('cliente'), datos.get('bodega'), datos.get('metodo_envio'), datos.get('productos'), datos.get('fecha_entrega'))
                )

def eliminar_pedido_temporal(telefono: str):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM pedidos_temp WHERE telefono = %s", (telefono,))
