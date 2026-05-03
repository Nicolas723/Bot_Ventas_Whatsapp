def formatear_precio(precio) -> str:
    """
    Formatea un precio en pesos colombianos.
    - Sin decimales
    - Separador de miles con punto
    - Símbolo $
    
    Ejemplos:
        20000   → "$20.000"
        1500000 → "$1.500.000"
        500     → "$500"
    """
    if precio is None:
        return "N/A"
    try:
        valor = int(float(str(precio)))
        # Formato con separador de miles usando punto (estilo colombiano)
        formateado = f"{valor:,}".replace(",", ".")
        return f"${formateado}"
    except (ValueError, TypeError):
        return str(precio)
