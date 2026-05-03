import requests

BASE_URL = "http://localhost:8000"

def enviar_mensaje(telefono, mensaje):
    """Simula un mensaje de WhatsApp vía Twilio webhook (Form Data)."""
    data = {
        "From": f"whatsapp:{telefono}",
        "Body": mensaje
    }
    response = requests.post(f"{BASE_URL}/webhook", data=data)
    print(f"  User: {mensaje}")
    print(f"  Bot:  (ver respuesta en WhatsApp/consola)\n")

if __name__ == "__main__":
    tel = "+573001234567"
    
    print("=" * 60)
    print("PRUEBA 1: Todo en un mensaje (lenguaje natural)")
    print("=" * 60)
    enviar_mensaje(tel, "Pedido de $20.000 en tienda Sur origen Soacha")
    input("Presiona Enter para confirmar...")
    enviar_mensaje(tel, "si")
    
    print("\n" + "=" * 60)
    print("PRUEBA 2: Paso a paso con IA")
    print("=" * 60)
    enviar_mensaje(tel, "Quiero registrar un pedido")
    input("Presiona Enter para enviar el precio...")
    enviar_mensaje(tel, "Son 150 mil pesos")
    input("Presiona Enter para enviar la tienda...")
    enviar_mensaje(tel, "Es para el local del norte")
    input("Presiona Enter para enviar el origen...")
    enviar_mensaje(tel, "Viene de Kennedy")
    input("Presiona Enter para confirmar...")
    enviar_mensaje(tel, "si")
    
    print("\n" + "=" * 60)
    print("PRUEBA 3: Modificación durante confirmación")
    print("=" * 60)
    enviar_mensaje(tel, "$20.000 tienda sur origen Soacha")
    input("Presiona Enter para modificar tienda...")
    enviar_mensaje(tel, "tienda norte")  # Modificar tienda
    input("Presiona Enter para confirmar...")
    enviar_mensaje(tel, "si")
    
    print("\n" + "=" * 60)
    print("PRUEBA 4: Múltiples modificaciones")
    print("=" * 60)
    enviar_mensaje(tel, "30000 tienda centro origen Bogotá")
    input("Presiona Enter para modificar precio...")
    enviar_mensaje(tel, "el precio es 35000")  # Modificar precio
    input("Presiona Enter para modificar origen...")
    enviar_mensaje(tel, "origen Chía")  # Modificar origen
    input("Presiona Enter para confirmar...")
    enviar_mensaje(tel, "dale")  # Confirmar con lenguaje natural
