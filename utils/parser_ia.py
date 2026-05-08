import requests
import json
import os
import re
import time
from dotenv import load_dotenv
from utils.formato import formatear_precio

from config import config

GROQ_API_KEY = config.GROQ_API_KEY
IA_MODEL = config.IA_MODEL

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


def _llamar_ia(system_prompt: str, user_prompt: str) -> str | None:
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
        "model": IA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
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


def interpretar_con_ia(texto: str, pedido_actual: dict = None) -> dict:
    """
    Usa Groq para interpretar pedidos. Si se pasa pedido_actual, lo usa como contexto
    para no sobrescribir datos correctos con ambigüedades.
    """
    from datetime import datetime
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    nombre_dia_hoy = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"][datetime.now().weekday()]

    SYSTEM_PROMPT = """Eres un sistema experto en extracción estructurada de pedidos para "Laminados Beka", empresa especializada en láminas, formicas, pegantes y herrajes.

Tu única función es convertir mensajes de usuarios en JSON estructurado.

REGLAS CRÍTICAS:

1. PRECIOS:
- TODO número asociado a un producto es SIEMPRE precio_unitario.
- NUNCA es precio total.
- NUNCA dividas valores.
- El total será calculado externamente.

2. PRODUCTOS:
- Extrae cada producto en una lista.
- Si falta cantidad, asumir 1.
- Si falta precio, usar 0.

3. FECHAS:
- Convierte fechas relativas ("hoy", "mañana", "lunes") a formato YYYY-MM-DD.
- Usa como referencia la fecha actual proporcionada.

4. DATOS:
- cliente → nombre de persona
- bodega → ubicación o destino
- metodo_envio → valores típicos: ruta, envio, recoger en tienda
- fecha_entrega → fecha en formato YYYY-MM-DD

5. CONTEXTO:
- Si se proporciona información previa, NO sobrescribas datos correctos.
- Solo completa o corrige lo necesario.

6. SALIDA:
- Responde ÚNICAMENTE con JSON válido.
- No expliques nada.
- No agregues texto adicional.

FORMATO DE RESPUESTA:

{
  "cliente": string | null,
  "bodega": string | null,
  "metodo_envio": string | null,
  "fecha_entrega": string | null,
  "lista_productos": [
    {
      "cantidad": number,
      "descripcion": string,
      "precio_unitario": number
    }
  ]
}"""

    USER_PROMPT = f"""FECHA ACTUAL: {fecha_hoy} ({nombre_dia_hoy})

CONTEXTO DEL PEDIDO ACTUAL:
- cliente: {pedido_actual.get('cliente') if pedido_actual else None}
- bodega: {pedido_actual.get('bodega') if pedido_actual else None}
- metodo_envio: {pedido_actual.get('metodo_envio') if pedido_actual else None}
- fecha_entrega: {pedido_actual.get('fecha_entrega') if pedido_actual else None}
- productos: {pedido_actual.get('productos') if pedido_actual else None}

EJEMPLOS:

Input: "3 laminas 200k soacha mañana"
Output:
{{"cliente": null, "bodega": "Soacha", "metodo_envio": null, "fecha_entrega": "YYYY-MM-DD", "lista_productos":[{{"cantidad":3,"descripcion":"laminas","precio_unitario":200000}}]}}

Input: "Pedro 5 formicas 150000 ruta hoy"
Output:
{{"cliente":"Pedro","bodega":null,"metodo_envio":"ruta","fecha_entrega":"YYYY-MM-DD","lista_productos":[{{"cantidad":5,"descripcion":"formicas","precio_unitario":150000}}]}}

Input: "2 laminas"
Output:
{{"cliente":null,"bodega":null,"metodo_envio":null,"fecha_entrega":null,"lista_productos":[{{"cantidad":2,"descripcion":"laminas","precio_unitario":0}}]}}

Input: "para el lunes 3 laminas 100k"
Output:
{{"cliente":null,"bodega":null,"metodo_envio":null,"fecha_entrega":"YYYY-MM-DD","lista_productos":[{{"cantidad":3,"descripcion":"laminas","precio_unitario":100000}}]}}

Input: "10 pegantes 50k cada uno enviar"
Output:
{{"cliente":null,"bodega":null,"metodo_envio":"envio","fecha_entrega":null,"lista_productos":[{{"cantidad":10,"descripcion":"pegantes","precio_unitario":50000}}]}}

MENSAJE DEL USUARIO:
"{texto}" """

    raw = _llamar_ia(SYSTEM_PROMPT, USER_PROMPT)
    if not raw:
        return {"precio": None, "cliente": None, "bodega": None, "metodo_envio": None, "fecha_entrega": None, "productos": None}

    try:
        result = json.loads(_limpiar_json(raw))
        
        # Calcular el precio total y formatear los productos en Python para evitar errores de la IA
        total_acumulado = 0
        productos_formateados = []
        
        if result.get("lista_productos"):
            for p in result["lista_productos"]:
                cant = p.get("cantidad", 1)
                p_unit = p.get("precio_unitario", 0)
                desc = p.get("descripcion", "Producto")
                subtotal = cant * p_unit
                total_acumulado += subtotal
                # Mostrar el precio unitario claramente en el resumen
                productos_formateados.append(f"{cant} {desc} - {formatear_precio(p_unit)} c/u (Total: {formatear_precio(subtotal)})")

        datos = {
            "precio": total_acumulado if total_acumulado > 0 else None,
            "cliente": result.get("cliente"),
            "bodega": result.get("bodega"),
            "metodo_envio": result.get("metodo_envio"),
            "fecha_entrega": result.get("fecha_entrega"),
            "productos": "\n".join(productos_formateados) if productos_formateados else None
        }
        print(f"  [IA] Datos extraídos: {datos}")
        return datos
    except Exception as e:
        print(f"Error parseando respuesta de IA: {e} | Raw: {raw}")
        return {"precio": None, "cliente": None, "bodega": None, "metodo_envio": None, "productos": None}


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
    Usa IA para detectar si el usuario quiere modificar, confirmar o cancelar.
    """
    # Primero: intentar fallback rápido para casos obvios
    texto_lower = texto.lower().strip()
    if texto_lower in _PALABRAS_CONFIRMAR:
        return {"accion": "confirmar"}
    if texto_lower in _PALABRAS_CANCELAR:
        return {"accion": "cancelar"}

    from datetime import datetime
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    dia_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"][datetime.now().weekday()]

    system_prompt = """Eres un sistema experto en análisis y corrección de pedidos para "Laminados Beka".

Tu función es interpretar si el usuario quiere:
1. confirmar el pedido
2. cancelar el pedido
3. modificar el pedido

REGLAS CRÍTICAS:

1. INTENCIÓN:
- "sí", "ok", "listo", "confirmar" → confirmar
- "no", "cancelar", "anular" → cancelar
- cualquier cambio en datos → modificar

2. MODIFICACIONES:
- SOLO devuelve los campos que cambian
- NO repitas datos que no cambian
- Si no hay cambios claros → accion = "desconocido"

3. PRODUCTOS:
- Tu objetivo es una FUSIÓN INTELIGENTE.
- Si el usuario menciona un cambio en un producto (ej: "son 2"), busca ese producto en el PEDIDO ACTUAL y actualiza su cantidad o precio.
- MANTÉN todos los demás productos que estaban en el pedido previo. NUNCA los elimines a menos que el usuario diga "quita", "borra" o "elimina".
- Devuelve SIEMPRE la lista de productos COMPLETA resultante de la fusión.

4. PRECIOS:
- TODO número asociado a producto es SIEMPRE precio_unitario
- NUNCA es total
- NUNCA dividir valores

5. FECHAS:
- Convierte fechas relativas a formato YYYY-MM-DD

6. CONSERVACIÓN:
- No inventes datos
- Si no estás seguro → devuelve null

7. SALIDA:
- Responde SOLO JSON válido
- Sin texto adicional

FORMATO:

{
  "accion": "confirmar" | "cancelar" | "modificar" | "desconocido",
  "cliente": string | null,
  "bodega": string | null,
  "metodo_envio": string | null,
  "fecha_entrega": string | null,
  "lista_productos": [
    {
      "cantidad": number,
      "descripcion": string,
      "precio_unitario": number
    }
  ] | null
}"""

    user_prompt = f"""FECHA ACTUAL: {fecha_hoy} ({dia_semana})

PEDIDO ACTUAL:
- cliente: {pedido_actual.get('cliente')}
- bodega: {pedido_actual.get('bodega')}
- metodo_envio: {pedido_actual.get('metodo_envio')}
- fecha_entrega: {pedido_actual.get('fecha_entrega')}
- productos: {pedido_actual.get('productos')}

EJEMPLOS:

Input: "sí"
Output:
{{"accion":"confirmar","cliente":null,"bodega":null,"metodo_envio":null,"fecha_entrega":null,"lista_productos":null}}

Input: "cancelar"
Output:
{{"accion":"cancelar","cliente":null,"bodega":null,"metodo_envio":null,"fecha_entrega":null,"lista_productos":null}}

Input: "cambia la fecha para mañana"
Output:
{{"accion":"modificar","cliente":null,"bodega":null,"metodo_envio":null,"fecha_entrega":"YYYY-MM-DD","lista_productos":null}}

Input: "envio en vez de ruta"
Output:
{{"accion":"modificar","cliente":null,"bodega":null,"metodo_envio":"envio","fecha_entrega":null,"lista_productos":null}}

Input: "ahora son 5 laminas 200k"
Output:
{{"accion":"modificar","cliente":null,"bodega":null,"metodo_envio":null,"fecha_entrega":null,"lista_productos":[{{"cantidad":5,"descripcion":"laminas","precio_unitario":200000}}]}}

Input: "es para soacha"
Output:
{{"accion":"modificar","cliente":null,"bodega":"Soacha","metodo_envio":null,"fecha_entrega":null,"lista_productos":null}}

Input: "todo bien"
Output:
{{"accion":"confirmar","cliente":null,"bodega":null,"metodo_envio":null,"fecha_entrega":null,"lista_productos":null}}

Input: "son 2 laminas" (Contexto previo tiene: 1 lamina y 5 pegantes)
Output:
{"accion":"modificar","cliente":null,"bodega":null,"metodo_envio":null,"fecha_entrega":null,"lista_productos":[{"cantidad":2,"descripcion":"laminas","precio_unitario":100000},{"cantidad":5,"descripcion":"pegantes","precio_unitario":50000}]}

Input: "no, mejor 3 laminas 150k y para el lunes"
Output:
{{"accion":"modificar","cliente":null,"bodega":null,"metodo_envio":null,"fecha_entrega":"YYYY-MM-DD","lista_productos":[{{"cantidad":3,"descripcion":"laminas","precio_unitario":150000}}]}}

MENSAJE DEL USUARIO:
"{texto}" """

    raw = _llamar_ia(system_prompt, user_prompt)
    if raw:
        try:
            result = json.loads(_limpiar_json(raw))
            
            if result.get("accion") == "modificar":
                # Recalcular precio y formatear productos si hubo cambios en la lista
                if result.get("lista_productos"):
                    total_acumulado = 0
                    productos_formateados = []
                    for p in result["lista_productos"]:
                        cant = p.get("cantidad", 1)
                        p_unit = p.get("precio_unitario", 0)
                        desc = p.get("descripcion", "Producto")
                        subtotal = cant * p_unit
                        total_acumulado += subtotal
                        productos_formateados.append(f"{cant} {desc} - {formatear_precio(p_unit)} c/u (Total: {formatear_precio(subtotal)})")
                    
                    result["precio"] = total_acumulado
                    result["productos"] = "\n".join(productos_formateados)
            
            print(f"  [IA] Intención detectada: {result}")
            return result
        except Exception as e:
            print(f"Error parseando respuesta de IA: {e} | Raw: {raw}")

    # Tercero: fallback con regex
    print("  [IA] Usando fallback regex para detección de modificación...")
    return _fallback_detectar_modificacion(texto)
def extraer_fecha_con_ia(texto: str) -> str | None:
    """Extrae una fecha en formato YYYY-MM-DD del texto usando IA."""
    from datetime import datetime
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    nombre_dia_hoy = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"][datetime.now().weekday()]

    system_prompt = "Eres un experto en extracción de fechas para Laminados Beka. Responde ÚNICAMENTE con JSON."
    user_prompt = f"""Extrae la fecha mencionada en el siguiente texto y devuélvela en formato YYYY-MM-DD.
HOY ES: {fecha_hoy} ({nombre_dia_hoy})

TEXTO: "{texto}"

Responde SOLO el JSON:
{{"fecha": "YYYY-MM-DD" | null}}
"""
    raw = _llamar_ia(system_prompt, user_prompt)
    if raw:
        try:
            result = json.loads(_limpiar_json(raw))
            return result.get("fecha")
        except:
            return None
    return None
