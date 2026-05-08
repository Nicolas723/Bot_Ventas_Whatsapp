from services.intent import intent_service
from services.pedidos.reports import ReportService
from services.pedidos.delivery import DeliveryService
from utils.logger import logger

class GroupHandler:
    @staticmethod
    def handle(jid: str, mensaje: str):
        intent_res = intent_service.detectar(mensaje)
        intent = intent_res["intent"]
        data = intent_res["data"]

        # Solo respondemos a intenciones operativas en grupos
        if intent == "ver_pedidos":
            logger.info(f"Reporte solicitado en grupo {jid}")
            return ReportService.generar_reporte_grupo(jid, data)

        if intent == "marcar_entregado":
            return DeliveryService.marcar_como_entregado(jid, data)

        return None
