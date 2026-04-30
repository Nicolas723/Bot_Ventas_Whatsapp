from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.pedido_service import PedidoService
from db import init_db

app = FastAPI(title="WhatsApp Bot Backend")

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    try:
        init_db()
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

class WebhookData(BaseModel):
    telefono: str
    mensaje: str

@app.post("/webhook")
async def webhook(data: WebhookData):
    """
    Endpoint principal que recibe mensajes de WhatsApp.
    """
    try:
        respuesta = PedidoService.procesar_mensaje(data.telefono, data.mensaje)
        return {"respuesta": respuesta}
    except Exception as e:
        # En producción, usar logging adecuado
        print(f"Error procesando mensaje: {e}")
        return {"respuesta": "Lo siento, ocurrió un error interno. Intenta más tarde."}

@app.get("/")
def read_root():
    return {"status": "Bot is running"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
