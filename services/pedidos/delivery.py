from models.pedidos import obtener_contexto_grupo, marcar_pedido_entregado
from utils.logger import logger

class DeliveryService:
    @staticmethod
    def marcar_como_entregado(jid: str, num_lista: int) -> str:
        ids = obtener_contexto_grupo(jid)
        if not ids or num_lista > len(ids) or num_lista < 1:
            logger.warning(f"Intento de entrega fallido: JID {jid}, Index {num_lista}")
            return "❌ No encuentro ese pedido en la última lista enviada."
        
        pedido_id = ids[num_lista - 1]
        marcar_pedido_entregado(pedido_id)
        logger.info(f"Pedido {pedido_id} marcado como entregado por {jid}")
        return f"✅ Pedido {num_lista} marcado como entregado."
