import re
from utils.normalizacion import normalizar_valor

class IntentService:
    @staticmethod
    def detectar(mensaje: str) -> dict:
        """
        Detección global de intenciones para comandos directos.
        """
        msg = mensaje.lower().strip()
        
        # 1. Comandos de Escape (Prioridad)
        if msg in ["hola", "inicio", "ayuda", "menu", "menú", "comandos", "opciones"]:
            return {"intent": "ver_menu", "data": None}
            
        # 2. Consultas Rápidas
        if any(k in msg for k in ["producto", "precios", "catálogo", "catalogo"]):
            return {"intent": "ver_productos", "data": None}
            
        if any(k in msg for k in ["bodega", "donde hay", "sedes", "puntos"]):
            return {"intent": "ver_bodegas", "data": None}
            
        # 3. Consultas de Pedidos (Vendedor/Admin)
        if msg in ["pedidos", "pedido", "lista de pedidos"]:
            return {"intent": "ver_pedidos", "data": "todos"}
            
        # 4. Confirmaciones/Cancelaciones
        if msg in ["si", "sí", "confirmar", "dale", "ok", "listo"]:
            return {"intent": "confirmar", "data": None}
            
        if msg in ["no", "cancelar", "anular", "parar"]:
            return {"intent": "cancelar", "data": None}

        # 5. Marcación de Entregas (Regex para grupos)
        match_entrega = re.search(r'(?:pedido\s+)?(\d+)\s+entregado', msg)
        if match_entrega:
            return {"intent": "marcar_entregado", "data": int(match_entrega.group(1))}

        # 6. Fallback: Si parece descripción de pedido, usar IA
        # Si tiene más de 3 palabras o palabras clave de productos
        if len(msg.split()) > 1:
            return {"intent": "interpretar_pedido", "data": mensaje}
            
        return {"intent": "desconocido", "data": None}

intent_service = IntentService()
