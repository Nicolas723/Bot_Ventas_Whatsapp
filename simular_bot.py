import os
import sys
import json
from unittest.mock import MagicMock

# Mockear dependencias externas ANTES de cualquier importación de PedidoService
mock_baileys = MagicMock()
sys.modules['services.baileys_service'] = mock_baileys

from services.pedido_service import PedidoService
from db import get_connection, init_db

def limpiar_bd():
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM usuarios")
        cursor.execute("DELETE FROM pedidos_temp")
        cursor.execute("DELETE FROM pedidos")
        # Asegurar un admin base
        cursor.execute("INSERT INTO usuarios (telefono, rol, estado) VALUES ('573505350587', 'admin', 'inicio')")
    conn.commit()
    conn.close()

def clean_text(text):
    return text.encode('ascii', 'ignore').decode('ascii')

def simular_chat(telefono, mensaje, label="USER"):
    print(f"\n[{label} {telefono}]: {mensaje}")
    try:
        respuesta = PedidoService.procesar_mensaje(telefono, mensaje)
        print(f"[BOT]: {clean_text(respuesta)}")
        return respuesta
    except Exception as e:
        print(f"[ERROR EN BOT]: {e}")
        raise e

def test_flujo_completo():
    print("\n--- TEST: FLUJO COMPLETO (AUTORIZACION + PEDIDO) ---")
    limpiar_bd()
    
    # 1. El vendedor intenta entrar
    simular_chat("573001112233", "Hola")
    simular_chat("573001112233", "Soy Alejo")
    
    # 2. El admin autoriza
    simular_chat("573505350587", "autorizar 573001112233", "ADMIN")
    simular_chat("573505350587", "si", "ADMIN")
    
    # 3. El vendedor ahora sí puede pedir
    simular_chat("573001112233", "Hola")
    simular_chat("573001112233", "Juan, 1 colbon y 2 pinturas, Castilla, hoy")
    
    # 4. Error de bodega -> Consulta
    simular_chat("573001112233", "bodegas")
    simular_chat("573001112233", "Ok") # Debería recordarle que falta bodega
    
    # 5. Corrección y cierre
    simular_chat("573001112233", "Siberia")
    simular_chat("573001112233", "Moto")
    simular_chat("573001112233", "si")

    # 6. Cambiar rol de Alejo a Admin
    print("\n--- TEST: CAMBIO DE ROL ---")
    simular_chat("573505350587", "rol 573001112233 admin", "ADMIN")
    simular_chat("573505350587", "si", "ADMIN")
    
    # 7. Alejo ahora debería ver el menú de admin
    simular_chat("573001112233", "Hola")

if __name__ == "__main__":
    init_db()
    try:
        test_flujo_completo()
        print("\nPruebas de simulacion completadas exitosamente.")
    except Exception as e:
        print(f"\nCRASH DETECTADO:")
        import traceback
        traceback.print_exc()
