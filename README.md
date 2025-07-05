# Organizador: Monitor Inteligente de Correos con Notificaciones a Telegram

Organizador es una solución avanzada para la gestión y monitoreo de correos electrónicos, diseñada para profesionales y equipos que necesitan estar informados en tiempo real sobre mensajes importantes. El sistema conecta tu cuenta de correo (Gmail, Outlook, IMAP personalizado) y utiliza inteligencia artificial para clasificar los mensajes según su urgencia o relevancia, enviando notificaciones automáticas y personalizadas a Telegram.

- **Clasificación inteligente** mediante modelos de IA y reglas configurables.
- **Notificaciones inmediatas** a Telegram, con soporte para grupos y usuarios individuales.
- **Resumen diario automático** con remitentes y asuntos de todos los correos recibidos.
- **Arquitectura modular y segura**, lista para producción, con soporte para Docker y despliegue tradicional.
- **Configuración flexible**: define grupos de remitentes, dominios prioritarios, palabras clave y más.
- **Logging avanzado** y sistema de pruebas completo.

---

## 🚀 Guías de Implementación

Para una instalación y configuración detallada, consulta las siguientes guías según tu entorno preferido:

- [Implementación en Ubuntu/Linux (sin Docker)](./docs/implementacion_ubuntu.md)
- [Implementación con Docker](./docs/implementacion_docker.md)

Ambas guías cubren desde la preparación del entorno, configuración de Gmail y Telegram, hasta la puesta en marcha y solución de problemas.

---

## 🗓️ Resumen Diario de Correos

El sistema envía automáticamente un **resumen diario** a Telegram con los remitentes y asuntos de todos los correos procesados durante el día. El horario se configura con la variable `DAILY_SUMMARY_TIME` en el archivo `.env` (por defecto `21:00`).

- El resumen incluye: total de correos, agrupación por clasificación y grupo, y detalle de remitente/asunto.
- Puedes enviar el resumen manualmente en cualquier momento con:

```bash
python main.py send_summary
```

- Si usas Docker:

```bash
docker exec -it organizador_email_monitor python main.py send_summary
```

---

## ⚡ Comandos Útiles

| Acción                       | Comando                                                                 |
| ---------------------------- | ----------------------------------------------------------------------- |
| Ejecutar monitor principal   | `python main.py`                                                        |
| Probar notificación Telegram | `python main.py test_telegram`                                          |
| Probar clasificación IA      | `python main.py test_classify`                                          |
| Ejecutar tests               | `python -m pytest tests/ -v`                                            |
| Enviar resumen diario manual | `python main.py send_summary`                                           |
| Resumen manual en Docker     | `docker exec -it organizador_email_monitor python main.py send_summary` |

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

## Funcionalidades

### 🤖 Clasificación Inteligente

- **IA Avanzada**: Utiliza modelos de transformers para clasificar automáticamente los correos
- **Fallback Robusto**: Sistema de clasificación básica cuando la IA no está disponible
- **Categorías**: Urgente, Importante, Otros

### 📧 Procesamiento de Correos

- Se conecta a servidores IMAP para revisar correos no leídos
- Decodifica correctamente headers y contenido multipart
- Extrae información relevante: remitente, asunto y fragmento del mensaje
- Manejo robusto de errores de codificación y formato

### 🔔 Notificaciones Inteligentes

- Envía notificaciones a Telegram con formato HTML
- Filtra correos basándose en múltiples criterios:
  - Clasificación por IA
  - Palabras clave configurables
  - Dominios prioritarios
  - Grupos de remitentes

### ⚡ Rendimiento y Estabilidad

- Inicialización lazy del clasificador de IA
- Manejo robusto de errores y reconexión automática
- Logging detallado para diagnóstico
- Optimización de memoria y CPU

## Estructura del Proyecto

- `main.py`: Punto de entrada principal del programa
- `src/core/`: Lógica principal, monitor, clasificación, logging
- `src/utils/`: Herramientas y scripts auxiliares
- `tests/`: Pruebas unitarias y de integración
- `config.example`: Plantilla de variables de entorno
- `sender_groups.json`: Configuración de grupos de remitentes
- `requirements.txt`: Dependencias del proyecto
- `docker/`: Archivos Docker y Docker Compose
- `docs/`: Documentación y guías de implementación

---

## Mejoras Implementadas

### 🏗️ Arquitectura Modular

- **Separación de responsabilidades**: Código reorganizado en clases especializadas
- **Inyección de dependencias**: Mejor testabilidad y mantenibilidad
- **Type hints**: Código más legible y menos propenso a errores
- **Arquitectura limpia**: Eliminación de archivos obsoletos y conflictos

### 🔧 Configuración Avanzada

- **Script de instalación automatizada**: `src/utils/setup.py` para configuración guiada
- **Logging con rotación**: Sistema de logs avanzado con `src/core/logging_config.py`
- **Variables de entorno opcionales**: Configuración flexible
- **Configuración Docker mejorada**: Build local y usuario no-root

### 🧪 Testing Mejorado

- **Tests unitarios completos**: Cobertura de todas las clases principales
- **Mocks para servicios externos**: Tests aislados y confiables
- **Tests de integración**: Verificación del flujo completo

### 🔒 Seguridad

- **Docker seguro**: Configuración con mejores prácticas de seguridad
- **Usuario no-root**: Ejecución con privilegios mínimos
- **Logs sanitizados**: Sin información sensible en logs
- **Dependencias limpias**: Solo las librerías necesarias

### 📊 Monitoreo

- **Health checks**: Verificación automática del estado del servicio
- **Métricas de rendimiento**: Decoradores para medir tiempos de ejecución
- **Logs estructurados**: Información detallada para debugging

### 🚀 Despliegue

- **Servicio systemd**: Integración con el sistema operativo
- **Docker Compose mejorado**: Configuración lista para producción
- **Scripts de automatización**: Instalación y configuración simplificada

---

## Licencia

Este proyecto es de código abierto y puede ser modificado y distribuido libremente.

---

¿Dudas, sugerencias o problemas? Abre un issue en GitHub o consulta las guías en la carpeta `docs/`.
