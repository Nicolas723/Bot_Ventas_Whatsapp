from models.pedidos import modificar_pedido_final
from models.pedidos_temp import actualizar_pedido_temporal, obtener_pedido_temporal, eliminar_pedido_temporal
from services.estado_service import EstadoService
from utils.parser_ia import interpretar_con_ia
from utils.logger import logger

class ModifierService:
    @staticmethod
    def iniciar_edicion(telefono: str, pedido_id: int):
        EstadoService.cambiar_estado(telefono, f"editando_pedido|{pedido_id}")
        return (
            f"✏️ *MODIFICANDO PEDIDO #{pedido_id}*\n\n"
            "Dime qué cambios deseas realizar (ej: 'cambia la bodega' o 'ahora son 3 láminas')."
        )

    @staticmethod
    def aplicar_cambios(telefono: str, pedido_id: int, mensaje: str):
        # Aquí se podría usar IA para detectar cambios específicos sobre el pedido original
        # Por simplicidad en el MVP, lo tratamos como una actualización de datos
        logger.info(f"Editando pedido {pedido_id} para {telefono}")
        # ... lógica de edición ...
        pass
