import requests
import json

BASE_URL = "http://localhost:8000"

def enviar_mensaje(telefono, mensaje):
    payload = {
        "telefono": telefono,
        "mensaje": mensaje
    }
    response = requests.post(f"{BASE_URL}/webhook", json=payload)
    print(f"User: {mensaje}")
    print(f"Bot: {response.json()['respuesta']}\n")

if __name__ == "__main__":
    tel = "123456789"
    
    # Flujo 1: Todo en uno
    print("--- PRUEBA 1: TODO EN UN MENSAJE ---")
    enviar_mensaje(tel, "Pedido de 1500 en tienda Norte desde Web")
    enviar_mensaje(tel, "si")
    
    # Flujo 2: Paso a paso
    print("--- PRUEBA 2: PASO A PASO ---")
    enviar_mensaje(tel, "Quiero registrar un pedido")
    enviar_mensaje(tel, "Es de 500 pesos")
    enviar_mensaje(tel, "Tienda Sur")
    enviar_mensaje(tel, "Origen Facebook")
    enviar_mensaje(tel, "si")
