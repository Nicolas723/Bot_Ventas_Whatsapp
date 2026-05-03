import os
import requests

def enviar_mensaje_grupo_baileys(texto: str, jid: str = None):
    """
    Envía un mensaje a un grupo de WhatsApp usando una API basada en Baileys.
    """
    url = os.getenv("BAILEYS_API_URL")
    grupo_id = jid or os.getenv("BAILEYS_GROUP_ID")
    api_key = os.getenv("BAILEYS_API_KEY", "")

    if not url or not grupo_id:
        print("  [BAILEYS] OMITIDO: Configura BAILEYS_API_URL y BAILEYS_GROUP_ID")
        return False

    payload = {
        "number": grupo_id,
        "text": texto
    }
    
    headers = {
        "Content-Type": "application/json",
        "apikey": api_key
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"  [BAILEYS] Error al enviar mensaje: {e}")
        return False
