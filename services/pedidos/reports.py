from models.pedidos import obtener_pedidos_con_filtros
from models.usuarios import guardar_contexto_usuario
from models.pedidos import guardar_contexto_grupo
from utils.formato import formatear_precio
from datetime import datetime

class ReportService:
    @staticmethod
    def generar_lista_pedidos(telefono: str, rol: str, filtro: str) -> str:
        pedidos = obtener_pedidos_con_filtros(telefono=telefono, rol=rol, estado=filtro)
        if not pedidos:
            return f"📭 No hay pedidos {filtro if filtro else ''} para mostrar."
        
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
    def generar_reporte_grupo(jid: str, filtro: str) -> str:
        pedidos = obtener_pedidos_con_filtros(rol='admin', estado=filtro)
        if not pedidos:
            return "📭 No hay pedidos para reportar en este momento."

        res = f"📋 *REPORTE OPERATIVO - {datetime.now().strftime('%d/%m')}*\n\n"
        ids = []
        for i, p in enumerate(pedidos, 1):
            status = "✅" if p['estado'] == 'entregado' else "⏳"
            res += f"{i}. {status} *{p['cliente']}* ({p['metodo_envio']})\n"
            ids.append(p['id'])
        
        guardar_contexto_grupo(jid, ids)
        return res
