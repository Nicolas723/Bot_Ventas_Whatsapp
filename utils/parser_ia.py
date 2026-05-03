import requests
import json
import os
import re
import time
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Configuración de reintentos
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 5


def _limpiar_json(texto: str) -> str:
    """Limpia la respuesta de Gemini para obtener JSON puro."""
    texto = texto.strip()
    texto = re.sub(r'^```json\s*', '', texto)
    texto = re.sub(r'^```\s*', '', texto)
    texto = re.sub(r'\s*```$', '', texto)
    return texto.strip()


def _llamar_ia(prompt: str) -> str | None:
    """Llama a Groq API con reintentos automáticos."""
    if not GROQ_API_KEY:
        print("WARN: GROQ_API_KEY no configurada. Crea una gratis en console.groq.com")
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-8b-instant", # Modelo rapidísimo y excelente para extraer JSON
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }

    for intento in range(MAX_RETRIES + 1):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                res_json = response.json()
                return res_json["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                if intento < MAX_RETRIES:
                    wait = RETRY_DELAY_SECONDS * (intento + 1)
                    print(f"  [IA] Rate limit Groq - reintentando en {wait}s...")
                    time.sleep(wait)
                    continue
                else:
                    print(f"  [IA] Rate limit agotado tras {MAX_RETRIES} reintentos.")
                    return None
            else:
                print(f"Error en Groq API: {response.text}")
                return None
        except Exception as e:
            print(f"Error llamando a Groq API: {e}")
            if intento == MAX_RETRIES:
                return None
            time.sleep(RETRY_DELAY_SECONDS)
    return None


def interpretar_con_ia(texto: str) -> dict:
    """
    Usa Google Gemini para interpretar texto natural y extraer precio, tienda, origen y metodo_envio.
    Entiende variaciones como:
    - Precio: "20 mil", "veinte mil", "$20.000", "por 20000", etc.
    - Tienda: "local norte", "sucursal centro", "sede sur", "punto calle 80", etc.
    - Origen: "viene de Soacha", "procedencia Bogotá", "desde Kennedy", etc.
    - Metodo: "ruta", "bici", "envio", "recoger", etc.
    """
    prompt = f"""Eres un asistente que extrae datos de pedidos de mensajes de WhatsApp de un negocio en Colombia.

Del siguiente mensaje, extrae estos 4 campos:
- precio: el valor numérico del pedido en pesos colombianos. Solo el número entero, sin símbolos, sin puntos de miles, sin decimales. Si dice "20 mil" interpreta como 20000. Si dice "20.000" interpreta como 20000. Si dice "un millón" interpreta como 1000000.
- tienda: el nombre de la tienda, local, sucursal, sede, punto de venta, almacén o lugar de destino del pedido. Capitaliza la primera letra de cada palabra.
- origen: el origen, procedencia, ciudad, barrio, localidad de donde viene el pedido o de donde es la venta. Capitaliza la primera letra. OJO: extrae ÚNICAMENTE el nombre. Si el usuario dice "el origen es whatsapp" o "es whatsapp", el valor debe ser SOLO "Whatsapp".
- metodo_envio: el método de entrega del pedido. Debe ser ESTRICTAMENTE uno de estos 4 valores: "ruta", "bicicleta", "envio", "recoger en tienda". Infiere el valor según el contexto del mensaje (ej. "bici" -> "bicicleta", "paso por el" -> "recoger en tienda").

REGLAS:
- Si no puedes identificar algún dato con certeza, pon null.
- No inventes datos que no están en el mensaje.
- Responde ÚNICAMENTE con un JSON válido, sin markdown, sin explicaciones, sin texto adicional.

Formato exacto de respuesta:
{{"precio": number|null, "tienda": string|null, "origen": string|null, "metodo_envio": string|null}}

Mensaje del usuario: "{texto}"
"""

    raw = _llamar_ia(prompt)
    if not raw:
        return {"precio": None, "tienda": None, "origen": None, "metodo_envio": None}

    try:
        result = json.loads(_limpiar_json(raw))
        datos = {
            "precio": int(result["precio"]) if result.get("precio") is not None else None,
            "tienda": result.get("tienda"),
            "origen": result.get("origen"),
            "metodo_envio": result.get("metodo_envio")
        }
        print(f"  [IA] Datos extraídos: {datos}")
        return datos
    except Exception as e:
        print(f"Error parseando respuesta de IA: {e} | Raw: {raw}")
        return {"precio": None, "tienda": None, "origen": None, "metodo_envio": None}


# =============================================================================
# FALLBACK INTELIGENTE PARA CONFIRMACIÓN (sin IA)
# =============================================================================

# Palabras que indican confirmación
_PALABRAS_CONFIRMAR = {
    "si", "sí", "yes", "dale", "ok", "okay", "confirmar", "confirmo",
    "correcto", "perfecto", "listo", "eso", "eso es", "está bien",
    "esta bien", "claro", "va", "sale", "de una", "hecho"
}

# Palabras que indican cancelación
_PALABRAS_CANCELAR = {
    "no", "cancelar", "anular", "nop", "nel", "cancela",
    "no quiero", "descarta", "eliminar", "olvídalo", "olvidalo"
}


def _fallback_detectar_modificacion(texto: str) -> dict:
    """
    Fallback con regex para detectar modificaciones sin necesidad de IA.
    Cubre los casos más comunes cuando la API no está disponible.
    """
    texto_lower = texto.lower().strip()

    # Verificar confirmación
    if texto_lower in _PALABRAS_CONFIRMAR:
        return {"accion": "confirmar"}

    # Verificar cancelación
    if texto_lower in _PALABRAS_CANCELAR:
        return {"accion": "cancelar"}

    # Intentar detectar modificaciones con regex
    datos_modificar = {"accion": "modificar", "precio": None, "tienda": None, "origen": None, "metodo_envio": None}
    encontro_algo = False

    # Detectar cambio de precio
    precio_match = re.search(
        r'(?:precio|valor|cuesta|son|por)?\s*\$?\s*(\d{1,3}(?:\.\d{3})+|\d{4,})',
        texto, re.IGNORECASE
    )
    if precio_match:
        precio_str = precio_match.group(1).replace(".", "")
        datos_modificar["precio"] = int(precio_str)
        encontro_algo = True

    # Detectar cambio de tienda
    tienda_match = re.search(
        r'(?:tienda|local|sucursal|sede|punto)\s+(.+?)(?:\s+(?:origen|desde|procedencia)|$|,)',
        texto, re.IGNORECASE
    )
    if tienda_match:
        datos_modificar["tienda"] = tienda_match.group(1).strip().title()
        encontro_algo = True

    # Detectar cambio de origen
    origen_match = re.search(
        r'(?:origen|desde|procedencia|viene\s+de)\s+(.+?)(?:\s+(?:tienda|local|sucursal)|$|,)',
        texto, re.IGNORECASE
    )
    if origen_match:
        datos_modificar["origen"] = origen_match.group(1).strip().title()
        encontro_algo = True

    # Detectar cambio de metodo de envio
    metodo_match = re.search(r'\b(ruta|bicicleta|envio|envío|recoger)\b', texto, re.IGNORECASE)
    if metodo_match:
        metodo = metodo_match.group(1).lower()
        if metodo == 'envío':
            metodo = 'envio'
        if metodo == 'recoger':
            metodo = 'recoger en tienda'
        datos_modificar["metodo_envio"] = metodo
        encontro_algo = True

    if encontro_algo:
        print(f"  [FALLBACK] Modificación detectada: {datos_modificar}")
        return datos_modificar

    return {"accion": "desconocido"}


def detectar_modificacion(texto: str, pedido_actual: dict) -> dict:
    """
    Usa Gemini para detectar si el usuario quiere modificar, confirmar o cancelar
    durante la fase de confirmación del pedido.
    Con fallback inteligente de regex si la API falla.
    
    Retorna:
    - {"accion": "confirmar"} si el usuario acepta
    - {"accion": "cancelar"} si el usuario rechaza
    - {"accion": "modificar", "precio": ..., "tienda": ..., "origen": ...} si quiere cambiar algo
    """
    # Primero: intentar fallback rápido para casos obvios (ahorra llamadas a API)
    texto_lower = texto.lower().strip()
    if texto_lower in _PALABRAS_CONFIRMAR:
        return {"accion": "confirmar"}
    if texto_lower in _PALABRAS_CANCELAR:
        return {"accion": "cancelar"}

    # Segundo: intentar con IA
    prompt = f"""Eres un asistente de pedidos por WhatsApp de un negocio en Colombia.

El usuario tiene un pedido pendiente de confirmación con estos datos:
- Precio: {pedido_actual.get('precio')} pesos
- Tienda: {pedido_actual.get('tienda')}
- Origen: {pedido_actual.get('origen')}
- Metodo Envio: {pedido_actual.get('metodo_envio')}

El usuario respondió con este mensaje en lugar de solo "sí" o "no":
"{texto}"

Determina la INTENCIÓN del usuario:

1. CONFIRMAR: si el usuario acepta el pedido (ejemplos: "sí", "dale", "correcto", "confirmo", "está bien", "ok", "perfecto", "eso es")
2. CANCELAR: si el usuario rechaza completamente (ejemplos: "no", "cancelar", "anular", "no quiero", "descarta")
3. MODIFICAR: si el usuario quiere cambiar algún dato específico (ejemplos: "tienda norte", "cambia el precio a 30000", "origen Bogotá", "no, es tienda centro", "es para envio")

Para MODIFICAR: pon el nuevo valor SOLO en los campos que cambian. Los que no cambian van en null.
El precio debe ser un número entero sin puntos ni símbolos.
El metodo_envio debe ser "ruta", "bicicleta", "envio", o "recoger en tienda" (o null).

Responde SOLO con JSON válido, sin markdown ni explicaciones:
- Confirmar: {{"accion": "confirmar"}}
- Cancelar: {{"accion": "cancelar"}}
- Modificar: {{"accion": "modificar", "precio": number|null, "tienda": string|null, "origen": string|null, "metodo_envio": string|null}}
"""

    raw = _llamar_ia(prompt)
    if raw:
        try:
            result = json.loads(_limpiar_json(raw))
            print(f"  [IA] Intención detectada: {result}")
            return result
        except Exception as e:
            print(f"Error parseando respuesta de IA: {e} | Raw: {raw}")

    # Tercero: fallback con regex si la IA falla
    print("  [IA] Usando fallback regex para detección de modificación...")
    return _fallback_detectar_modificacion(texto)
