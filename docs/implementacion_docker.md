# Guía de Implementación con Docker

## 📋 Índice

1. [Requisitos Previos](#requisitos-previos)
2. [Preparación del Entorno](#preparación-del-entorno)
3. [Configuración de Gmail](#configuración-de-gmail)
4. [Configuración de Telegram](#configuración-de-telegram)
5. [Configuración del Proyecto](#configuración-del-proyecto)
6. [Despliegue con Docker](#despliegue-con-docker)
7. [Gestión y Mantenimiento](#gestión-y-mantenimiento)
8. [Solución de Problemas](#solución-de-problemas)
9. [Resumen Diario de Correos](#resumen-diario-de-correos)

---

## 🔧 Requisitos Previos

- Docker instalado ([Guía oficial](https://docs.docker.com/get-docker/))
- Docker Compose instalado ([Guía oficial](https://docs.docker.com/compose/install/))
- Acceso a una cuenta de Gmail y Telegram
- Token de bot y Chat ID de Telegram (ver secciones siguientes)

---

## 🖥️ Preparación del Entorno

1. Clona el repositorio en tu máquina o servidor:

```bash
git clone https://github.com/dav-tech-work/mail_notification.git
cd mail_notification
```

2. Crea los archivos de configuración necesarios:

```bash
cp config.example .env
# El archivo sender_groups.json ya existe en el repositorio
```

---

## 📧 Configuración de Gmail

Sigue los mismos pasos que en la [guía de Ubuntu](./implementacion_ubuntu.md#configuración-de-gmail) para:

- Activar 2FA
- Generar una contraseña de aplicación
- Habilitar IMAP

---

## 📱 Configuración de Telegram

Sigue los mismos pasos que en la [guía de Ubuntu](./implementacion_ubuntu.md#configuración-de-telegram) para:

- Crear un bot con BotFather
- Obtener el token del bot
- Obtener el Chat ID

---

## ⚙️ Configuración del Proyecto

1. Edita el archivo `.env` con tus datos reales:

```env
IMAP_SERVER=imap.gmail.com
MAIL=tu-email@gmail.com
PASS=tu-contraseña-de-aplicación
TELEGRAM_TOKEN=token_de_tu_bot
TELEGRAM_CHAT_ID=tu_chat_id
NOTIFY_DOMAINS=gmail.com,hotmail.com
LABEL_CANDIDATES=Urgente,Importante,Otros
LOG_LEVEL=INFO
```

2. Edita `sender_groups.json` para definir los grupos de remitentes:

```json
{
  "Trabajo": ["jefe@empresa.com", "hr@empresa.com"],
  "Familia": ["mama@gmail.com"]
}
```

---

## 🚀 Despliegue con Docker

1. Construye y levanta el servicio:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

Esto creará el contenedor, instalará dependencias y ejecutará el monitor automáticamente.

3. Verifica que el contenedor esté corriendo:

```bash
docker ps
```

4. Consulta los logs:

```bash
docker logs organizador_email_monitor
```

---

## 🛠️ Gestión y Mantenimiento

- **Reiniciar el servicio:**
  ```bash
  docker compose -f docker/docker-compose.yml restart
  ```
- **Detener el servicio:**
  ```bash
  docker compose -f docker/docker-compose.yml down
  ```
- **Actualizar el código:**
  ```bash
  git pull origin main
  docker compose -f docker/docker-compose.yml up --build -d
  ```
- **Ver logs en tiempo real:**
  ```bash
  docker logs -f organizador_email_monitor
  ```
- **Acceso a archivos de configuración y logs:**
  - `.env` y `sender_groups.json` están montados como volúmenes.
  - Los logs se guardan en el directorio `logs/` del proyecto.

---

## ❗ Solución de Problemas

- **El contenedor se detiene al iniciar:**
  - Verifica los logs con `docker logs organizador_email_monitor`.
  - Revisa que `.env` y `sender_groups.json` estén correctamente configurados.
- **No llegan notificaciones a Telegram:**
  - Verifica el token y chat ID.
  - Prueba la conexión con `python main.py test_telegram` (puedes ejecutar comandos dentro del contenedor con `docker exec -it organizador_email_monitor bash`).
- **Errores de conexión IMAP:**
  - Revisa usuario, contraseña y configuración IMAP.
- **Actualizar dependencias:**
  - Modifica `requirements.txt` y reconstruye el contenedor.

---

## 📞 Soporte

- Consulta la [guía de Ubuntu](./implementacion_ubuntu.md) para detalles avanzados, solución de problemas y ejemplos de configuración.
- Abre un issue en GitHub si encuentras algún problema.

## 🗓️ Resumen Diario de Correos

El sistema envía automáticamente un **resumen diario** a Telegram con los remitentes y asuntos de todos los correos procesados durante el día. El horario se configura con la variable `DAILY_SUMMARY_TIME` en el archivo `.env` (por defecto `21:00`).

- El resumen incluye: total de correos, agrupación por clasificación y grupo, y detalle de remitente/asunto.
- Puedes enviar el resumen manualmente en cualquier momento con:

```bash
docker exec -it organizador_email_monitor python main.py send_summary
```

Asegúrate de tener en tu `.env`:

```env
DAILY_SUMMARY_TIME=21:00
```

---

## ⚡ Comandos Útiles

| Acción                       | Comando                                                                  |
| ---------------------------- | ------------------------------------------------------------------------ |
| Ejecutar monitor principal   | `docker compose -f docker/docker-compose.yml up -d`                      |
| Ver logs                     | `docker logs -f organizador_email_monitor`                               |
| Probar notificación Telegram | `docker exec -it organizador_email_monitor python main.py test_telegram` |
| Probar clasificación IA      | `docker exec -it organizador_email_monitor python main.py test_classify` |
| Ejecutar tests               | `docker exec -it organizador_email_monitor python -m pytest tests/ -v`   |
| Enviar resumen diario manual | `docker exec -it organizador_email_monitor python main.py send_summary`  |

---

## 🛠️ Ejemplo de archivo `.env`

```env
IMAP_SERVER=imap.gmail.com
MAIL=tu-email@gmail.com
PASS=tu-contraseña-de-aplicación
TELEGRAM_TOKEN=token_de_tu_bot
TELEGRAM_CHAT_ID=tu_chat_id
NOTIFY_DOMAINS=gmail.com,hotmail.com
LABEL_CANDIDATES=Urgente,Importante,Otros
LOG_LEVEL=INFO
DAILY_SUMMARY_TIME=21:00
```

---
