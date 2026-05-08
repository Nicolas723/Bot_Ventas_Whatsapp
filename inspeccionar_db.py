from db import get_connection

def inspeccionar_configuracion():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM configuracion")
            filas = cursor.fetchall()
            print("Contenido de configuracion:")
            for f in filas:
                print(f)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspeccionar_configuracion()
