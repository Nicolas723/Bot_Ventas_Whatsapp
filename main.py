from fastapi import FastAPI, Request, Form
from services.pedido_service import PedidoService
from db import init_db
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="WhatsApp Bot Backend (Twilio)")

# Configuración de Twilio (Cargar desde .env)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "whatsapp:+14155238886") # Número de Sandbox por defecto

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    try:
        init_db()
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

@app.post("/webhook")
async def webhook(From: str = Form(...), Body: str = Form(...)):
    """
    Endpoint para recibir mensajes de WhatsApp vía Twilio.
    Twilio envía los datos como Form Data.
    """
    try:
        # Twilio envía el teléfono como 'whatsapp:+521...'
        telefono = From.replace("whatsapp:", "")
        texto = Body

        if texto:
            # Procesar lógica del bot
            respuesta = PedidoService.procesar_mensaje(telefono, texto)
            
            # Enviar respuesta de vuelta vía Twilio
            enviar_mensaje_twilio(telefono, respuesta)

        return {"status": "ok"}
    except Exception as e:
        print(f"Error procesando webhook de Twilio: {e}")
        return {"status": "error"}

def enviar_mensaje_twilio(telefono: str, texto: str):
    """
    Envía un mensaje de texto de vuelta al usuario vía la API de Twilio.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("Falta configuración de Twilio (SID o Token) en .env")
        return

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    
    # Twilio requiere Basic Auth (SID como usuario, Token como contraseña)
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    data = {
        "From": TWILIO_PHONE_NUMBER,
        "To": f"whatsapp:{telefono}",
        "Body": texto
    }
    
    try:
        response = requests.post(url, data=data, auth=auth)
        if response.status_code not in [200, 201]:
            print(f"Error al enviar mensaje vía Twilio: {response.text}")
    except Exception as e:
        print(f"Error en la petición a Twilio: {e}")

@app.get("/")
def read_root():
    return {"status": "Bot is running and ready for Twilio WhatsApp Sandbox"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
