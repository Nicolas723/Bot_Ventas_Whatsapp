import requests
from config import config
from utils.logger import logger

class WhatsAppService:
    def __init__(self):
        self.api_url = config.EVOLUTION_API_URL
        self.api_key = config.EVOLUTION_API_KEY
        self.instance = config.EVOLUTION_INSTANCE
        self._check_instance()

    def _check_instance(self):
        """Verifica si la instancia existe, si no, intenta crearla."""
        url = f"{self.api_url}/instance/fetchInstances"
        try:
            res = requests.get(url, headers=self._get_headers())
            data = res.json()
            
            # En V2, data suele ser una lista de objetos que contienen la instancia
            exists = False
            if isinstance(data, list):
                for item in data:
                    name = item.get('instance', {}).get('instanceName') or item.get('name')
                    if name == self.instance:
                        exists = True
                        break
            
            if not exists:
                logger.info(f"Instancia '{self.instance}' no encontrada. Creándola...")
                create_url = f"{self.api_url}/instance/create"
                payload = {
                    "instanceName": self.instance,
                    "token": self.api_key,
                    "number": ""
                }
                requests.post(create_url, json=payload, headers=self._get_headers())
        except Exception as e:
            logger.warning(f"No se pudo verificar/crear la instancia: {e}")

    def _get_headers(self):
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    def send_text(self, to: str, text: str):
        """Envía un mensaje de texto plano (Máxima estabilidad)."""
        url = f"{self.api_url}/message/sendText/{self.instance}"
        # Aseguramos que el número sea solo dígitos para evitar errores
        telefono = to.split("@")[0]
        
        payload = {
            "number": telefono,
            "text": str(text), # Forzamos a string
            "delay": 1200,
            "linkPreview": False
        }
        
        try:
            res = requests.post(url, json=payload, headers=self._get_headers())
            if res.status_code not in [200, 201]:
                logger.error(f"Error enviando texto: {res.status_code} - {res.text}")
            return res.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Excepción en WhatsAppService.send_text: {e}")
            return False

    def send_to_group(self, group_jid: str, text: str):
        """Envía reportes a grupos."""
        if not group_jid:
            logger.warning("GROUP_JID no configurado. Saltando envío grupal.")
            return False
            
        url = f"{self.api_url}/message/sendText/{self.instance}"
        payload = {
            "number": group_jid,
            "text": text
        }
        try:
            logger.info(f"Enviando reporte al grupo: {group_jid}")
            res = requests.post(url, json=payload, headers=self._get_headers())
            return res.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Error en WhatsAppService.send_to_group: {e}")
            return False

whatsapp = WhatsAppService()
