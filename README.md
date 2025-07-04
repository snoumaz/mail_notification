# Email to Telegram Notification Bot

Este programa es un bot que monitorea una cuenta de correo electrónico para detectar nuevos mensajes no leídos y envía notificaciones a un chat de Telegram basándose en ciertos criterios como el remitente, palabras clave en el asunto o el dominio del correo.

## Funcionalidad

- Se conecta a un servidor IMAP para revisar correos no leídos.
- Decodifica y procesa los correos para extraer información relevante como remitente, asunto y fragmento del mensaje.
- Clasifica los correos según grupos de remitentes definidos en un archivo JSON (`sender_groups.json`).
- Envía notificaciones a un chat de Telegram usando un bot, con formato Markdown para mejor legibilidad.
- Permite configurar dominios y palabras clave para filtrar notificaciones.
- Corre en un ciclo continuo revisando correos cada 60 segundos.

## Archivos principales

- `main.py`: Código principal del bot.
- `sender_groups.json`: Archivo JSON que contiene grupos de remitentes para clasificar los correos.
- `.env`: Archivo de configuración con variables de entorno para credenciales y tokens.
- `test_main.py`: Pruebas unitarias para las funciones del bot.

## Variables de entorno necesarias

El archivo `.env` debe contener las siguientes variables:

- `IMAP_SERVER`: Servidor IMAP para acceder al correo.
- `MAIL`: Dirección de correo electrónico.
- `PASS`: Contraseña o token de aplicación para el correo.
- `TELEGRAM_TOKEN`: Token del bot de Telegram.
- `TELEGRAM_CHAT_ID`: ID del chat de Telegram donde se enviarán las notificaciones.
- `NOTIFY_DOMAINS`: Lista separada por comas de dominios para notificar siempre.

## Uso

Para ejecutar el bot:

```bash
python main.py
```

El bot se ejecutará en un ciclo infinito revisando correos cada 60 segundos.

### Comando para enviar un mensaje de prueba a Telegram

```bash
python main.py test_telegram
```

Esto enviará un mensaje de prueba al chat configurado en Telegram para verificar que la integración funciona correctamente.

## Docker

El proyecto incluye un `dockerfile` y un `docker-compose.yml` para ejecutar el bot en un contenedor Docker.

Para construir y ejecutar el contenedor:

```bash
docker-compose up --build
```

## Notas

- Asegúrese de que el archivo `sender_groups.json` esté correctamente configurado con los grupos y remitentes deseados.
- El bot utiliza MarkdownV2 para formatear los mensajes en Telegram, por lo que algunos caracteres especiales son escapados automáticamente.
- El bot está configurado para reiniciarse automáticamente en caso de fallo cuando se ejecuta con Docker Compose.

## Licencia

Este proyecto es de código abierto y puede ser modificado y distribuido libremente.

---

Si necesita ayuda adicional o desea contribuir, por favor abra un issue o un pull request en el repositorio correspondiente.
