# 🤖 WhatsApp Order Bot Backend

Este es un backend robusto y modular desarrollado con **FastAPI** para gestionar pedidos a través de WhatsApp. Está diseñado para ser utilizado por vendedores internos, permitiendo registrar ventas de forma rápida mediante mensajes de texto, utilizando una combinación de **Regex** e **IA** para la extracción de datos.

## 🚀 Tecnologías

*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
*   **Base de Datos:** [PostgreSQL](https://www.postgresql.org/) (Hosteado en [Supabase](https://supabase.com/))
*   **Servidor Web:** [Uvicorn](https://www.uvicorn.org/)
*   **ORM/Driver:** `psycopg2`
*   **Despliegue:** Preparado para [Render](https://render.com/)

## ✨ Funcionalidades

1.  **Gestión de Estados:** Mantiene el contexto de la conversación por cada usuario (vendedor).
2.  **Extracción de Datos:**
    *   **Regex:** Identifica precios, tiendas y orígenes mediante patrones definidos.
    *   **IA (Simulada):** Fallback inteligente para mensajes complejos (preparado para integración con OpenAI).
3.  **Flujo de Confirmación:** Valida que todos los datos estén presentes antes de solicitar una confirmación final ("si"/"no").
4.  **Persistencia Temporal:** Guarda datos parciales en una tabla temporal para que el usuario pueda completar el pedido paso a paso.
5.  **Reportes Diarios:** Genera automáticamente un resumen de los pedidos realizados por el vendedor durante el día actual.

## 📁 Estructura del Proyecto

```text
├── main.py              # Punto de entrada (FastAPI)
├── db.py                # Conexión y configuración de PostgreSQL
├── create_db.py         # Script para inicializar tablas en Supabase
├── models/              # Lógica de base de datos por entidad
│   ├── usuarios.py
│   ├── pedidos.py
│   └── pedidos_temp.py
├── services/            # Lógica de negocio y estados
│   ├── estado_service.py
│   └── pedido_service.py
├── utils/               # Parsers (Regex e IA)
│   ├── parser_regex.py
│   └── parser_ia.py
├── test_bot.py          # Script de prueba local
├── Procfile             # Configuración para Render
└── requirements.txt     # Dependencias del proyecto
```

## 🛠️ Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio
```

### 2. Configurar variables de entorno
Crea un archivo `.env` basado en `.env.example`:
```env
DATABASE_URL=your_supabase_postgresql_url
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Inicializar la base de datos
Este comando creará las tablas necesarias en tu instancia de Supabase:
```bash
python create_db.py
```

### 5. Ejecutar localmente
```bash
python main.py
```

## 🧪 Pruebas
Puedes simular mensajes de WhatsApp usando el script de prueba incluido:
```bash
python test_bot.py
```

## 🌐 Despliegue en Render
1.  Crea un nuevo **Web Service** en Render.
2.  Conecta tu repositorio de GitHub.
3.  Configura la variable de entorno `DATABASE_URL`.
4.  Render detectará automáticamente el `Procfile` y desplegará la aplicación.

---
Desarrollado para la gestión eficiente de pedidos vía WhatsApp. 📈
