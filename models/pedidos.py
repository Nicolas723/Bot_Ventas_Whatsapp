from db import get_db_conn
import json
from datetime import datetime

def guardar_pedido_final(telefono: str, precio: float, cliente: str, bodega: str, metodo_envio: str, productos: str, fecha_entrega: str = None):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            if not fecha_entrega:
                fecha_entrega = datetime.now().strftime("%Y-%m-%d")
                
            cursor.execute(
                "INSERT INTO pedidos (telefono, precio, cliente, bodega, metodo_envio, productos, fecha_entrega, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, 'pendiente')",
                (telefono, precio, cliente, bodega, metodo_envio, productos, fecha_entrega)
            )

def modificar_pedido_final(pedido_id: int, modificado_por: str, nuevos_datos: dict):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            # 1. Obtener datos actuales
            cursor.execute("SELECT * FROM pedidos WHERE id = %s", (pedido_id,))
            actual = cursor.fetchone()
            if not actual: return False
            
            # 2. Guardar en historial
            cursor.execute("""
                INSERT INTO historial_pedidos (pedido_id, datos_previos, modificado_por)
                VALUES (%s, %s, %s)
            """, (pedido_id, json.dumps(actual, default=str), modificado_por))
            
            # 3. Aplicar cambios
            fields = [f"{k} = %s" for k in nuevos_datos.keys()]
            if fields:
                query = f"UPDATE pedidos SET {', '.join(fields)} WHERE id = %s"
                cursor.execute(query, list(nuevos_datos.values()) + [pedido_id])
            return True

def obtener_pedidos_con_filtros(telefono: str = None, rol: str = 'admin', estado: str = None, fecha: str = 'hoy'):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            query = "SELECT p.*, u.nombre as vendedor FROM pedidos p JOIN usuarios u ON p.telefono = u.telefono WHERE 1=1"
            params = []
            
            if rol == 'vendedor' and telefono:
                query += " AND p.telefono = %s"
                params.append(telefono)
                
            if estado:
                query += " AND p.estado = %s"
                params.append(estado)
                
            if fecha == 'hoy':
                query += " AND p.fecha_entrega = CURRENT_DATE"
            
            query += " ORDER BY p.fecha_entrega DESC, p.metodo_envio"
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

def marcar_pedido_entregado(pedido_id: int):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE pedidos SET estado = 'entregado', fecha_entregado = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (pedido_id,))

def guardar_contexto_grupo(jid: str, lista_ids: list):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO contexto_grupos (jid, lista_pedidos_ids) VALUES (%s, %s)
                ON CONFLICT (jid) DO UPDATE SET lista_pedidos_ids = %s
            """, (jid, lista_ids, lista_ids))

def obtener_contexto_grupo(jid: str):
    with get_db_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT lista_pedidos_ids FROM contexto_grupos WHERE jid = %s", (jid,))
            res = cursor.fetchone()
            return res['lista_pedidos_ids'] if res else []

def obtener_pedidos_hoy():
    """Retorna todos los pedidos registrados con fecha de hoy."""
    return obtener_pedidos_con_filtros(fecha='hoy', rol='admin')
