import re

def extraer_con_regex(texto: str) -> dict:
    """
    Intenta extraer precio, tienda y origen usando expresiones regulares.
    Soporta formatos colombianos de precio (20.000, $20.000, 1.500.000).
    Ejemplo: "Pedido de $20.000 en tienda Norte desde Soacha"
    """
    datos = {
        "precio": None,
        "tienda": None,
        "origen": None,
        "metodo_envio": None
    }
    
    # Buscar precio - Soporta formatos colombianos:
    # "$20.000", "20.000", "20000", "$1.500.000", "1500000"
    precio_match = re.search(
        r'\$?\s*(\d{1,3}(?:\.\d{3})+|\d{4,})', 
        texto
    )
    if precio_match:
        precio_str = precio_match.group(1).replace(".", "")
        datos["precio"] = int(precio_str)
    
    # Buscar tienda (después de: tienda, local, sucursal, sede, punto)
    tienda_match = re.search(
        r'(?:tienda|local|sucursal|sede|punto)\s+([a-zA-Z0-9áéíóúÁÉÍÓÚñÑ ]+?)(?:\s+(?:origen|desde|procedencia|viene)|$|,|\n)',
        texto, re.IGNORECASE
    )
    if tienda_match:
        datos["tienda"] = tienda_match.group(1).strip().title()
        
    # Buscar origen (después de: origen, desde, procedencia, viene de)
    origen_match = re.search(
        r'(?:origen|desde|procedencia|viene\s+de)\s+([a-zA-Z0-9áéíóúÁÉÍÓÚñÑ ]+?)(?:\s+(?:tienda|local|sucursal|sede|punto|ruta|bicicleta|envio|envío|recoger)|$|,|\n)',
        texto, re.IGNORECASE
    )
    if origen_match:
        datos["origen"] = origen_match.group(1).strip().title()

    # Buscar metodo de envio (ruta, bicicleta, envio, recoger)
    metodo_match = re.search(r'\b(ruta|bicicleta|envio|envío|recoger)\b', texto, re.IGNORECASE)
    if metodo_match:
        metodo = metodo_match.group(1).lower()
        if metodo == 'envío':
            metodo = 'envio'
        if metodo == 'recoger':
            metodo = 'recoger en tienda'
        datos["metodo_envio"] = metodo

    return datos
