import os
from db import get_connection
from rapidfuzz import process, fuzz

def normalizar_valor(texto, tabla):
    """
    Busca el mejor match para un texto en una tabla (productos o bodegas).
    Retorna (nombre_real, id, score)
    """
    if not texto: return None, None, 0
    
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT id, nombre, alias FROM {tabla}")
            rows = cursor.fetchall()
            
            choices = []
            id_map = {}
            for r in rows:
                choices.append(r['nombre'])
                id_map[r['nombre']] = r['id']
                if r['alias']:
                    for alias in r['alias'].split(','):
                        choices.append(alias.strip())
                        id_map[alias.strip()] = r['id']
                        # También mapeamos el alias al nombre real
                        id_map[alias.strip() + "_real"] = r['nombre']

            if not choices: return texto, None, 0
            
            # Fuzzy matching
            result = process.extractOne(texto, choices, scorer=fuzz.WRatio)
            if result:
                match_text, score, _ = result
                real_id = id_map.get(match_text)
                real_name = id_map.get(match_text + "_real", match_text)
                return real_name, real_id, score
                
            return texto, None, 0
    finally:
        conn.close()

def sugerir_productos(texto, limite=3):
    """Retorna hasta N sugerencias para un producto."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT nombre FROM productos")
            choices = [r['nombre'] for r in cursor.fetchall()]
            
            results = process.extract(texto, choices, scorer=fuzz.WRatio, limit=limite)
            return [r[0] for r in results if r[1] > 50]
    finally:
        conn.close()
