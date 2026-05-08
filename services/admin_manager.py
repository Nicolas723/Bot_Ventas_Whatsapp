from models.usuarios import autorizar_usuario, desautorizar_usuario, cambiar_rol_usuario, actualizar_estado_usuario
from models.admin import bloquear_fecha, desbloquear_fecha
from utils.parser_ia import extraer_fecha_con_ia
from utils.telefonos import normalizar_telefono

class AdminManager:
    @staticmethod
    def procesar_comando(telefono: str, mensaje: str) -> str:
        cmd = mensaje.lower().strip()
        
        # 1. Autorización de Usuarios
        if cmd.startswith("autorizar "):
            parts = cmd.split()
            if len(parts) < 2: return "❌ Formato: autorizar [numero] [vendedor/admin]"
            
            num_raw = parts[1]
            rol = parts[2] if len(parts) > 2 else "vendedor"
            if rol == "administrador": rol = "admin"
            
            num = normalizar_telefono(num_raw)
            if not num: return "❌ Número de teléfono inválido."
            
            autorizar_usuario(num, rol)
            return f"✅ Usuario {num} autorizado como *{rol.upper()}*."

        # 2. Desautorización
        if cmd.startswith("desautorizar "):
            num_raw = cmd.replace("desautorizar ", "").strip()
            num = normalizar_telefono(num_raw)
            if not num: return "❌ Número inválido."
            desautorizar_usuario(num)
            return f"✅ Usuario {num} desautorizado."

        # 3. Cambio de Rol
        if cmd.startswith("rol "):
            parts = cmd.split()
            if len(parts) >= 3:
                num = normalizar_telefono(parts[1])
                rol = parts[2].lower()
                if rol == "administrador": rol = "admin"
                cambiar_rol_usuario(num, rol)
                return f"✅ Rol de {num} cambiado a *{rol.upper()}*."

        # 4. Bloqueo de Fechas
        if cmd.startswith("bloquear "):
            raw_fecha = cmd.replace("bloquear ", "").strip()
            fecha = extraer_fecha_con_ia(raw_fecha)
            if fecha:
                bloquear_fecha(fecha)
                return f"✅ Fecha {fecha} bloqueada para entregas."
            return "❌ No entendí la fecha."

        if cmd.startswith("desbloquear "):
            raw_fecha = cmd.replace("desbloquear ", "").strip()
            fecha = extraer_fecha_con_ia(raw_fecha)
            if fecha:
                desbloquear_fecha(fecha)
                return f"✅ Fecha {fecha} desbloqueada."
            return "❌ No entendí la fecha."

        return None

admin_manager = AdminManager()
