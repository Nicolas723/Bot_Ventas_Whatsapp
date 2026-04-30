import re

def extraer_con_regex(texto: str) -> dict:
    """
    Intenta extraer precio, tienda y origen usando expresiones regulares.
    Ejemplo: "Pedido de 500 en tienda Norte desde web"
    """
    datos = {
        "precio": None,
        "tienda": None,
        "origen": None
    }
    
    # Buscar precio (números que parezcan dinero)
    precio_match = re.search(r'\b(\d+(?:\.\d{1,2})?)\b', texto)
    if precio_match:
        datos["precio"] = float(precio_match.group(1))
    
    # Buscar tienda (palabra después de "tienda")
    tienda_match = re.search(r'tienda\s+([a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]+)', texto, re.IGNORECASE)
    if tienda_match:
        datos["tienda"] = tienda_match.group(1).capitalize()
        
    # Buscar origen (palabra después de "origen" o "desde")
    origen_match = re.search(r'(?:origen|desde)\s+([a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]+)', texto, re.IGNORECASE)
    if origen_match:
        datos["origen"] = origen_match.group(1).capitalize()
        
    return datos
