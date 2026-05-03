"""
Test del flujo completo con registro de vendedor y método de envío.
"""
import sys
import os
import time

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from db import init_db, get_connection
from services.pedido_service import PedidoService
from models.pedidos_temp import eliminar_pedido_temporal

TEL = "+573009999999"

def reset():
    # Eliminar usuario para forzar registro
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM usuarios WHERE telefono = %s", (TEL,))
            cursor.execute("DELETE FROM pedidos WHERE telefono = %s", (TEL,))
            conn.commit()
    except Exception as e:
        print(f"Error reseteando: {e}")
    finally:
        conn.close()
    eliminar_pedido_temporal(TEL)

def enviar(mensaje: str):
    print(f"\n  >>> User: {mensaje}")
    respuesta = PedidoService.procesar_mensaje(TEL, mensaje)
    print(f"  <<< Bot:")
    for linea in respuesta.split("\n"):
        print(f"       {linea}")
    return respuesta

if __name__ == "__main__":
    init_db()
    reset()
    
    print("\n" + "=" * 60)
    print("  PRUEBA: Registro → Pedido (Ruta) → Modificación → Confirmación")
    print("=" * 60)
    
    # 1. Primer mensaje (debería pedir nombre)
    enviar("hola")
    
    # 2. Registrar nombre
    enviar("Juan Perez")
    
    # 3. Enviar datos completos
    enviar("20000 tienda sur origen Soacha en bicicleta")
    
    # 4. Modificar método de envío
    enviar("es para ruta")
    
    # 5. Confirmar
    enviar("si")
    
    print("\n" + "=" * 60)
    print("  RESULTADO: Verifica el resumen del grupo arriba")
    print("=" * 60)
