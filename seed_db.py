from db import get_connection

def seed_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Sembrar Bodegas
            bodegas = [
                ('Soacha', 'bodega sur, soacha centro'),
                ('Siberia', 'bodega norte, siberia bogota'),
                ('Paloquemao', 'centro, bogota centro, palo quemado')
            ]
            for nombre, alias in bodegas:
                cursor.execute("""
                    INSERT INTO bodegas (nombre, alias) VALUES (%s, %s)
                    ON CONFLICT (nombre) DO NOTHING
                """, (nombre, alias))
            
            # Sembrar Productos
            productos = [
                ('Lámina Roble', 'roble, lamina cafe, madera roble'),
                ('Formica Blanca', 'blanca, formica, laminado blanco'),
                ('Pegante 60k', 'pegante, pegante rojo, 60k'),
                ('Herraje Bisagra', 'bisagra, herraje, union')
            ]
            for nombre, alias in productos:
                cursor.execute("""
                    INSERT INTO productos (nombre, alias) VALUES (%s, %s)
                    ON CONFLICT (nombre) DO NOTHING
                """, (nombre, alias))
            
            print("Datos de prueba sembrados correctamente.")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_data()
