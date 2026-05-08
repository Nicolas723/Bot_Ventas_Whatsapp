import sys
import os

# Añadir el directorio actual al path
sys.path.append(os.getcwd())

from services.pedido_manager import pedido_manager
from models.usuarios import obtener_o_crear_usuario, autorizar_usuario

def test_flujo():
    telefono_test = "573000000000"
    
    print("--- INICIANDO PRUEBAS DE REFACTOR ---")
    
    # 1. Asegurar usuario autorizado
    autorizar_usuario(telefono_test, "vendedor", "Test User")
    print("✅ Usuario de prueba autorizado.")

    # 2. Probar INTENT: Menu
    print("\n[TEST] Intención: Menu")
    res = pedido_manager.procesar_privado(telefono_test, "hola")
    print(f"Respuesta: {res}")
    assert "SISTEMA DE PEDIDOS" in res

    # 3. Probar INTENT: Productos (Listas WA)
    print("\n[TEST] Intención: Productos")
    res = pedido_manager.procesar_privado(telefono_test, "que productos tienes")
    # Como send_list devuelve None (envía por API), la respuesta debería ser None o manejada
    print(f"Respuesta (vía API): {res}")

    # 4. Probar INTENT: Crear Pedido (IA simulada)
    print("\n[TEST] Intención: Crear Pedido")
    # Nota: Esto llamará a la IA real si GROQ_API_KEY está configurada
    res = pedido_manager.procesar_privado(telefono_test, "Juan, 2 laminas soacha ruta hoy")
    print(f"Respuesta: {res}")

    print("\n--- PRUEBAS COMPLETADAS ---")

if __name__ == "__main__":
    test_flujo()
