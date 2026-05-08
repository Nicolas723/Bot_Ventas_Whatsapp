import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- Evolution API ---
    EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
    EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
    EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME", "MiBot")

    # --- Database ---
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_PORT = os.getenv("DB_PORT", "5432")

    # --- IA (Groq) ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    IA_MODEL = "llama-3.3-70b-versatile"

    # --- Negocio ---
    ADMIN_PHONES = [p.strip() for p in (os.getenv("ADMIN_PHONES") or "").split(",") if p.strip()]
    GROUP_JID = os.getenv("GROUP_JID") # JID del grupo de ventas
    METODOS_ENVIO = ["Ruta", "Bicicleta", "Recoger en punto", "Transportadora"]
    
    # --- Logs ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "logs/bot.log"

config = Config()
