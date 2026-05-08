from models.usuarios import obtener_o_crear_usuario, actualizar_estado_usuario
from services.intent import intent_service
from services.whatsapp import whatsapp
from services.pedidos.creator import CreatorService
from config import config
from utils.logger import logger

class PrivateHandler:
    @staticmethod
    def handle(telefono: str, mensaje: str):
        usuario = obtener_o_crear_usuario(telefono)
        estado = usuario.get('estado', 'inicio')
        mensaje_limpio = mensaje.lower().strip()
        
        # Log de Debug Operativo
        logger.info(f"MSG: '{mensaje_limpio}' | Tel: {telefono} | Estado: {estado}")

        # 1. Autorización Básica
        if not usuario.get('autorizado') and telefono not in config.ADMIN_PHONES:
            return "⚠️ No autorizado. Contacta a un administrador."

        # 2. Registro de Nombre (Si no tiene)
        if not usuario.get('nombre') and estado != "capturando_nombre":
            actualizar_estado_usuario(telefono, "capturando_nombre")
            return "👋 ¡Hola! Veo que es tu primera vez aquí.\n\n¿Podrías decirme tu *nombre completo* para registrarte en el sistema?"

        if estado == "capturando_nombre":
            from models.usuarios import actualizar_nombre_usuario
            nombre = mensaje.strip()
            actualizar_nombre_usuario(telefono, nombre)
            actualizar_estado_usuario(telefono, "menu:principal")
            return f"✅ ¡Gracias, *{nombre}*! Registro completado.\n\n" + PrivateHandler._mostrar_menu_principal(telefono, usuario.get('rol'))

        # 3. Detección de Intención Global
        intent_res = intent_service.detectar(mensaje)
        intent = intent_res["intent"]

        # 2. Comandos de Escape / Reset (Siempre disponibles)
        if mensaje_limpio in ["menu", "menú", "hola", "inicio", "cancelar", "salir"]:
            actualizar_estado_usuario(telefono, "menu:principal")
            return PrivateHandler._mostrar_menu_principal(telefono, usuario.get('rol'))

        # 4. Comandos de Administrador (Globales)
        if usuario.get('rol') == 'admin':
            if mensaje_limpio.startswith("autorizar "):
                target = mensaje_limpio.replace("autorizar ", "").strip()
                from models.usuarios import autorizar_usuario
                autorizar_usuario(target)
                return f"✅ Usuario {target} *autorizado* correctamente."
            
            elif mensaje_limpio.startswith("desautorizar "):
                target = mensaje_limpio.replace("desautorizar ", "").strip()
                from models.usuarios import desautorizar_usuario
                desautorizar_usuario(target)
                return f"❌ Usuario {target} *desautorizado*."

            elif mensaje_limpio.startswith("hacer admin "):
                target = mensaje_limpio.replace("hacer admin ", "").strip()
                from models.usuarios import cambiar_rol_usuario
                cambiar_rol_usuario(target, 'admin')
                return f"👑 Usuario {target} ahora es *Administrador*."

            elif mensaje_limpio.startswith("hacer vendedor "):
                target = mensaje_limpio.replace("hacer vendedor ", "").strip()
                from models.usuarios import cambiar_rol_usuario
                cambiar_rol_usuario(target, 'vendedor')
                return f"💼 Usuario {target} ahora es *Vendedor*."

        # 3. Procesamiento según Estado Actual (Máquina de Estados)
        
        # --- ESTADO: MENÚ PRINCIPAL ---
        if estado == "menu:principal":
            if mensaje_limpio == "1":
                actualizar_estado_usuario(telefono, "capturando")
                return (
                    "📝 *NUEVO PEDIDO*\n\n"
                    "Por favor, envía los datos del pedido en un solo mensaje.\n\n"
                    "*Incluye:*\n"
                    "• Nombre del Cliente\n"
                    "• Productos y Cantidades\n"
                    "• Bodega y Método de Envío\n\n"
                    "💡 _Ejemplo: 'Pedido para Juan Pérez, 3 laminas blancas 200.000, recoger en Bodega Sur, entrega mañana.'_"
                )
            
            elif mensaje_limpio == "2":
                actualizar_estado_usuario(telefono, "menu:pedidos")
                return PrivateHandler._mostrar_menu_pedidos(telefono)
            
            elif mensaje_limpio == "3":
                return "🧾 *Catálogo:* Próximamente integración con DB."
            
            elif mensaje_limpio == "4":
                return "📍 *BODEGAS DISPONIBLES:*\n\n• Principal\n• Sur\n• Chía"
            

            elif mensaje_limpio == "6" and usuario.get('rol') == 'admin':
                from models.pedidos import obtener_pedidos_hoy
                pedidos = obtener_pedidos_hoy()
                if not pedidos: return "📊 No hay pedidos registrados hoy."
                
                reporte = "📊 *REPORTE GLOBAL DE HOY*\n\n"
                for p in pedidos:
                    vendedor = p.get('vendedor') or p.get('telefono') or 'Desconocido'
                    reporte += f"• *{vendedor}* -> {p['cliente']}\n   _{p['productos']}_\n\n"
                return reporte

            elif mensaje_limpio == "7" and usuario.get('rol') == 'admin':
                from models.usuarios import obtener_todos_los_usuarios
                usuarios_lista = obtener_todos_los_usuarios()
                if not usuarios_lista: return "👥 No hay usuarios registrados."
                
                res = "👥 *GESTIÓN DE USUARIOS*\n\n"
                for u in usuarios_lista:
                    estado_auth = "✅" if u['autorizado'] else "❌"
                    nombre_u = u['nombre'] or "Sin nombre"
                    res += f"• {estado_auth} *{nombre_u}*\n   Tel: {u['telefono']} | Rol: {u['rol']}\n\n"
                
                res += "💡 *COMANDOS:*\n"
                res += "- 'autorizar [tel]'\n"
                res += "- 'desautorizar [tel]'\n"
                res += "- 'hacer admin [tel]'\n"
                res += "- 'hacer vendedor [tel]'"
                return res

        # --- ESTADO: MENÚ PEDIDOS ---
        elif estado == "menu:pedidos":
            from models.pedidos import obtener_pedidos_con_filtros
            rol = usuario.get('rol', 'vendedor')

            if mensaje_limpio == "1":
                pedidos = obtener_pedidos_con_filtros(telefono=telefono, rol=rol, estado='pendiente')
                if not pedidos: return "📭 No hay pedidos *pendientes* registrados para hoy."
                
                res = "📋 *PEDIDOS PENDIENTES (HOY):*\n\n"
                for p in pedidos:
                    res += f"• ID: {p['id']} | *{p['cliente']}*\n   {p['productos']}\n   ({p['bodega']} - {p['metodo_envio']})\n\n"
                return res

            elif mensaje_limpio == "2":
                pedidos = obtener_pedidos_con_filtros(telefono=telefono, estado='enviado')
                if not pedidos: return "✅ No tienes pedidos enviados."
                
                res = "🚚 *PEDIDOS ENVIADOS*\n\n"
                for p in pedidos:
                    res += f"📦 ID: {p['id']} | Cliente: {p['cliente']}\n"
                return res

            elif mensaje_limpio == "3":
                pedidos = obtener_pedidos_con_filtros(telefono=telefono, estado='pendiente')
                if not pedidos: return "❌ No tienes pedidos pendientes para modificar."
                
                lista = "📝 *SELECCIONA EL ID A MODIFICAR*\n\n"
                for p in pedidos:
                    lista += f"🆔 *{p['id']}* - {p['cliente']}\n"
                lista += "\nEscribe el *ID* del pedido que quieres modificar."
                
                actualizar_estado_usuario(telefono, "esperando_id_modificar")
                return lista

            elif mensaje_limpio == "4":
                actualizar_estado_usuario(telefono, "menu:principal")
                return PrivateHandler._mostrar_menu_principal(telefono, usuario.get('rol'))

        # --- ESTADO: ESPERANDO ID PARA MODIFICAR ---
        elif estado == "esperando_id_modificar":
            if not mensaje_limpio.isdigit():
                return "⚠️ Por favor, escribe solo el número del ID (Ej: 15)."
            
            from models.pedidos import obtener_pedido_por_id
            pedido = obtener_pedido_por_id(int(mensaje_limpio))
            if not pedido or str(pedido['telefono']) != str(telefono):
                return "❌ Pedido no encontrado o no te pertenece. Intenta de nuevo o escribe 'menu'."
            
            # Reutilizamos el servicio de creación con el comando de modificación
            return CreatorService.fluir_pedido(telefono, f"modificar {mensaje_limpio}", "modificar_pedido")

        # --- ESTADO: CONFIRMACIÓN DE PEDIDO ---
        elif estado == "menu:confirmacion_pedido":
            if mensaje_limpio in ["1", "confirmar", "si", "sí", "dale", "listo"]:
                return CreatorService.fluir_pedido(telefono, mensaje, "confirmar")
            elif mensaje_limpio in ["2", "cancelar", "no", "parar"]:
                return CreatorService.fluir_pedido(telefono, mensaje, "cancelar")
            else:
                # Si escribe cualquier otra cosa, lo tomamos como una corrección/edición
                return CreatorService.fluir_pedido(telefono, mensaje, "interpretar_pedido")

        # --- ESTADO: CAPTURANDO PEDIDO (IA) ---
        elif estado == "capturando":
            return CreatorService.fluir_pedido(telefono, mensaje, intent)

        # 4. Fallback: Intentar detección de intención global
        if intent == "interpretar_pedido":
             actualizar_estado_usuario(telefono, "capturando")
             return CreatorService.fluir_pedido(telefono, mensaje, intent)
        
        # Si nada funciona, sugerir menú
        return "No entendí tu opción. Escribe *MENU* para volver al inicio."

    @staticmethod
    def _mostrar_menu_principal(telefono: str, rol: str):
        menu = "📋 *MENÚ PRINCIPAL*\n\n"
        menu += "1️⃣ Crear nuevo pedido\n"
        menu += "2️⃣ Gestionar pedidos\n"
        menu += "3️⃣ Ver catálogo\n"
        menu += "4️⃣ Ubicación bodegas\n\n"
        menu += "Responde con el *número* de la opción."
        
        if rol == 'admin':
            menu += "\n\n*Admin:* 📊 (6) Reportes | ⚙️ (7) Usuarios"
            
        return menu

    @staticmethod
    def _mostrar_menu_pedidos(telefono: str):
        menu = "📦 *GESTIÓN DE PEDIDOS*\n\n"
        menu += "1️⃣ Pedidos pendientes\n"
        menu += "2️⃣ Pedidos enviados\n"
        menu += "3️⃣ Modificar pedido\n"
        menu += "4️⃣ ⬅️ Volver al menú principal"
        return menu
