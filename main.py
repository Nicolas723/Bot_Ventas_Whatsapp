from fastapi import FastAPI, Request, Form
from services.pedido_service import PedidoService
from db import init_db
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="WhatsApp Bot Backend (Evolution API)")

# Configuración de Evolution API (Cargar desde .env)
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME", "MiBot")

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    try:
        init_db()
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

@app.post("/webhook")
async def webhook(request: Request):
    """
    Endpoint para recibir mensajes de WhatsApp vía Evolution API.
    """
    try:
        payload = await request.json()
        print("===== INCOMING PAYLOAD FROM EVOLUTION =====")
        print(payload)
        print("===========================================")
        
        # Evolution envía diferentes eventos. Nos interesa cuando entra un mensaje.
        if payload.get("event") == "messages.upsert":
            # Extraer el bloque "data" completo
            mensaje_data = payload.get("data", {})

            if not mensaje_data:
                return {"status": "ok"}
                
            key = mensaje_data.get("key", {})
            
            # Ignorar mensajes enviados por el propio bot
            if key.get("fromMe"):
                return {"status": "ok"}

            # Extraer teléfono / remoteJid
            remoteJid = key.get("remoteJid", "")
            
            # Extraer texto (puede venir en conversation o extendedTextMessage)
            msg_content = mensaje_data.get("message", {})
            texto = msg_content.get("conversation") or msg_content.get("extendedTextMessage", {}).get("text") or ""
            
            if not texto:
                return {"status": "ok"}

            # TRATAMIENTO DE GRUPOS
            if "@g.us" in remoteJid:
                if texto.lower().strip() == "pedido":
                    respuesta_grupo = PedidoService.procesar_mensaje_grupo(remoteJid)
                    # Enviar al grupo (o dejar que el service lo envíe)
                    # En este caso, el service ya lo envía al grupo de reportes, 
                    # pero si queremos responder al MISMO grupo:
                    # enviar_mensaje_evolution_jid(remoteJid, respuesta_grupo)
                return {"status": "ok"}
                
            telefono = remoteJid.split("@")[0]
            
            # Procesar lógica del bot en privado
            respuesta = PedidoService.procesar_mensaje(telefono, texto)
            
            # Enviar respuesta de vuelta vía Evolution API
            enviar_mensaje_evolution(telefono, respuesta)

        return {"status": "ok"}
    except Exception as e:
        print(f"Error procesando webhook de Evolution API: {e}")
        return {"status": "error"}

def enviar_mensaje_evolution(telefono: str, texto: str):
    """
    Envía un mensaje de texto de vuelta al usuario vía Evolution API.
    """
    if not EVOLUTION_API_KEY:
        print("Falta configuración de Evolution API (API_KEY) en .env")
        return

    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE_NAME}"
    
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "number": telefono,
        "options": {
            "delay": 1200,
        },
        "text": texto
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code not in [200, 201]:
            print(f"Error al enviar mensaje vía Evolution API: {response.text}")
    except Exception as e:
        print(f"Error en la petición a Evolution API: {e}")

@app.get("/")
def read_root():
    return {"status": "Bot is running and ready for Evolution API"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
