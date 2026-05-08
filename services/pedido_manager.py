import re
from datetime import datetime
from services.whatsapp import whatsapp
from services.intent import intent_service
from services.admin_manager import admin_manager
from services.estado_service import EstadoService
from models.usuarios import obtener_o_crear_usuario, guardar_contexto_usuario, obtener_contexto_usuario
from models.pedidos import (
    guardar_pedido_final, obtener_pedidos_con_filtros, 
    marcar_pedido_entregado, obtener_contexto_grupo, guardar_contexto_grupo,
    modificar_pedido_final
)
from models.pedidos_temp import obtener_pedido_temporal, actualizar_pedido_temporal, eliminar_pedido_temporal
from models.catalogo import catalogo_model
from utils.parser_ia import interpretar_con_ia, detectar_modificacion
from utils.formato import formatear_precio

class PedidoManager:
    @staticmethod
    def procesar_privado(telefono: str, mensaje: str):
        usuario = obtener_o_crear_usuario(telefono)
        
        # 1. Verificar Autorización
        if not usuario.get('autorizado'):
            # Si es el primer mensaje de un admin por .env, se le da paso
            from os import getenv
            admins = (getenv("ADMIN_PHONES") or "").split(",")
            if telefono not in admins:
                return "⚠️ No tienes autorización. Contacta a un administrador."

        # 2. Detectar Intención (SIN IA)
        intent_res = intent_service.detectar(mensaje)
        intent = intent_res["intent"]
        data = intent_res["data"]
        
        # 3. Ruteo según Intención y Estado
        # Si es Admin, probar comandos de admin primero
        if usuario.get('rol') == 'admin':
            res_admin = admin_manager.procesar_comando(telefono, mensaje)
            if res_admin: return res_admin

        # Lógica de Menú
        if intent == "ver_menu":
            return PedidoManager._enviar_menu(telefono, usuario.get('rol'))

        # Lógica de Catálogo (Listas WA)
        if intent == "ver_productos":
            return PedidoManager._enviar_lista_productos(telefono)
            
        if intent == "ver_bodegas":
            return PedidoManager._enviar_lista_bodegas(telefono)

        # Lógica de Listado de Pedidos
        if intent == "ver_pedidos":
            return PedidoManager._listar_pedidos(telefono, usuario.get('rol'), data)

        # 4. Flujo de Pedidos (Estado)
        estado = usuario.get('estado', 'inicio')

        if estado == 'confirmacion':
            return PedidoManager._manejar_confirmacion(telefono, mensaje)

        if estado == 'capturando' or intent == "interpretar_pedido":
            return PedidoManager._fluir_pedido(telefono, mensaje, usuario)

        return "No entendí ese comando. Escribe *MENU* para ver opciones."

    @staticmethod
    def procesar_grupo(jid: str, mensaje: str):
        """Lógica simplificada para grupos."""
        intent_res = intent_service.detectar(mensaje)
        intent = intent_res["intent"]
        data = intent_res["data"]

        if intent == "ver_pedidos":
            return PedidoManager._enviar_reporte_grupo(jid, data)

        if intent == "marcar_entregado":
            return PedidoManager._marcar_entregado_grupo(jid, data)

        return None

    # --- Métodos Privados de Apoyo ---

    @staticmethod
    def _enviar_menu(telefono: str, rol: str):
        if rol == 'admin':
            menu = (
                "👑 *MENU ADMINISTRADOR*\n\n"
                "👤 *Usuarios:* `autorizar [número]`, `rol [número] [rol]`\n"
                "📅 *Calendario:* `bloquear [fecha]`\n"
                "📋 *Operación:* `pedidos`, `productos`, `bodegas`"
            )
        else:
            menu = (
                "👋 *SISTEMA DE PEDIDOS - BEKA*\n\n"
                "Para crear un pedido envía los datos:\n"
                "👉 _Juan, 2 laminas, Soacha, hoy_\n\n"
                "📌 *Comandos:* `productos`, `bodegas`, `pedidos`"
            )
        return menu

    @staticmethod
    def _enviar_lista_productos(telefono: str):
        productos = catalogo_model.obtener_productos()
        if not productos: return "No hay productos registrados."
        
        sections = [{"title": "Catálogo", "rows": [{"title": p, "rowId": f"prod_{i}"} for i, p in enumerate(productos)]}]
        whatsapp.send_list(telefono, "🧾 Productos", "Selecciona para ver detalles o simplemente escribe tu pedido.", "Ver Catálogo", sections)
        return None # El mensaje se envía vía API

    @staticmethod
    def _enviar_lista_bodegas(telefono: str):
        bodegas = catalogo_model.obtener_bodegas()
        sections = [{"title": "Nuestras Sedes", "rows": [{"title": b, "rowId": f"bod_{i}"} for i, b in enumerate(bodegas)]}]
        whatsapp.send_list(telefono, "📍 Bodegas", "Selecciona una bodega disponible.", "Ver Sedes", sections)
        return None

    @staticmethod
    def _listar_pedidos(telefono: str, rol: str, filtro: str):
        pedidos = obtener_pedidos_con_filtros(telefono=telefono, rol=rol, estado=filtro)
        if not pedidos: return f"No hay pedidos {filtro if filtro else ''}."
        
        res = f"📋 *PEDIDOS ({filtro.upper() if filtro else 'HOY'})*\n\n"
        ids = []
        for i, p in enumerate(pedidos, 1):
            status = "✅" if p['estado'] == 'entregado' else "⏳"
            res += f"{i}. {status} *{p['cliente']}* - {formatear_precio(p['precio'])}\n"
            res += f"   📍 {p['bodega']} | 🚚 {p['metodo_envio']}\n\n"
            ids.append(p['id'])
        
        guardar_contexto_usuario(telefono, ids)
        return res

    @staticmethod
    def _fluir_pedido(telefono: str, mensaje: str, usuario: dict):
        pedido_actual = obtener_pedido_temporal(telefono)
        
        # 1. IA para extraer datos
        datos = interpretar_con_ia(mensaje, pedido_actual)
        
        # 2. VALIDACIONES Y NORMALIZACIÓN CRÍTICA
        # Validar Fecha Bloqueada
        if datos.get('fecha_entrega') and catalogo_model.es_fecha_bloqueada(datos['fecha_entrega']):
            return f"❌ La fecha {datos['fecha_entrega']} está bloqueada. Por favor selecciona otra."

        # Normalizar Bodega
        if datos.get('bodega'):
            from utils.normalizacion import normalizar_valor
            nombre, _, score = normalizar_valor(datos['bodega'], 'bodegas')
            if score > 70: datos['bodega'] = nombre
            else:
                actualizar_pedido_temporal(telefono, {"bodega": None})
                return f"📍 No reconozco la bodega '{datos['bodega']}'. ¿A cuál sede pertenece?"

        # Normalizar Productos
        if datos.get('lista_productos'):
            from utils.normalizacion import normalizar_valor
            productos_validados = []
            total = 0
            for p in datos['lista_productos']:
                nombre_norm, _, score = normalizar_valor(p['descripcion'], 'productos')
                if score < 75:
                    actualizar_pedido_temporal(telefono, {"productos": None})
                    return f"❓ No encontré el producto '{p['descripcion']}'. ¿Podrías verificar el nombre?"
                
                subtotal = p['cantidad'] * p['precio_unitario']
                total += subtotal
                productos_validados.append(f"{p['cantidad']} {nombre_norm} - {formatear_precio(p['precio_unitario'])} c/u")
            
            datos['productos'] = "\n".join(productos_validados)
            datos['precio'] = total

        # Normalizar Envío
        if datos.get('metodo_envio'):
            from utils.normalizacion import normalizar_valor
            nombre, _, score = normalizar_valor(datos['metodo_envio'], 'metodos_envio')
            if score > 70: datos['metodo_envio'] = nombre

        # Guardar progreso
        actualizar_pedido_temporal(telefono, datos)
        
        # 3. Verificar Faltantes
        faltantes = []
        if not datos.get('cliente'): faltantes.append("Cliente")
        if not datos.get('productos'): faltantes.append("Productos")
        if not datos.get('bodega'): faltantes.append("Bodega")
        if not datos.get('metodo_envio'): faltantes.append("Envío")

        if not faltantes:
            EstadoService.cambiar_a_confirmacion(telefono)
            resumen = (
                f"📦 *RESUMEN DEL PEDIDO*\n\n"
                f"👤 *Cliente:* {datos['cliente']}\n"
                f"📍 *Bodega:* {datos['bodega']}\n"
                f"🚚 *Envío:* {datos['metodo_envio']}\n"
                f"💰 *Total:* {formatear_precio(datos['precio'])}\n"
                f"📦 *Detalle:*\n{datos['productos']}"
            )
            buttons = [
                {"buttonId": "confirmar", "buttonText": {"displayText": "✅ Confirmar"}},
                {"buttonId": "cancelar", "buttonText": {"displayText": "❌ Cancelar"}}
            ]
            whatsapp.send_buttons(telefono, "Confirmación de Pedido", resumen, buttons)
            return None
        
        EstadoService.cambiar_a_capturando(telefono)
        return f"Aún faltan datos: *{', '.join(faltantes)}*. Por favor envíalos."

    @staticmethod
    def _manejar_confirmacion(telefono: str, mensaje: str):
        msg = mensaje.lower().strip()
        pedido = obtener_pedido_temporal(telefono)
        
        if msg in ["si", "sí", "confirmar", "✅ confirmar"]:
            guardar_pedido_final(telefono, pedido['precio'], pedido['cliente'], pedido['bodega'], pedido['metodo_envio'], pedido['productos'], pedido['fecha_entrega'])
            eliminar_pedido_temporal(telefono)
            EstadoService.cambiar_a_inicio(telefono)
            return "✅ *¡Pedido registrado con éxito!*"
        
        if msg in ["no", "cancelar", "❌ cancelar"]:
            eliminar_pedido_temporal(telefono)
            EstadoService.cambiar_a_inicio(telefono)
            return "❌ Pedido descartado."
            
        # Si escribe algo más, podría ser una corrección (IA)
        return PedidoManager._fluir_pedido(telefono, mensaje, {})

    @staticmethod
    def _enviar_reporte_grupo(jid: str, filtro: str):
        pedidos = obtener_pedidos_con_filtros(rol='admin', estado=filtro)
        if not pedidos:
            whatsapp.send_to_group(jid, "📭 No hay pedidos para reportar.")
            return None

        res = f"📋 *REPORTE OPERATIVO - {datetime.now().strftime('%d/%m')}*\n\n"
        ids = []
        for i, p in enumerate(pedidos, 1):
            status = "✅" if p['estado'] == 'entregado' else "⏳"
            res += f"{i}. {status} *{p['cliente']}* ({p['metodo_envio']})\n"
            ids.append(p['id'])
        
        guardar_contexto_grupo(jid, ids)
        whatsapp.send_to_group(jid, res)
        return None

    @staticmethod
    def _marcar_entregado_grupo(jid: str, num_lista: int):
        ids = obtener_contexto_grupo(jid)
        if not ids or num_lista > len(ids):
            return "❌ No encuentro ese pedido en la lista."
        
        pedido_id = ids[num_lista - 1]
        marcar_pedido_entregado(pedido_id)
        return f"✅ Pedido {num_lista} marcado como entregado."

pedido_manager = PedidoManager()
