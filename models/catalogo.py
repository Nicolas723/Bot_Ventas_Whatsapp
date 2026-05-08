from db import get_db_conn

class CatalogoModel:
    @staticmethod
    def obtener_bodegas():
        """Retorna lista de bodegas registradas."""
        with get_db_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT nombre FROM bodegas ORDER BY nombre")
                return [r['nombre'] for r in cursor.fetchall()]

    @staticmethod
    def obtener_productos():
        """Retorna lista de productos registrados."""
        with get_db_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT nombre FROM productos ORDER BY nombre")
                return [r['nombre'] for r in cursor.fetchall()]

    @staticmethod
    def obtener_metodos_envio():
        """Retorna los métodos de envío fijos."""
        return ["Ruta", "Bicicleta", "Recoger en punto", "Transportadora"]

    @staticmethod
    def es_fecha_bloqueada(fecha):
        """Verifica si una fecha está bloqueada para entregas."""
        with get_db_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM fechas_bloqueadas WHERE fecha = %s", (fecha,))
                return cursor.fetchone() is not None

catalogo_model = CatalogoModel()
