from db import get_connection

def limpiar_usuarios():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            print("Limpiando tabla de usuarios...")
            cursor.execute("TRUNCATE TABLE usuarios CASCADE")
            conn.commit()
            print("Tabla de usuarios vaciada.")
    except Exception as e:
        print(f"Error limpiando tabla: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    limpiar_usuarios()
