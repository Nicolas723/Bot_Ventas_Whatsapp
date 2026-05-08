from db import get_connection

def poblar_metodos():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            metodos = [
                ('Ruta', 'camion,furgon'),
                ('Bicicleta', 'bici,cicla,bicimoto,moto,motito'),
                ('Envio', 'servientrega,interrapidisimo,transportadora,envio'),
                ('Recoger en tienda', 'tienda,punto,recoger')
            ]
            for nombre, alias in metodos:
                cursor.execute("""
                    INSERT INTO metodos_envio (nombre, alias) 
                    VALUES (%s, %s) 
                    ON CONFLICT (nombre) DO UPDATE SET alias = EXCLUDED.alias
                """, (nombre, alias))
            print("Metodos de envio actualizados.")
    finally:
        conn.close()

if __name__ == "__main__":
    poblar_metodos()
