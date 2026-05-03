from db import get_connection

def bloquear_fecha(fecha: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO fechas_bloqueadas (fecha) VALUES (%s) ON CONFLICT DO NOTHING", (fecha,))
    finally:
        conn.commit()
        conn.close()

def desbloquear_fecha(fecha: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM fechas_bloqueadas WHERE fecha = %s", (fecha,))
    finally:
        conn.commit()
        conn.close()

def es_fecha_bloqueada(fecha: str) -> bool:
    if not fecha: return False
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM fechas_bloqueadas WHERE fecha = %s", (fecha,))
            return cursor.fetchone() is not None
    finally:
        conn.close()
