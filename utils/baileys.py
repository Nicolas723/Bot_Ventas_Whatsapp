import os
import requests

def enviar_mensaje_grupo_baileys(texto: str):
    """
    Envía un mensaje a un grupo de WhatsApp usando una API basada en Baileys 
    (ej: Evolution API, WAPI, o una API custom en Node.js).
    """
    url = os.getenv("BAILEYS_API_URL")
    grupo_id = os.getenv("BAILEYS_GROUP_ID")  # Ej: 1234567890-098765@g.us
    api_key = os.getenv("BAILEYS_API_KEY", "")

    if not url or not grupo_id:
        print("  [BAILEYS] OMITIDO: Configura BAILEYS_API_URL y BAILEYS_GROUP_ID en el archivo .env")
        return False

    # Este payload es un estándar común en APIs basadas en Baileys (como Evolution API o parecidas)
    # Puede que necesites ajustarlo ligeramente dependiendo de qué API exacta uses.
    payload = {
        "number": grupo_id,
        "text": texto
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    if api_key:
        headers["apikey"] = api_key  # Evolution API usa 'apikey'
        headers["Authorization"] = f"Bearer {api_key}"

    # Evolution API endpoint normal: http://URL:PORT/message/sendText/NOMBRE_INSTANCIA
    endpoint = url.rstrip('/')

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"  [BAILEYS] ¡Mensaje enviado al grupo exitosamente!")
        return True
    except Exception as e:
        print(f"  [BAILEYS] Error al enviar mensaje: {e}")
        return False
