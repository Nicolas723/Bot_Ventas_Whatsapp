from models.pedidos import guardar_pedido_final, obtener_pedidos_del_dia
from models.pedidos_temp import (
    obtener_pedido_temporal, 
    actualizar_pedido_temporal, 
    eliminar_pedido_temporal
)
from models.usuarios import obtener_o_crear_usuario
from services.estado_service import EstadoService
from utils.parser_regex import extraer_con_regex
from utils.parser_ia import interpretar_con_ia

class PedidoService:
    @staticmethod
    def procesar_mensaje(telefono: str, mensaje: str) -> str:
        usuario = obtener_o_crear_usuario(telefono)
        estado = usuario['estado']
        mensaje_clean = mensaje.lower().strip()

        # Lógica basada en el estado actual
        if estado == 'inicio':
            return PedidoService._manejar_estado_inicio(telefono, mensaje)
        
        elif estado == 'capturando':
            return PedidoService._manejar_estado_capturando(telefono, mensaje)
            
        elif estado == 'confirmacion':
            return PedidoService._manejar_estado_confirmacion(telefono, mensaje_clean)
        
        return "Lo siento, hubo un error. Escribe algo para empezar de nuevo."

    @staticmethod
    def _manejar_estado_inicio(telefono: str, mensaje: str) -> str:
        # Intentar extraer datos del primer mensaje
        datos = extraer_con_regex(mensaje)
        # Fallback a IA si no hay nada
        if not any(datos.values()):
            datos = interpretar_con_ia(mensaje)
        
        # Guardar en temporal
        actualizar_pedido_temporal(telefono, datos)
        EstadoService.cambiar_a_capturando(telefono)
        
        return PedidoService._verificar_y_responder(telefono)

    @staticmethod
    def _manejar_estado_capturando(telefono: str, mensaje: str) -> str:
        datos = extraer_con_regex(mensaje)
        if not any(datos.values()):
            datos = interpretar_con_ia(mensaje)
            
        actualizar_pedido_temporal(telefono, datos)
        return PedidoService._verificar_y_responder(telefono)

    @staticmethod
    def _manejar_estado_confirmacion(telefono: str, mensaje_clean: str) -> str:
        if mensaje_clean == 'si':
            pedido_temp = obtener_pedido_temporal(telefono)
            if not pedido_temp:
                EstadoService.cambiar_a_inicio(telefono)
                return "No encontré tu pedido. Empecemos de nuevo."
            
            # Guardar final
            guardar_pedido_final(
                telefono, 
                pedido_temp['precio'], 
                pedido_temp['tienda'], 
                pedido_temp['origen']
            )
            
            # Simular envío a grupo
            print(f" LOG: Pedido confirmado - Tel: {telefono}, $ {pedido_temp['precio']} en {pedido_temp['tienda']}")
            
            # Limpiar temporal y volver a inicio
            eliminar_pedido_temporal(telefono)
            EstadoService.cambiar_a_inicio(telefono)
            
            # Generar listado del día
            pedidos_hoy = obtener_pedidos_del_dia(telefono)
            lista_str = "\n".join([f"- $ {p['precio']} en {p['tienda']}" for p in pedidos_hoy])
            
            return (
                "✅ ¡Pedido registrado con éxito!\n\n"
                "Sus pedidos de hoy:\n"
                f"{lista_str}\n\n"
                "Envíe datos para un nuevo pedido."
            )
            
        elif mensaje_clean == 'no':
            eliminar_pedido_temporal(telefono)
            EstadoService.cambiar_a_inicio(telefono)
            return "Pedido cancelado. ¿Qué deseas registrar ahora?"
        
        else:
            return "Por favor, responde 'si' para confirmar o 'no' para cancelar."

    @staticmethod
    def _verificar_y_responder(telefono: str) -> str:
        pedido = obtener_pedido_temporal(telefono)
        faltantes = []
        
        if not pedido.get('precio'): faltantes.append("precio")
        if not pedido.get('tienda'): faltantes.append("tienda")
        if not pedido.get('origen'): faltantes.append("origen")
        
        if not faltantes:
            EstadoService.cambiar_a_confirmacion(telefono)
            return (
                "📦 *Resumen del Pedido*\n"
                f"💰 Precio: {pedido['precio']}\n"
                f"🏬 Tienda: {pedido['tienda']}\n"
                f"📍 Origen: {pedido['origen']}\n\n"
                "¿Confirmar? (si/no)"
            )
        else:
            msg = "He recibido parte de los datos. Por favor, dime:\n"
            if "precio" in faltantes: msg += "- El precio del pedido\n"
            if "tienda" in faltantes: msg += "- La tienda donde se realizó\n"
            if "origen" in faltantes: msg += "- El origen de la venta\n"
            return msg
