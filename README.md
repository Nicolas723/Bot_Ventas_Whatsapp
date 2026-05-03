# 🤖 WhatsApp Order Bot Backend

Este es un backend robusto y modular desarrollado con **FastAPI** y **Evolution API** para gestionar pedidos a través de WhatsApp. Está diseñado para ser utilizado por vendedores internos, permitiendo registrar ventas de forma rápida mediante mensajes de texto, utilizando una combinación de **Regex** y la inteligencia artificial de **Groq** para la extracción de datos.

## 🚀 Tecnologías

*   **API de WhatsApp:** [Evolution API v2](https://evolution-api.com/) (Self-hosted)
*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
*   **Base de Datos:** [PostgreSQL](https://www.postgresql.org/) (Hosteado localmente vía Docker)
*   **Caché / Memoria:** Redis (vía Docker)
*   **Inteligencia Artificial:** [Groq API](https://groq.com/) (Modelo Llama-3.1-8b-instant)
*   **Despliegue:** Docker Compose (Entorno 100% independiente)

## ✨ Funcionalidades

1.  **Gestión de Estados:** Mantiene el contexto de la conversación por cada usuario (vendedor).
2.  **Extracción de Datos:**
    *   **Regex:** Identifica precios, tiendas y orígenes mediante patrones rápidos.
    *   **IA de Groq:** Fallback ultra-rápido para entender lenguaje natural y estructurarlo en JSON ("el origen es whatsapp y se va en ruta").
3.  **Flujo de Confirmación Inteligente:** Detecta explícitamente si el usuario quiere "confirmar", "cancelar" o "modificar" un pedido antes de guardarlo.
4.  **Envíos de Resúmenes:** Reúne y envía los reportes directamente a un grupo preconfigurado de WhatsApp.
5.  **100% Autónomo:** Ya no depende de servicios de pago por mensaje como Twilio ni de bases de datos externas como Supabase.

## 📁 Estructura del Proyecto

```text
├── main.py              # Punto de entrada (FastAPI) y webhook de Evolution
├── db.py                # Conexión a PostgreSQL (Docker) y setup automático
├── docker-compose.yml   # Contenedores para Evolution, Postgres y Redis
├── setup_evolution.py   # Script para automatizar la creación de la instancia de WhatsApp
├── .env                 # Variables de entorno y credenciales
├── models/              # Lógica de base de datos por entidad
│   ├── usuarios.py
│   ├── pedidos.py
│   └── pedidos_temp.py
├── services/            # Lógica de negocio y estados
│   ├── estado_service.py
│   └── pedido_service.py
└── utils/               # Parsers (Regex e IA) y Baileys Utils
    ├── parser_regex.py
    ├── parser_ia.py
    └── baileys.py
```

## 🛠️ Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio
```

### 2. Levantar la infraestructura base (Docker)
Este comando descargará y encenderá Evolution API, PostgreSQL y Redis:
```bash
docker-compose up -d
```

### 3. Configurar variables de entorno
Asegúrate de contar con un archivo `.env` configurado:
```env
# Base de datos local
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/evolution

# Evolution API
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=tu_clave_secreta
EVOLUTION_INSTANCE_NAME=MiBot

# Configuración Grupo Destino
BAILEYS_API_URL=http://localhost:8080/message/sendText/MiBot
BAILEYS_GROUP_ID=12036...numero_del_grupo@g.us
BAILEYS_API_KEY=tu_clave_secreta

# GROQ API (Para parseo con Inteligencia Artificial)
GROQ_API_KEY=gsk_tu_api_key_aqui
```

### 4. Inicializar Bot
Ejecuta el bot de FastAPI localmente. Este script automáticamente creará las tablas en PostgreSQL si no existen:
```bash
python -m uvicorn main:app --reload
```

### 5. Conectar WhatsApp a Evolution
Abre otra terminal y ejecuta el script de setup para vincular el número:
```bash
python setup_evolution.py
```
Esto te imprimirá o abrirá un código QR. Escanéalo con tu dispositivo móvil desde WhatsApp > Dispositivos Vinculados.

---
Desarrollado para la gestión eficiente, rápida y **privada** de pedidos vía WhatsApp. 📈
