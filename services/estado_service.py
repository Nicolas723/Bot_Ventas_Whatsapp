from models.usuarios import actualizar_estado_usuario

class EstadoService:
    @staticmethod
    def cambiar_a_inicio(telefono: str):
        actualizar_estado_usuario(telefono, 'inicio')
        
    @staticmethod
    def cambiar_a_capturando(telefono: str):
        actualizar_estado_usuario(telefono, 'capturando')
        
    @staticmethod
    def cambiar_a_confirmacion(telefono: str):
        actualizar_estado_usuario(telefono, 'confirmacion')

    @staticmethod
    def cambiar_estado(telefono: str, nuevo_estado: str):
        actualizar_estado_usuario(telefono, nuevo_estado)
