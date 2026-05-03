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
                        if isinstance(v, str) and k != 'productos':
                            v = v.replace('\n', ' ').replace('\r', '').strip()
                        fields.append(f"{k} = %s")
                        values.append(v)
                
                if fields:
                    query = f"UPDATE pedidos_temp SET {', '.join(fields)} WHERE telefono = %s"
                    values.append(telefono)
                    cursor.execute(query, tuple(values))
            else:
                precio = datos.get('precio')
                cliente = datos.get('cliente').replace('\n', ' ').strip() if isinstance(datos.get('cliente'), str) else datos.get('cliente')
                bodega = datos.get('bodega').replace('\n', ' ').strip() if isinstance(datos.get('bodega'), str) else datos.get('bodega')
                metodo_envio = datos.get('metodo_envio').replace('\n', ' ').strip() if isinstance(datos.get('metodo_envio'), str) else datos.get('metodo_envio')
                productos = datos.get('productos')
                
                cursor.execute(
                    "INSERT INTO pedidos_temp (telefono, precio, cliente, bodega, metodo_envio, productos) VALUES (%s, %s, %s, %s, %s, %s)",
                    (telefono, precio, cliente, bodega, metodo_envio, productos)
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
