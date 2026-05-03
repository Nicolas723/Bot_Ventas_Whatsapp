"""
Test local del bot - Ejecuta la lógica directamente sin necesidad de Twilio.
Muestra las respuestas del bot en consola.

Uso: python test_local.py
"""
import sys
import os

# Forzar UTF-8 en consola Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from db import init_db
from services.pedido_service import PedidoService
from models.pedidos_temp import eliminar_pedido_temporal
from models.usuarios import actualizar_estado_usuario

TEL = "+573009999999"

def reset_usuario():
    """Limpia el estado del usuario de prueba."""
    try:
        actualizar_estado_usuario(TEL, 'inicio')
        eliminar_pedido_temporal(TEL)
    except:
        pass

def enviar(mensaje: str):
    """Simula un mensaje y muestra la respuesta del bot."""
    print(f"\n  👤 User: {mensaje}")
    respuesta = PedidoService.procesar_mensaje(TEL, mensaje)
    print(f"  🤖 Bot:\n")
    for linea in respuesta.split("\n"):
        print(f"       {linea}")
    print()
    return respuesta

def separador(titulo: str):
    print("\n" + "=" * 60)
    print(f"  {titulo}")
    print("=" * 60)

if __name__ == "__main__":
    print("Inicializando base de datos...")
    init_db()
    
    # ===== PRUEBA 1: Mensaje con keywords exactos (regex) =====
    separador("PRUEBA 1: Keywords exactos (regex)")
    reset_usuario()
    enviar("20000 tienda sur origen Soacha")
    enviar("si")
    
    # ===== PRUEBA 2: Lenguaje natural (IA) =====
    separador("PRUEBA 2: Lenguaje natural (IA)")
    reset_usuario()
    enviar("Tengo un pedido de 150 mil pesos para el local del norte, viene de Kennedy")
    enviar("dale")
    
    # ===== PRUEBA 3: Paso a paso =====
    separador("PRUEBA 3: Datos paso a paso")
    reset_usuario()
    enviar("Quiero registrar un pedido")
    enviar("Son 25 mil pesos")
    enviar("Es para la sucursal centro")
    enviar("Viene de Soacha")
    enviar("correcto")
    
    # ===== PRUEBA 4: Modificación en confirmación =====
    separador("PRUEBA 4: Modificar durante confirmación")
    reset_usuario()
    enviar("$20.000 tienda sur origen Soacha")
    enviar("tienda norte")  # Modificar
    enviar("si")
    
    # ===== PRUEBA 5: Múltiples modificaciones =====
    separador("PRUEBA 5: Varias modificaciones seguidas")
    reset_usuario()
    enviar("30000 tienda centro origen Bogotá")
    enviar("el precio es 35000")
    enviar("origen Chía")
    enviar("perfecto")
    
    print("\n✅ Todas las pruebas ejecutadas.")
