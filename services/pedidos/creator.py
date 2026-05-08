from services.whatsapp import whatsapp
from services.intent import intent_service
from config import config
from utils.parser_ia import interpretar_con_ia as interpretar_pedido
from utils.formato import formatear_precio
from models.pedidos_temp import obtener_pedido_temporal, actualizar_pedido_temporal, eliminar_pedido_temporal
from models.pedidos import guardar_pedido_final
from models.usuarios import actualizar_estado_usuario
from utils.logger import logger

class CreatorService:
    @staticmethod
    def fluir_pedido(telefono: str, mensaje: str, intent: str):
        """Gestiona el flujo conversacional de creación de pedidos."""
        
        # 1. Caso Cancelar
        if intent == "cancelar":
            eliminar_pedido_temporal(telefono)
            actualizar_estado_usuario(telefono, "inicio")
            return "❌ Pedido cancelado correctamente."

        # 2. Caso Confirmar
        if intent == "confirmar":
            temp = obtener_pedido_temporal(telefono)
            if not temp or not temp.get('productos'):
                return "⚠️ No hay un pedido pendiente para confirmar."
            
            guardar_pedido_final(
                telefono=telefono,
                precio=temp['precio'],
                cliente=temp['cliente'],
                bodega=temp['bodega'],
                metodo_envio=temp['metodo_envio'],
                productos=temp['productos'],
                fecha_entrega=temp.get('fecha_entrega')
            )
            eliminar_pedido_temporal(telefono)
            actualizar_estado_usuario(telefono, "inicio")

            # --- ENVÍO AUTOMÁTICO AL GRUPO ---
            try:
                from models.pedidos import obtener_pedidos_hoy
                pedidos_hoy = obtener_pedidos_hoy()
                if pedidos_hoy:
                    reporte = "📢 *LISTA ACTUALIZADA DE PEDIDOS*\n\n"
                    for p in pedidos_hoy:
                        reporte += f"• *{p['cliente']}*: {p['productos']} ({p['metodo_envio']} - {p['bodega']})\n"
                    
                    jid_grupo = config.GROUP_JID
                    if jid_grupo:
                        logger.info(f"Reporte listo. Enviando a JID: {jid_grupo}")
                        whatsapp.send_to_group(jid_grupo, reporte)
            except Exception as e:
                logger.error(f"Error enviando reporte al grupo: {e}")

            return "✅ *¡Pedido guardado con éxito!* Se ha enviado la lista actualizada al grupo."

        # 3. Interpretación con IA (Si no hay comando directo)
        datos_ia = interpretar_pedido(mensaje)
        logger.info(f"[IA] Datos extraídos: {datos_ia}")

        # Guardar en temporal
        actualizar_pedido_temporal(telefono, datos_ia)
        temp = obtener_pedido_temporal(telefono)
        
        # Verificar si falta información crítica (TODOS los campos)
        faltantes = []
        if not temp.get('cliente'): faltantes.append("- Nombre del cliente")
        if not temp.get('productos'): faltantes.append("- Productos y cantidades")
        if not temp.get('bodega'): faltantes.append("- Bodega (Principal/Sur/Chía)")
        if not temp.get('metodo_envio'): faltantes.append("- Método de envío (Ruta/Recoger/Envío)")
        if not temp.get('fecha_entrega'): faltantes.append("- Fecha de entrega (ej: Mañana, Viernes, 15 mayo)")
        
        if faltantes:
            actualizar_estado_usuario(telefono, "capturando")
            lista_faltantes = "\n".join(faltantes)
            return f"📝 *Pedido en proceso...*\n\nPara continuar, necesito estos datos:\n{lista_faltantes}\n\nEscríbelos a continuación."

        # 4. Mostrar resumen y pedir confirmación con List Message
        resumen = (
            f"📦 *Resumen del Pedido*\n\n"
            f"👤 *Cliente:* {temp['cliente']}\n"
            f"🏗️ *Bodega:* {temp['bodega'] or 'Por definir'}\n"
            f"🚚 *Envío:* {temp['metodo_envio'] or 'Por definir'}\n"
            f"📅 *Entrega:* {temp.get('fecha_entrega') or 'Hoy'}\n"
            f"💰 *Total:* {formatear_precio(temp['precio']) if temp['precio'] else 'Por definir'}\n\n"
            f"🛒 *Productos:*\n{temp['productos']}\n\n"
            "¿Todo está correcto?"
        )
        
        # 4. Mostrar resumen y pedir confirmación mediante menú numérico
        resumen_final = (
            f"{resumen}\n"
            f"1️⃣ Confirmar y Guardar\n"
            f"2️⃣ Cancelar y Borrar\n\n"
            f"Responde con el *número*."
        )
        
        whatsapp.send_text(telefono, resumen_final)
        actualizar_estado_usuario(telefono, "menu:confirmacion_pedido")
        return None
