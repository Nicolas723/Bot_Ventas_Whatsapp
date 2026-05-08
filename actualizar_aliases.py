from db import get_connection

def actualizar_aliases():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            updates = [
                ('Bicicleta', 'bici,cicla,bicimoto,moto,motito,run run,motocicleta'),
                ('Ruta', 'camion,furgon,carro,vehiculo,camioneta'),
                ('Envio', 'servientrega,interrapidisimo,transportadora,envio,correo,paqueteria'),
                ('Recoger en tienda', 'tienda,punto,recoger,local,oficina')
            ]
            for nombre, alias in updates:
                cursor.execute("""
                    UPDATE metodos_envio SET alias = %s WHERE nombre = %s
                """, (alias, nombre))
            print("Aliases actualizados con éxito.")
    finally:
        conn.close()

if __name__ == "__main__":
    actualizar_aliases()
