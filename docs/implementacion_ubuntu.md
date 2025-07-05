# Guía Completa: Implementación del Monitor de Correos en Ubuntu

## 🗓️ Resumen Diario de Correos

El sistema envía automáticamente un **resumen diario** a Telegram con los remitentes y asuntos de todos los correos procesados durante el día. El horario se configura con la variable `DAILY_SUMMARY_TIME` en el archivo `.env` (por defecto `21:00`).

- El resumen incluye: total de correos, agrupación por clasificación y grupo, y detalle de remitente/asunto.
- Puedes enviar el resumen manualmente en cualquier momento con:

```bash
python main.py send_summary
```

Asegúrate de tener en tu `.env`:

```env
DAILY_SUMMARY_TIME=21:00
```

---

## 📋 Índice

1. [Requisitos Previos](#requisitos-previos)
2. [Preparación del Servidor](#preparación-del-servidor)
3. [Configuración de Gmail](#configuración-de-gmail)
4. [Configuración de Telegram](#configuración-de-telegram)
5. [Instalación del Software](#instalación-del-software)
6. [Configuración del Monitor](#configuración-del-monitor)
7. [Configuración como Servicio](#configuración-como-servicio)
8. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)
9. [Solución de Problemas](#solución-de-problemas)

---

## 🔧 Requisitos Previos

### Hardware Mínimo Recomendado

- **CPU**: 1 núcleo
- **RAM**: 512 MB
- **Almacenamiento**: 10 GB
- **Red**: Conexión a Internet estable

### Software Requerido

- **Sistema Operativo**: Ubuntu 20.04 LTS o superior
- **Python**: 3.8 o superior
- **Git**: Para clonar el repositorio

---

## 🖥️ Preparación del Servidor

### 1. Actualizar el Sistema

```bash
# Conectar al servidor via SSH
ssh usuario@tu-servidor.com

# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
sudo apt install -y python3 python3-pip python3-venv git curl wget
```

### 2. Crear Usuario Dedicado (Recomendado)

```bash
# Crear usuario para el servicio
sudo useradd -m -s /bin/bash emailmonitor
sudo usermod -aG sudo emailmonitor

# Cambiar al usuario
sudo su - emailmonitor
```

### 3. Verificar Python

```bash
# Verificar versión de Python
python3 --version

# Debe mostrar Python 3.8 o superior
```

---

## 📧 Configuración de Gmail

### 1. Habilitar Autenticación de Dos Factores

1. **Acceder a tu cuenta de Google**

   - Ve a [myaccount.google.com](https://myaccount.google.com)
   - Inicia sesión con tu cuenta de Gmail

2. **Activar 2FA**
   - Ve a "Seguridad" → "Verificación en dos pasos"
   - Sigue los pasos para activar la autenticación de dos factores

### 2. Generar Contraseña de Aplicación

1. **Acceder a contraseñas de aplicación**

   - Ve a "Seguridad" → "Contraseñas de aplicación"
   - O directamente: [Contraseñas de aplicación](https://myaccount.google.com/apppasswords)

2. **Crear nueva contraseña**

   - Selecciona "Otra (nombre personalizado)"
   - Escribe un nombre como "Monitor de Correos"
   - Haz clic en "Generar"

3. **Guardar la contraseña**
   - Se mostrará una contraseña de 16 caracteres
   - **IMPORTANTE**: Guárdala en un lugar seguro, no la compartas

### 3. Configuración IMAP

1. **Verificar configuración IMAP**

   - Ve a Gmail → Configuración → Reenvío y correo POP/IMAP
   - Asegúrate de que IMAP esté habilitado

2. **Configuración del servidor**
   - **Servidor IMAP**: `imap.gmail.com`
   - **Puerto**: 993 (SSL)
   - **Usuario**: Tu dirección de Gmail completa
   - **Contraseña**: La contraseña de aplicación generada

### 4. Configuración para Otros Proveedores

#### Outlook/Hotmail

```
Servidor IMAP: outlook.office365.com
Puerto: 993
```

#### Yahoo

```
Servidor IMAP: imap.mail.yahoo.com
Puerto: 993
```

#### Proveedores Personalizados

Consulta con tu proveedor de correo los datos IMAP específicos.

---

## 📱 Configuración de Telegram

### 1. Crear un Bot de Telegram

1. **Abrir Telegram**

   - Instala Telegram en tu dispositivo
   - Inicia sesión con tu cuenta

2. **Contactar a BotFather**

   - Busca `@BotFather` en Telegram
   - Inicia una conversación con él

3. **Crear nuevo bot**

   ```
   /newbot
   ```

4. **Configurar el bot**

   - **Nombre del bot**: Ej: "Monitor de Correos"
   - **Username del bot**: Debe terminar en "bot" (ej: `mi_monitor_bot`)

5. **Obtener el token**
   - BotFather te enviará un mensaje con el token
   - **IMPORTANTE**: Guárdalo en un lugar seguro
   - Ejemplo: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. Obtener el Chat ID

#### Método 1: Usando el Bot

1. **Iniciar conversación con tu bot**

   - Busca tu bot por username
   - Haz clic en "Start" o envía `/start`

2. **Enviar mensaje de prueba**

   - Envía cualquier mensaje al bot

3. **Obtener Chat ID**
   - Ve a: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
   - Reemplaza `<TU_TOKEN>` con tu token real
   - Busca el campo `"chat":{"id":123456789}`

#### Método 2: Usando @userinfobot

1. **Contactar a @userinfobot**

   - Busca `@userinfobot` en Telegram
   - Inicia conversación

2. **Obtener tu Chat ID**
   - El bot te enviará tu información
   - Anota tu Chat ID

### 3. Configurar Notificaciones

1. **Crear grupo (opcional)**

   - Crea un grupo en Telegram
   - Agrega tu bot al grupo
   - Obtén el Chat ID del grupo usando el método anterior

2. **Configurar permisos**
   - Asegúrate de que el bot pueda enviar mensajes
   - En grupos, puede ser necesario hacer admin al bot

---

## 💻 Instalación del Software

### 1. Clonar el Repositorio

```bash
# Cambiar al directorio home del usuario
cd ~

# Clonar el repositorio
git clone https://github.com/dav-tech-work/mail_notification.git
cd organizador

# Verificar que se clonó correctamente
ls -la

# Verificar archivos principales
ls -la main.py email_monitor.py logging_config.py setup.py
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Verificar que está activado (debe mostrar la ruta del venv)
which python
```

### 3. Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
python -c "import transformers, telegram; print('Dependencias instaladas correctamente')"
```

### 4. Crear Directorios Necesarios

```bash
# Crear directorios para logs y datos
mkdir -p logs data

# Verificar permisos
ls -la
```

---

## ⚙️ Configuración del Monitor

### 1. Configuración Automatizada (Recomendado)

```bash
# Ejecutar script de configuración
python setup.py
```

El script te guiará a través de:

- Configuración de variables de entorno
- Configuración de grupos de remitentes
- Pruebas de conexión
- Creación del servicio systemd

### 2. Configuración Manual

#### Crear archivo .env

```bash
# Crear archivo de configuración
cp config.example .env
nano .env
```

**Nota**: El archivo `config.example` contiene todas las variables necesarias con valores de ejemplo.

**Contenido del archivo .env:**

```bash
# Configuración del servidor IMAP
IMAP_SERVER=imap.gmail.com
MAIL=tu-email@gmail.com
PASS=tu-contraseña-de-aplicación

# Configuración de Telegram
TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Configuración opcional
NOTIFY_DOMAINS=gmail.com,hotmail.com,outlook.com
LABEL_CANDIDATES=Urgente,Importante,Otros
LOG_LEVEL=INFO
DAILY_SUMMARY_TIME=21:00
CHECK_INTERVAL=120
CLEANUP_DAYS=30
```

#### Configurar grupos de remitentes

```bash
# Editar archivo de grupos
nano sender_groups.json
```

**Ejemplo de contenido:**

```json
{
  "Trabajo": ["jefe@empresa.com", "hr@empresa.com", "soporte@empresa.com"],
  "Bancos": ["notificaciones@banco.com", "alertas@tarjeta.com"],
  "Servicios": ["facturas@servicio.com", "soporte@servicio.com"],
  "Familia": ["mama@gmail.com", "hermano@hotmail.com"]
}
```

### 3. Probar la Configuración

```bash
# Probar conexión a Telegram
python main.py test_telegram

# Probar clasificación de emails
python main.py test_classify

# Ejecutar pruebas completas
python -m pytest test_main.py -v
```

---

## 🔄 Configuración como Servicio

### 1. Crear Servicio Systemd

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/email-monitor.service
```

**Contenido del servicio:**

```ini
[Unit]
Description=Email Monitor Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=emailmonitor
Group=emailmonitor
WorkingDirectory=/home/emailmonitor/organizador
Environment=PATH=/home/emailmonitor/organizador/venv/bin
ExecStart=/home/emailmonitor/organizador/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Configuración de seguridad
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/emailmonitor/organizador/logs /home/emailmonitor/organizador/data

[Install]
WantedBy=multi-user.target
```

### 2. Configurar Permisos

```bash
# Ajustar permisos del directorio
sudo chown -R emailmonitor:emailmonitor /home/emailmonitor/organizador

# Dar permisos de escritura a logs y data
sudo chmod 755 /home/emailmonitor/organizador/logs
sudo chmod 755 /home/emailmonitor/organizador/data
```

### 3. Habilitar y Iniciar el Servicio

```bash
# Recargar configuración de systemd
sudo systemctl daemon-reload

# Habilitar el servicio (inicia automáticamente al arrancar)
sudo systemctl enable email-monitor.service

# Iniciar el servicio
sudo systemctl start email-monitor.service

# Verificar estado
sudo systemctl status email-monitor.service
```

### 4. Verificar Logs del Servicio

```bash
# Ver logs en tiempo real
sudo journalctl -u email-monitor.service -f

# Ver logs de las últimas 100 líneas
sudo journalctl -u email-monitor.service -n 100

# Ver logs desde el inicio
sudo journalctl -u email-monitor.service --since "2024-01-01"
```

---

## 📊 Monitoreo y Mantenimiento

### 1. Verificar Estado del Servicio

```bash
# Estado del servicio
sudo systemctl status email-monitor.service

# Verificar si está ejecutándose
ps aux | grep python

# Verificar uso de recursos
htop
```

### 2. Monitorear Logs

```

```

## ⚡ Comandos Útiles

| Acción                       | Comando                                  |
| ---------------------------- | ---------------------------------------- |
| Ejecutar monitor principal   | `python main.py`                         |
| Probar notificación Telegram | `python main.py test_telegram`           |
| Probar clasificación IA      | `python main.py test_classify`           |
| Ejecutar tests               | `python -m pytest tests/test_main.py -v` |
| Enviar resumen diario manual | `python main.py send_summary`            |

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
