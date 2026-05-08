from db import get_connection

def listar_tablas():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            tablas = cursor.fetchall()
            print("Tablas encontradas:")
            for t in tablas:
                print(f"- {t['table_name']}")
    finally:
        conn.close()

if __name__ == "__main__":
    listar_tablas()
