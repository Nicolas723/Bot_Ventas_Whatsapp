from models.pedidos import guardar_pedido_final, obtener_pedidos_del_dia, obtener_pedidos_del_dia_todos
from models.pedidos_temp import (
    obtener_pedido_temporal, 
    actualizar_pedido_temporal, 
    eliminar_pedido_temporal
)
from models.usuarios import obtener_o_crear_usuario, actualizar_nombre_usuario
from services.estado_service import EstadoService
from utils.parser_regex import extraer_con_regex
from utils.parser_ia import interpretar_con_ia, detectar_modificacion
from utils.formato import formatear_precio
from utils.baileys import enviar_mensaje_grupo_baileys

class PedidoService:
    @staticmethod
    def procesar_mensaje(telefono: str, mensaje: str) -> str:
        usuario = obtener_o_crear_usuario(telefono)
        estado = usuario['estado']

        # Lógica basada en el estado actual
        if estado == 'nuevo':
            EstadoService.cambiar_estado(telefono, 'esperando_nombre')
            return "¡Hola! 👋 Para empezar a registrar tus pedidos, por favor dime: ¿Cuál es tu nombre completo?"
            
        elif estado == 'esperando_nombre':
            nombre = mensaje.strip().title()
            from models.usuarios import actualizar_nombre_temp_usuario
            actualizar_nombre_temp_usuario(telefono, nombre)
            return f"Entendido. Tu nombre es *{nombre}*.\n\n¿Es correcto? (Responde *sí* o *no*)"
            
        elif estado == 'confirmando_nombre':
            resp = mensaje.lower().strip()
            if resp in ['si', 'sí', 'yes', 'correcto', 'ok']:
                from models.usuarios import actualizar_estado_usuario
                actualizar_estado_usuario(telefono, 'inicio')
                return "¡Perfecto! Ya estás registrado.\n\nPor favor, envía los datos de tu primer pedido (ej: 20000 tienda sur origen centro en ruta)."
            elif resp in ['no', 'incorrecto']:
                from models.usuarios import actualizar_estado_usuario
                actualizar_estado_usuario(telefono, 'esperando_nombre')
                return "Vale, empecemos de nuevo. ¿Cuál es tu nombre completo?"
            else:
                return "Por favor, responde *sí* si el nombre es correcto, o *no* si quieres corregirlo."
            
        elif estado == 'inicio':
            return PedidoService._manejar_estado_inicio(telefono, mensaje)
        
        elif estado == 'capturando':
            return PedidoService._manejar_estado_capturando(telefono, mensaje)
            
        elif estado == 'confirmacion':
            return PedidoService._manejar_estado_confirmacion(telefono, mensaje)
        
        return "Lo siento, hubo un error. Escribe algo para empezar de nuevo."

    @staticmethod
    def _manejar_estado_inicio(telefono: str, mensaje: str) -> str:
        # Intentar extraer datos del primer mensaje con regex
        datos = extraer_con_regex(mensaje)
        # Fallback a IA si regex no encontró todo
        if not any(datos.values()):
            datos = interpretar_con_ia(mensaje)
        else:
            # Si regex encontró algunos datos, complementar con IA los faltantes
            if not all(datos.values()):
                datos_ia = interpretar_con_ia(mensaje)
                for campo in ['precio', 'tienda', 'origen', 'metodo_envio']:
                    if datos.get(campo) is None and datos_ia.get(campo) is not None:
                        datos[campo] = datos_ia[campo]
        
        # Asegurar precio sin decimales
        if datos.get('precio') is not None:
            datos['precio'] = int(float(str(datos['precio'])))
        
        # Guardar en temporal
        actualizar_pedido_temporal(telefono, datos)
        EstadoService.cambiar_a_capturando(telefono)
        
        return PedidoService._verificar_y_responder(telefono)

    @staticmethod
    def _manejar_estado_capturando(telefono: str, mensaje: str) -> str:
        datos = extraer_con_regex(mensaje)
        if not any(datos.values()):
            datos = interpretar_con_ia(mensaje)
        else:
            if not all(datos.values()):
                datos_ia = interpretar_con_ia(mensaje)
                for campo in ['precio', 'tienda', 'origen', 'metodo_envio']:
                    if datos.get(campo) is None and datos_ia.get(campo) is not None:
                        datos[campo] = datos_ia[campo]
        
        # Asegurar precio sin decimales
        if datos.get('precio') is not None:
            datos['precio'] = int(float(str(datos['precio'])))
            
        actualizar_pedido_temporal(telefono, datos)
        return PedidoService._verificar_y_responder(telefono)

    @staticmethod
    def _manejar_estado_confirmacion(telefono: str, mensaje: str) -> str:
        """
        Maneja el estado de confirmación con soporte para modificaciones.
        El usuario puede:
        - Confirmar: "sí", "dale", "correcto", etc.
        - Cancelar: "no", "cancelar", etc.
        - Modificar: "tienda norte", "cambia el precio a 30000", etc.
        """
        pedido_temp = obtener_pedido_temporal(telefono)
        if not pedido_temp:
            EstadoService.cambiar_a_inicio(telefono)
            return "No encontré tu pedido. Empecemos de nuevo."

        # Usar IA para detectar la intención del usuario
        resultado = detectar_modificacion(mensaje, pedido_temp)
        accion = resultado.get("accion", "desconocido")

        if accion == "confirmar":
            return PedidoService._confirmar_pedido(telefono, pedido_temp)
        
        elif accion == "cancelar":
            eliminar_pedido_temporal(telefono)
            EstadoService.cambiar_a_inicio(telefono)
            return "❌ Pedido cancelado. Envía nuevos datos cuando quieras."
        
        elif accion == "modificar":
            return PedidoService._aplicar_modificacion(telefono, resultado)
        
        else:
            return (
                "No entendí tu respuesta. Puedes:\n"
                "- Responder *sí* para confirmar\n"
                "- Responder *no* para cancelar\n"
                "- Enviar la corrección (ej: *tienda norte*)"
            )

    @staticmethod
    def _confirmar_pedido(telefono: str, pedido_temp: dict) -> str:
        """Guarda el pedido final y genera el resumen del día."""
        # Guardar final
        guardar_pedido_final(
            telefono, 
            int(float(str(pedido_temp['precio']))),
            pedido_temp['tienda'], 
            pedido_temp['origen'],
            pedido_temp.get('metodo_envio')
        )
        
        # Log
        print(f"  LOG: Pedido confirmado - Tel: {telefono}, {formatear_precio(pedido_temp['precio'])} en {pedido_temp['tienda']}")
        
        # Limpiar temporal y volver a inicio
        eliminar_pedido_temporal(telefono)
        EstadoService.cambiar_a_inicio(telefono)
        
        # Generar listado de TODOS los vendedores para el grupo
        todos_pedidos = obtener_pedidos_del_dia_todos()
        
        # Agrupar por metodo_envio
        agrupados = {
            "ruta": [],
            "bicicleta": [],
            "envio": [],
            "recoger en tienda": []
        }
        
        for p in todos_pedidos:
            metodo = p.get('metodo_envio') or 'ruta'
            if metodo in agrupados:
                agrupados[metodo].append(p)
                
        # Construir mensaje para el grupo
        msg_grupo = "📋 *RESUMEN DE PEDIDOS DEL DÍA*\n\n"
        
        for metodo, pedidos in agrupados.items():
            if not pedidos:
                continue
            
            icono = "🚚" if metodo == "ruta" else "🚲" if metodo == "bicicleta" else "📦" if metodo == "envio" else "🏪"
            msg_grupo += f"{icono} *{metodo.upper()}*\n"
            
            for p in pedidos:
                msg_grupo += f"  👤 {p['nombre']}: {formatear_precio(p['precio'])} | {p['tienda']} | {p['origen']}\n"
            msg_grupo += "\n"
            
        print("\n=== MENSAJE PARA EL GRUPO DE WHATSAPP ===")
        print(msg_grupo)
        print("=========================================\n")
        
        # Enviar vía Baileys
        enviar_mensaje_grupo_baileys(msg_grupo)
        
        return (
            "✅ *¡Pedido registrado con éxito!*\n\n"
            "El resumen ha sido actualizado para enviar al grupo.\n\n"
            "Envíe datos para un nuevo pedido."
        )

    @staticmethod
    def _aplicar_modificacion(telefono: str, resultado: dict) -> str:
        """Aplica las modificaciones al pedido temporal y muestra nuevo resumen."""
        datos_modificar = {}
        campos_modificados = []
        
        if resultado.get("precio") is not None:
            datos_modificar["precio"] = int(float(str(resultado["precio"])))
            campos_modificados.append("precio")
        if resultado.get("tienda") is not None:
            datos_modificar["tienda"] = resultado["tienda"]
            campos_modificados.append("tienda")
        if resultado.get("origen") is not None:
            datos_modificar["origen"] = resultado["origen"]
            campos_modificados.append("origen")
        if resultado.get("metodo_envio") is not None:
            datos_modificar["metodo_envio"] = resultado["metodo_envio"]
            campos_modificados.append("metodo_envio")
        
        if datos_modificar:
            actualizar_pedido_temporal(telefono, datos_modificar)
        
        # Obtener datos actualizados
        pedido = obtener_pedido_temporal(telefono)
        
        # Construir resumen con indicador de campos modificados
        precio_str = formatear_precio(pedido['precio'])
        tienda_str = pedido['tienda']
        origen_str = pedido['origen']
        metodo_str = pedido.get('metodo_envio', '').capitalize()
        
        # Marcar campos que fueron modificados
        marca_precio = " ✏️" if "precio" in campos_modificados else ""
        marca_tienda = " ✏️" if "tienda" in campos_modificados else ""
        marca_origen = " ✏️" if "origen" in campos_modificados else ""
        marca_metodo = " ✏️" if "metodo_envio" in campos_modificados else ""
        
        cambios_texto = ", ".join(campos_modificados)
        
        return (
            f"📝 *Pedido actualizado* ({cambios_texto})\n\n"
            f"💰 Precio: {precio_str}{marca_precio}\n"
            f"🏬 Tienda: {tienda_str}{marca_tienda}\n"
            f"📍 Origen: {origen_str}{marca_origen}\n"
            f"🚚 Método: {metodo_str}{marca_metodo}\n\n"
            "¿Confirmar? Responde *sí*, *no*, o envía otra corrección."
        )

    @staticmethod
    def _verificar_y_responder(telefono: str) -> str:
        pedido = obtener_pedido_temporal(telefono)
        
        if not pedido:
            return "He recibido tu mensaje, pero no pude procesar los datos. ¿Podrías repetirlos?"

        faltantes = []
        
        if not pedido.get('precio'): faltantes.append("precio")
        if not pedido.get('tienda'): faltantes.append("tienda")
        if not pedido.get('origen'): faltantes.append("origen")
        if not pedido.get('metodo_envio'): faltantes.append("metodo_envio")
        
        if not faltantes:
            EstadoService.cambiar_a_confirmacion(telefono)
            return (
                "📦 *Resumen del Pedido*\n"
                f"💰 Precio: {formatear_precio(pedido['precio'])}\n"
                f"🏬 Tienda: {pedido['tienda']}\n"
                f"📍 Origen: {pedido['origen']}\n"
                f"🚚 Método: {pedido.get('metodo_envio', '').capitalize()}\n\n"
                "¿Confirmar? Responde *sí*, *no*, o envía la corrección."
            )
        else:
            msg = "He recibido parte de los datos. Por favor, dime:\n"
            if "precio" in faltantes: msg += "- El precio del pedido\n"
            if "tienda" in faltantes: msg += "- La tienda donde se realizó\n"
            if "origen" in faltantes: msg += "- El origen de la venta\n"
            if "metodo_envio" in faltantes: msg += "- El método de envío (ruta, bicicleta, envio, recoger en tienda)\n"
            return msg
