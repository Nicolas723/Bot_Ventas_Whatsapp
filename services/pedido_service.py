import os
from models.pedidos import guardar_pedido_final, obtener_pedidos_del_dia, obtener_pedidos_del_dia_todos
from models.pedidos_temp import (
    obtener_pedido_temporal, 
    actualizar_pedido_temporal, 
    eliminar_pedido_temporal
)
from models.usuarios import obtener_o_crear_usuario, actualizar_nombre_usuario
from models.admin import es_fecha_bloqueada, bloquear_fecha, desbloquear_fecha
from services.estado_service import EstadoService
from utils.parser_regex import extraer_con_regex
from utils.parser_ia import interpretar_con_ia, detectar_modificacion, extraer_fecha_con_ia
from utils.formato import formatear_precio
from utils.baileys import enviar_mensaje_grupo_baileys

# Cargar lista de administradores desde ADMIN_PHONES o ADMIN_PHONE (soporta comas y espacios)
_admins_raw = (os.getenv("ADMIN_PHONES") or os.getenv("ADMIN_PHONE") or "")
ADMIN_PHONES = [num.strip() for num in _admins_raw.split(",") if num.strip()]

class PedidoService:
    @staticmethod
    def procesar_mensaje(telefono: str, mensaje: str) -> str:
        try:
            # Comandos de administrador
            if telefono in ADMIN_PHONES:
                cmd = mensaje.lower().strip()
                
                # Comandos directos o inicio de flujo interactivo
                if cmd == "bloquear":
                    EstadoService.cambiar_estado(telefono, 'admin_esperando_bloqueo')
                    return "¿Qué fecha deseas bloquear? (Ej: 2026-05-10, mañana, lunes)"
                elif cmd == "desbloquear":
                    EstadoService.cambiar_estado(telefono, 'admin_esperando_desbloqueo')
                    return "¿Qué fecha deseas desbloquear? (Ej: 2026-05-10, mañana, lunes)"
                
                # Comandos con fecha incluida (legacy/rápido)
                if cmd.startswith("bloquear "):
                    fecha = cmd.replace("bloquear ", "").strip()
                    bloquear_fecha(fecha)
                    return f"✅ Fecha {fecha} bloqueada para nuevos pedidos."
                elif cmd.startswith("desbloquear "):
                    fecha = cmd.replace("desbloquear ", "").strip()
                    desbloquear_fecha(fecha)
                    return f"✅ Fecha {fecha} desbloqueada."

            usuario = obtener_o_crear_usuario(telefono)
            estado = usuario['estado']

            # Flujos interactivos de Admin
            if estado == 'admin_esperando_bloqueo':
                fecha = extraer_fecha_con_ia(mensaje)
                if fecha:
                    bloquear_fecha(fecha)
                    EstadoService.cambiar_a_inicio(telefono)
                    return f"✅ Fecha *{fecha}* bloqueada correctamente."
                else:
                    return "No pude entender la fecha. Por favor escribe algo como '2026-05-10', 'mañana' o 'lunes'."

            elif estado == 'admin_esperando_desbloqueo':
                fecha = extraer_fecha_con_ia(mensaje)
                if fecha:
                    desbloquear_fecha(fecha)
                    EstadoService.cambiar_a_inicio(telefono)
                    return f"✅ Fecha *{fecha}* desbloqueada correctamente."
                else:
                    return "No pude entender la fecha. Por favor escribe algo como '2026-05-10', 'mañana' o 'lunes'."

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
                    return (
                        "¡Perfecto! Ya estás registrado. ✅\n\n"
                        "Para registrar un pedido, por favor envíame estos datos:\n\n"
                        "✅ *Cliente*\n"
                        "✅ *Productos* (con cantidades y precios)\n"
                        "✅ *Bodega* (lugar de salida)\n"
                        "✅ *Método de envío* (ruta, bicicleta, envio o recoger en tienda)\n"
                        "✅ *Fecha de entrega* (hoy, mañana, o fecha específica)\n\n"
                        "💡 *Tip:* Puedes separar los datos con comas para mayor precisión.\n"
                        "Ejemplo: *Jhon Baron, 1 pegante 60mil, Soacha, Ruta, para mañana*"
                    )
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

        except Exception as e:
            print(f"!!! CRASH en procesar_mensaje: {e}")
            import traceback
            traceback.print_exc()
            return "Lo siento, tuve un error interno procesando tu mensaje. ¿Podrías intentarlo de nuevo?"

    @staticmethod
    def procesar_mensaje_grupo(remoteJid: str) -> str:
        """Maneja comandos que vienen de un grupo (ej: 'pedido')."""
        print(f"  [GRUPO] Comando recibido en {remoteJid}")
        PedidoService._enviar_reporte_diario(jid=remoteJid)
        return "Reporte enviado al grupo."

    @staticmethod
    def _manejar_estado_inicio(telefono: str, mensaje: str) -> str:
        datos = interpretar_con_ia(mensaje)
        
        if datos.get('fecha_entrega') and es_fecha_bloqueada(datos['fecha_entrega']):
            return f"❌ Lo siento, la fecha {datos['fecha_entrega']} está bloqueada para nuevos pedidos. Por favor selecciona otra fecha."

        if datos.get('precio') is not None:
            datos['precio'] = int(float(str(datos['precio'])))
        
        actualizar_pedido_temporal(telefono, datos)
        EstadoService.cambiar_a_capturando(telefono)
        return PedidoService._verificar_y_responder(telefono)

    @staticmethod
    def _manejar_estado_capturando(telefono: str, mensaje: str) -> str:
        pedido_actual = obtener_pedido_temporal(telefono)
        datos = interpretar_con_ia(mensaje, pedido_actual)
        
        if datos.get('fecha_entrega') and es_fecha_bloqueada(datos['fecha_entrega']):
            return f"❌ Lo siento, la fecha {datos['fecha_entrega']} está bloqueada. Por favor selecciona otra fecha."

        if datos.get('precio') is not None:
            datos['precio'] = int(float(str(datos['precio'])))
            
        actualizar_pedido_temporal(telefono, datos)
        return PedidoService._verificar_y_responder(telefono)

    @staticmethod
    def _manejar_estado_confirmacion(telefono: str, mensaje: str) -> str:
        pedido_temp = obtener_pedido_temporal(telefono)
        if not pedido_temp:
            EstadoService.cambiar_a_inicio(telefono)
            return "No encontré tu pedido. Empecemos de nuevo."

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
            return "No entendí tu respuesta. Responde *sí* para confirmar, *no* para cancelar o envía la corrección."

    @staticmethod
    def _confirmar_pedido(telefono: str, pedido_temp: dict) -> str:
        guardar_pedido_final(
            telefono, 
            int(float(str(pedido_temp['precio']))),
            pedido_temp['cliente'], 
            pedido_temp['bodega'],
            pedido_temp.get('metodo_envio'),
            pedido_temp.get('productos'),
            pedido_temp.get('fecha_entrega')
        )
        
        eliminar_pedido_temporal(telefono)
        EstadoService.cambiar_a_inicio(telefono)
        
        # Enviar reporte solo si la entrega es para hoy
        from datetime import datetime
        hoy = datetime.now().strftime("%Y-%m-%d")
        if pedido_temp.get('fecha_entrega') == hoy or not pedido_temp.get('fecha_entrega'):
            PedidoService._enviar_reporte_diario()
        
        return "✅ *¡Pedido registrado con éxito!*"

    @staticmethod
    def _enviar_reporte_diario(jid: str = None):
        todos_pedidos = obtener_pedidos_del_dia_todos()
        agrupados = {"ruta": [], "bicicleta": [], "envio": [], "recoger en tienda": []}
        
        for p in todos_pedidos:
            metodo_raw = (p.get('metodo_envio') or 'ruta').lower().strip()
            metodo = 'bicicleta' if 'bici' in metodo_raw else 'recoger en tienda' if 'recoger' in metodo_raw else 'envio' if 'envio' in metodo_raw else 'ruta'
            if metodo in agrupados: agrupados[metodo].append(p)
            else: agrupados['ruta'].append(p)
                
        msg_grupo = "📋 *RESUMEN DE PEDIDOS PARA HOY*\n\n"
        for metodo, pedidos in agrupados.items():
            if not pedidos: continue
            icono = "🚚" if metodo == "ruta" else "🚲" if metodo == "bicicleta" else "📦" if metodo == "envio" else "🏪"
            msg_grupo += f"{icono} *{metodo.upper()}*\n"
            for p in pedidos:
                msg_grupo += f"  👤 *Cliente:* {p['cliente']} ({formatear_precio(p['precio'])})\n"
                if p.get('productos'):
                    for prod in p['productos'].split('\n'):
                        if prod.strip(): msg_grupo += f"    - {prod.strip()}\n"
            msg_grupo += "\n"
            
        enviar_mensaje_grupo_baileys(msg_grupo, jid=jid)

    @staticmethod
    def _aplicar_modificacion(telefono: str, resultado: dict) -> str:
        datos_modificar = {}
        campos_modificados = []
        for campo in ["precio", "cliente", "bodega", "metodo_envio", "productos", "fecha_entrega"]:
            if resultado.get(campo) is not None:
                datos_modificar[campo] = resultado[campo]
                campos_modificados.append(campo)
        
        if datos_modificar:
            actualizar_pedido_temporal(telefono, datos_modificar)
        
        pedido = obtener_pedido_temporal(telefono)
        m = {c: " ✏️" if c in campos_modificados else "" for c in ["precio", "cliente", "bodega", "metodo_envio", "productos", "fecha_entrega"]}
        
        return (
            f"📝 *Pedido actualizado*\n\n"
            f"💰 Total: {formatear_precio(pedido['precio'])}{m['precio']}\n"
            f"👤 Cliente: {pedido['cliente']}{m['cliente']}\n"
            f"📍 Bodega: {pedido['bodega']}{m['bodega']}\n"
            f"🚚 Método: {pedido.get('metodo_envio', '').capitalize()}{m['metodo_envio']}\n"
            f"📅 Fecha: {pedido.get('fecha_entrega', 'Hoy')}{m['fecha_entrega']}\n"
            f"📦 Productos:{m['productos']}\n{pedido.get('productos')}\n\n"
            "¿Confirmar? Responde *sí*, *no*, o envía otra corrección."
        )

    @staticmethod
    def _verificar_y_responder(telefono: str) -> str:
        pedido = obtener_pedido_temporal(telefono)
        if not pedido: return "Error recuperando pedido."

        faltantes = []
        if not pedido.get('cliente'): faltantes.append("cliente")
        if not pedido.get('productos'): faltantes.append("productos")
        if not pedido.get('bodega'): faltantes.append("bodega")
        if not pedido.get('metodo_envio'): faltantes.append("método de envío")
        
        if not pedido.get('productos') or (5 - len(faltantes)) <= 1:
            return (
                "¡Hola! 👋 Envíame estos datos:\n\n"
                "✅ *Cliente*, *Productos*, *Bodega*, *Envío* y *Fecha*\n"
                "💡 *Tip:* Usa comas. Ejemplo: *Juan, 1 pegante 60k, Soacha, Ruta, para mañana*"
            )

        if not faltantes:
            EstadoService.cambiar_a_confirmacion(telefono)
            return (
                "📦 *Resumen del Pedido*\n"
                f"💰 Total: {formatear_precio(pedido['precio'])}\n"
                f"👤 Cliente: {pedido['cliente']}\n"
                f"📍 Bodega: {pedido['bodega']}\n"
                f"🚚 Método: {pedido.get('metodo_envio', '').capitalize()}\n"
                f"📅 Fecha: {pedido.get('fecha_entrega', 'Hoy')}\n"
                f"📦 Productos:\n{pedido.get('productos')}\n\n"
                "¿Confirmar? Responde *sí*, *no*, o envía la corrección."
            )
        else:
            return "Faltan datos: " + ", ".join(faltantes)
