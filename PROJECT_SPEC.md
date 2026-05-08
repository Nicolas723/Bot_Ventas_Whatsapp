# Especificación del Proyecto: BekaBot v3.0 - Gestión de Ventas WhatsApp

BekaBot es un ecosistema inteligente diseñado para **Laminados Beka**, que transforma una conversación de WhatsApp en un potente sistema de gestión de pedidos y control de equipo de ventas.

---

## 1. Visión para el Cliente (¿Qué hace el bot?)

El bot actúa como un asistente de ventas 24/7 que organiza la operación de la empresa de la siguiente manera:

### 🚀 Flujo del Vendedor
*   **Registro Automático**: La primera vez que un vendedor escribe, el bot le da la bienvenida y registra su nombre para que todos sus pedidos estén identificados.
*   **Captura Inteligente**: El vendedor envía un mensaje natural (ej: *"3 láminas blancas 200k para Juan en Chía ruta lunes"*). La IA extrae productos, precios, bodega, cliente y fecha automáticamente.
*   **Confirmación Asistida**: El bot presenta un resumen profesional y permite confirmar o corregir simplemente respondiendo con números (**1** para sí, **2** para no).
*   **Gestión de Pedidos**: Los vendedores pueden ver sus pedidos pendientes y modificarlos de forma guiada eligiendo el ID de una lista.

### 📢 Comunicación Grupal
*   **Reportes en Tiempo Real**: Cada vez que un pedido se confirma, el bot envía automáticamente una lista actualizada de todos los pedidos del día al grupo principal de WhatsApp de la empresa.

### 🕵️‍♂️ Control Administrativo (Solo Admins)
*   **Reporte Global**: Con un solo número, el administrador ve qué ha vendido cada persona del equipo en el día.
*   **Gestión de Usuarios**: El administrador puede autorizar nuevos vendedores, bloquear accesos o promover a otros a administradores mediante comandos de texto sencillos.

---

## 2. Arquitectura Técnica (¿Cómo funciona?)

El sistema utiliza una arquitectura de **Navegación Numérica Contextual**, diseñada para la máxima estabilidad en conexiones móviles.

### 🏗️ Stack Tecnológico
*   **Motor Principal**: Python 3.10+ con **FastAPI**.
*   **Cerebro (IA)**: **Groq (Llama-3)** para el procesamiento de lenguaje natural y extracción de datos estructurados (JSON).
*   **Base de Datos**: **PostgreSQL** para la persistencia de usuarios, pedidos y estados.
*   **Puerta de Enlace**: **Evolution API v2**, que gestiona la conexión con WhatsApp Web y la entrega de mensajes.
*   **Infraestructura**: **Docker & Docker Compose** para asegurar que todo corra igual en cualquier servidor.

### 🔄 Máquina de Estados
El bot no responde al azar; utiliza una máquina de estados finitos para saber en qué parte de la conversación está el usuario:
1.  `capturando_nombre`: Primera interacción, esperando nombre del vendedor.
2.  `menu:principal`: Navegación base.
3.  `capturando`: La IA está procesando los datos del pedido.
4.  `menu:confirmacion_pedido`: Esperando validación del resumen.
5.  `menu:pedidos`: Exploración de historial.
6.  `esperando_id_modificar`: Usuario seleccionó modificar y el bot espera el número del pedido.

### 🤖 Lógica de la IA (Fusión Inteligente)
El sistema de IA está configurado para realizar **actualizaciones incrementales**. Si un usuario corrige un pedido diciendo *"son 2 unidades"*, la IA mantiene los productos anteriores, precios y cliente, modificando estrictamente lo que el usuario indicó.

---

## 3. Seguridad y Configuración
*   **Acceso Restringido**: Solo los números autorizados o definidos en la lista de `ADMIN_PHONES` pueden interactuar con el bot.
*   **Variables de Entorno**: Toda la configuración sensible (API Keys, URLs de DB, JID de Grupo) se gestiona mediante un archivo `.env` protegido.

---

## 4. Estructura de Archivos Clave
*   `main.py`: Punto de entrada y receptor de Webhooks.
*   `handlers/private.py`: El corazón de la lógica de menús y estados.
*   `services/pedidos/creator.py`: Lógica de negocio para procesar, guardar y reportar pedidos.
*   `utils/parser_ia.py`: Prompt Engineering para la comunicación con Llama-3.
*   `models/`: Definición de consultas SQL para Pedidos y Usuarios.
