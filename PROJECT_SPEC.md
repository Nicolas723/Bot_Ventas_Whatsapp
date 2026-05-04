# Especificación del Proyecto: Bot de Ventas WhatsApp - Laminados Beka

Este documento describe la arquitectura, lógica y flujo del bot de gestión de pedidos para **Laminados Beka**, especialistas en láminas, formicas y materiales para carpintería.

## 1. Visión General
El bot automatiza la captura de pedidos de láminas y materiales afines a través de WhatsApp, procesando lenguaje natural para extraer datos estructurados y guardarlos en una base de datos PostgreSQL (Supabase).

## 2. Stack Tecnológico
- **Backend**: Python 3.10+ con FastAPI.
- **Base de Datos**: PostgreSQL para persistencia.
- **Caché/Sesiones**: Redis (utilizado por Evolution API).
- **IA (NLP)**: Modelos Llama-3 (vía Groq) y Gemini.
- **Integración WhatsApp**: Evolution API (basada en Baileys).

## 3. Infraestructura y Despliegue (Docker Full)
El proyecto está diseñado para ejecutarse íntegramente en un entorno de **Docker**, utilizando **Docker Compose** para la orquestación de microservicios:

1.  **Contenedor `bot_app`**: Ejecuta el backend de FastAPI que procesa los webhooks y la lógica de negocio de Laminados Beka.
2.  **Contenedor `evolution_api`**: Gestiona la conexión con WhatsApp y proporciona la interfaz API para enviar mensajes.
3.  **Contenedor `postgres_db`**: Base de datos relacional para usuarios, pedidos y configuraciones.
4.  **Contenedor `redis_cache`**: Soporte para la gestión de sesiones y colas de mensajes de Evolution API.

Este enfoque garantiza la portabilidad total entre entornos de desarrollo local y servidores de producción (VPS/Render).

## 4. Lógica de Negocio Crítica

### A. Extracción de Pedidos
- **Precio Unitario Prioritario**: Cualquier valor numérico asociado a un producto se trata estrictamente como **Precio Unitario**. El sistema calcula el total multiplicando `cantidad * precio_unitario`.
- **Detección de Datos**: Extrae Cliente, Productos, Bodega, Método de Envío y Fecha de Entrega.
- **Manejo de Fechas**: Soporta lenguaje relativo ("hoy", "mañana", "lunes") traduciéndolo a formato `YYYY-MM-DD`.

### B. Estados de Conversación
1. `nuevo`: Usuario no registrado.
2. `esperando_nombre`: Captura del nombre del vendedor.
3. `inicio`: Estado listo para recibir datos de pedido.
4. `capturando`: Faltan datos (ej: falta la bodega).
5. `confirmacion`: Resumen generado esperando "sí", "no" o correcciones.

### C. Controles de Administrador
- **ADMIN_PHONES**: Lista de números con permisos especiales definidos en `.env`.
- **Comandos**:
  - `bloquear [fecha]`: Impide registrar pedidos para un día específico.
  - `desbloquear [fecha]`: Habilita la fecha nuevamente.
- **Reporte Grupal**: Al escribir "pedido" en un grupo de WhatsApp, el bot envía un resumen consolidado de los pedidos cuya `fecha_entrega` es el día actual.

## 5. Estructura de Datos (Tablas Clave)
- `usuarios`: `telefono`, `nombre`, `estado`.
- `pedidos`: `cliente`, `precio` (total), `bodega`, `metodo_envio`, `productos` (texto formateado), `fecha_entrega`.
- `fechas_bloqueadas`: `fecha` (DATE).

## 6. Próximos Pasos (Hoja de Ruta)
- **Base de Datos de Tiendas**: Crear tabla `tiendas` con `nombre`, `direccion`, `geolocalizacion` y `horarios`.
- **Validación Geográfica**: Validar si la bodega seleccionada tiene cobertura para el método de envío elegido.
- **Integración de Facturación**: Exportar pedidos confirmados a un sistema contable vía API.

## 7. Instrucciones para la IA de Documentación
Al analizar este código, prioriza siempre el archivo `services/pedido_service.py` para la lógica de flujo y `utils/parser_ia.py` para las reglas de extracción de precios y fechas. El sistema debe mantener la integridad de los precios unitarios en todo momento.
