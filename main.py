from fastapi import FastAPI, Request
from handlers.private import PrivateHandler
from handlers.group import GroupHandler
from services.whatsapp import whatsapp
from db import init_db
from utils.logger import logger
import uvicorn
import os

app = FastAPI(title="Beka Bot Operativo")

@app.on_event("startup")
def startup():
    init_db()
    logger.info("Bot iniciado y base de datos conectada.")

@app.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
        if payload.get("event") != "messages.upsert":
            return {"status": "ignored"}

        data = payload.get("data", {})
        if not data or data.get("key", {}).get("fromMe"):
            return {"status": "ignored"}

        remoteJid = data.get("key", {}).get("remoteJid", "")
        msg = data.get("message", {})
        
        texto = (
            msg.get("conversation") or 
            msg.get("extendedTextMessage", {}).get("text") or 
            msg.get("buttonsResponseMessage", {}).get("selectedButtonId") or 
            msg.get("listResponseMessage", {}).get("title") or 
            ""
        )

        if not texto: return {"status": "empty"}

        if "@g.us" in remoteJid:
            respuesta = GroupHandler.handle(remoteJid, texto)
            if respuesta: whatsapp.send_to_group(remoteJid, respuesta)
        else:
            telefono = remoteJid.split("@")[0]
            respuesta = PrivateHandler.handle(telefono, texto)
            if respuesta: whatsapp.send_text(telefono, respuesta)

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error crítico en webhook: {e}")
        return {"status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

