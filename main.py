from fastapi import FastAPI, Request
from pydantic import BaseModel
from services.pedido_service import PedidoService
from db import init_db
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="WhatsApp Bot Backend")

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    try:
        init_db()
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

# Configuración de WhatsApp (Cargar desde .env)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "my_secret_token")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Endpoint para verificación de WhatsApp Cloud API (Meta).
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        print("Webhook verificado correctamente.")
        # Meta espera que devolvamos el challenge como texto/número
        from fastapi.responses import Response
        return Response(content=challenge, media_type="text/plain")
    
    return {"error": "Token de verificación inválido"}

@app.post("/webhook")
async def webhook(request: Request):
    """
    Recibe los mensajes reales desde la API de WhatsApp de Meta.
    """
    body = await request.json()
    
    # Imprimir body para depuración en Render (opcional)
    # print(f"Payload recibido: {body}")

    try:
        # Navegar en el JSON de Meta para extraer el mensaje y el teléfono
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                if messages:
                    message = messages[0]
                    telefono = message.get("from")
                    texto = message.get("text", {}).get("body")

                    if texto:
                        # Procesar lógica del bot
                        respuesta = PedidoService.procesar_mensaje(telefono, texto)
                        
                        # Enviar respuesta de vuelta a WhatsApp
                        enviar_mensaje_whatsapp(telefono, respuesta)

        return {"status": "ok"}
    except Exception as e:
        print(f"Error procesando webhook de Meta: {e}")
        return {"status": "error"}

def enviar_mensaje_whatsapp(telefono: str, texto: str):
    """
    Envía un mensaje de texto de vuelta al usuario vía WhatsApp Cloud API.
    """
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("Falta configuración de WhatsApp (Token o ID) para enviar mensaje.")
        return

    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "text",
        "text": {"body": texto}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Error al enviar mensaje a WhatsApp: {response.text}")
    except Exception as e:
        print(f"Error en la petición a Meta: {e}")

@app.get("/")
def read_root():
    return {"status": "Bot is running and ready for WhatsApp Cloud API"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
