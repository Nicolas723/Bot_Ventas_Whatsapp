import re

def normalizar_telefono(telefono_raw: str) -> str:
    """
    Limpia el teléfono de espacios, signos y asegura el código de país 57 (Colombia)
    si no está presente.
    """
    if not telefono_raw: return ""
    
    # Solo números
    solo_numeros = re.sub(r'\D', '', telefono_raw)
    
    # Si tiene 10 dígitos (formato local Colombia), agregar 57
    if len(solo_numeros) == 10:
        return "57" + solo_numeros
    
    # Si ya tiene 12 dígitos y empieza con 57, dejarlo así
    if len(solo_numeros) == 12 and solo_numeros.startswith("57"):
        return solo_numeros
        
    return solo_numeros
