from db import get_connection

def obtener_pedido_temporal(telefono: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM pedidos_temp WHERE telefono = %s", (telefono,))
            return cursor.fetchone()
    finally:
        conn.close()

def actualizar_pedido_temporal(telefono: str, datos: dict):
    """Actualiza o crea un registro temporal con los datos proporcionados."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM pedidos_temp WHERE telefono = %s", (telefono,))
            existente = cursor.fetchone()
            
            if existente:
                # Actualizar solo los campos que vienen en 'datos' y no son None
                fields = []
                values = []
                for k, v in datos.items():
                    if v is not None:
                        fields.append(f"{k} = %s")
                        values.append(v)
                
                if fields:
                    query = f"UPDATE pedidos_temp SET {', '.join(fields)} WHERE telefono = %s"
                    values.append(telefono)
                    cursor.execute(query, tuple(values))
            else:
                cursor.execute(
                    "INSERT INTO pedidos_temp (telefono, precio, tienda, origen, metodo_envio) VALUES (%s, %s, %s, %s, %s)",
                    (telefono, datos.get('precio'), datos.get('tienda'), datos.get('origen'), datos.get('metodo_envio'))
                )
    finally:
        conn.close()

def eliminar_pedido_temporal(telefono: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM pedidos_temp WHERE telefono = %s", (telefono,))
    finally:
        conn.close()
