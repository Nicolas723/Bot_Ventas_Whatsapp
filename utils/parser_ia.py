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
        "model": "llama-3.3-70b-versatile", # Modelo mucho más potente y capaz
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


def interpretar_con_ia(texto: str, pedido_actual: dict = None) -> dict:
    """
    Usa Groq para interpretar pedidos. Si se pasa pedido_actual, lo usa como contexto
    para no sobrescribir datos correctos con ambigüedades.
    """
    contexto = ""
    # Obtener fecha actual para referencia de la IA
    from datetime import datetime, timedelta
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    nombre_dia_hoy = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"][datetime.now().weekday()]

    contexto = ""
    if pedido_actual:
        contexto = f"""
FECHA ACTUAL: {fecha_hoy} ({nombre_dia_hoy})

CONTEXTO DEL PEDIDO ACTUAL (lo que ya sabemos):
- Precio Total: {pedido_actual.get('precio') or 'Pendiente'}
- Cliente: {pedido_actual.get('cliente') or 'Pendiente'}
- Bodega: {pedido_actual.get('bodega') or 'Pendiente'}
- Método Envío: {pedido_actual.get('metodo_envio') or 'Pendiente'}
- Fecha Entrega: {pedido_actual.get('fecha_entrega') or 'Pendiente'}
- Productos: {pedido_actual.get('productos') or 'Pendiente'}

El usuario está completando los datos faltantes o corrigiendo.
"""

    prompt = f"""Eres un experto en extracción de datos para "Laminados Beka", una empresa líder en venta de láminas, formicas, pegantes y herrajes. 
{contexto}

REGLAS DE PRECIO:
1. ¡SIEMPRE ES VALOR UNITARIO!: Cualquier precio que el usuario mencione junto a un producto es el precio de UNA unidad.
   Ejemplo: "3 laminas 200k" -> precio_unitario: 200000. (Total será 600000).
2. NO DIVIDIR: Nunca intentes dividir el precio entre la cantidad.
3. PRECIO TOTAL: El sistema calculará el total automáticamente multiplicando Cantidad x Precio Unitario.

REGLAS DE FECHA:
- Si dice "hoy", "mañana", "lunes", etc., calcula la fecha real basándote en que hoy es {fecha_hoy} ({nombre_dia_hoy}).
- Formato: YYYY-MM-DD.

EJEMPLOS:
- "Jhon, 3 laminas 300k, Soacha, ruta, para el lunes"
  -> {{"cliente": "Jhon", "bodega": "Soacha", "metodo_envio": "ruta", "fecha_entrega": "YYYY-MM-DD (del lunes)", "lista_productos": [{{"cantidad": 3, "descripcion": "laminas", "precio_unitario": 100000}}]}}

NUEVO MENSAJE: "{texto}"

Responde SOLO el JSON:
{{
  "cliente": string|null,
  "bodega": string|null,
  "metodo_envio": string|null,
  "fecha_entrega": string|null,
  "lista_productos": [
    {{"cantidad": number, "descripcion": string, "precio_unitario": number}}
  ]
}}
"""

    raw = _llamar_ia(prompt)
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

    # Segundo: intentar con IA
    prompt = f"""Eres un experto en corregir pedidos para "Laminados Beka" (especialistas en láminas y formicas). 
HOY ES: {datetime.now().strftime("%Y-%m-%d")}

PEDIDO ACTUAL:
- Cliente: {pedido_actual.get('cliente')}
- Productos: {pedido_actual.get('productos')}
- Fecha actual del pedido: {pedido_actual.get('fecha_entrega')}

MENSAJE DEL USUARIO: "{texto}"

REGLAS:
1. SI MODIFICA PRODUCTOS: Devuelve la lista COMPLETA de productos actualizada en 'lista_productos'.
2. PRECIOS: ¡SIEMPRE ES VALOR UNITARIO! Si dice "3 laminas 100k", el precio unitario es 100000.
3. FECHA: Si el usuario menciona una nueva fecha (ej: "para el lunes"), devuélvela en 'fecha_entrega'.
4. SOLO CAMBIOS: Devuelve valor SOLO para los campos que cambian. El resto null.

Responde SOLO el JSON:
{{
  "accion": "confirmar" | "cancelar" | "modificar",
  "cliente": string|null,
  "bodega": string|null,
  "metodo_envio": string|null,
  "fecha_entrega": string|null,
  "lista_productos": [
    {{"cantidad": number, "descripcion": string, "precio_unitario": number}}
  ] | null
}}
"""

    raw = _llamar_ia(prompt)
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

    prompt = f"""Extrae la fecha mencionada en el siguiente texto y devuélvela en formato YYYY-MM-DD.
HOY ES: {fecha_hoy} ({nombre_dia_hoy})

TEXTO: "{texto}"

Responde SOLO el JSON:
{{"fecha": "YYYY-MM-DD" | null}}
"""
    raw = _llamar_ia(prompt)
    if raw:
        try:
            result = json.loads(_limpiar_json(raw))
            return result.get("fecha")
        except:
            return None
    return None
