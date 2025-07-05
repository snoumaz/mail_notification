# Guía de Solución de Problemas - Servicio Systemd

## 🔍 Diagnóstico del Error `status=203/EXEC`

El error `status=203/EXEC` indica que systemd no puede ejecutar el comando especificado en el servicio. Esto suele ocurrir por problemas con las rutas, permisos o configuración.

---

## 🚀 Solución Rápida

### 1. Usar el Script de Diagnóstico

```bash
# Ejecutar diagnóstico automático
python src/utils/setup.py diagnose
```

### 2. Recrear el Servicio

```bash
# Detener y deshabilitar el servicio actual
sudo systemctl stop email-monitor.service
sudo systemctl disable email-monitor.service

# Recrear el servicio con el script mejorado
python src/utils/setup.py
```

---

## 🔧 Diagnóstico Manual

### 1. Verificar Estado del Servicio

```bash
# Ver estado actual
sudo systemctl status email-monitor.service

# Ver logs detallados
sudo journalctl -u email-monitor.service -n 50 --no-pager
```

### 2. Verificar Rutas y Archivos

```bash
# Verificar que existe el entorno virtual
ls -la /home/emailmonitor/mail_notification/venv/bin/python

# Verificar permisos del directorio
ls -la /home/emailmonitor/mail_notification/

# Verificar que existe main.py
ls -la /home/emailmonitor/mail_notification/main.py
```

### 3. Verificar Archivo del Servicio

```bash
# Ver contenido del archivo de servicio
sudo cat /etc/systemd/system/email-monitor.service

# Verificar permisos del archivo
ls -la /etc/systemd/system/email-monitor.service
```

---

## 🛠️ Problemas Comunes y Soluciones

### Problema 1: Entorno Virtual No Existe

**Síntomas:**

- Error: `No such file or directory`
- El directorio `venv/` no existe

**Solución:**

```bash
# Crear entorno virtual
cd /home/emailmonitor/mail_notification
python3 -m venv venv

# Activar y instalar dependencias
source venv/bin/activate
pip install -r requirements.txt
```

### Problema 2: Rutas Incorrectas en el Servicio

**Síntomas:**

- Error: `ExecStart path is not absolute`
- Rutas relativas en lugar de absolutas

**Solución:**

```bash
# Verificar y corregir rutas en el archivo de servicio
sudo nano /etc/systemd/system/email-monitor.service
```

**Contenido correcto:**

```ini
[Unit]
Description=Email Monitor Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=emailmonitor
Group=emailmonitor
WorkingDirectory=/home/emailmonitor/mail_notification
Environment=PATH=/home/emailmonitor/mail_notification/venv/bin
ExecStart=/home/emailmonitor/mail_notification/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Configuración de seguridad
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/emailmonitor/mail_notification/logs /home/emailmonitor/mail_notification/data

[Install]
WantedBy=multi-user.target
```

### Problema 3: Permisos Incorrectos

**Síntomas:**

- Error: `Permission denied`
- El usuario no puede acceder a los archivos

**Solución:**

```bash
# Corregir permisos del directorio
sudo chown -R emailmonitor:emailmonitor /home/emailmonitor/mail_notification

# Corregir permisos del archivo de servicio
sudo chown root:root /etc/systemd/system/email-monitor.service
sudo chmod 644 /etc/systemd/system/email-monitor.service

# Crear directorios necesarios con permisos correctos
sudo mkdir -p /home/emailmonitor/mail_notification/logs
sudo mkdir -p /home/emailmonitor/mail_notification/data
sudo chown -R emailmonitor:emailmonitor /home/emailmonitor/mail_notification/logs
sudo chown -R emailmonitor:emailmonitor /home/emailmonitor/mail_notification/data
```

### Problema 4: Usuario No Existe

**Síntomas:**

- Error: `User does not exist`
- El usuario especificado no existe en el sistema

**Solución:**

```bash
# Crear usuario si no existe
sudo useradd -m -s /bin/bash emailmonitor

# O cambiar el usuario en el archivo de servicio
sudo nano /etc/systemd/system/email-monitor.service
# Cambiar User=emailmonitor por User=tu_usuario
```

### Problema 5: Dependencias Faltantes

**Síntomas:**

- Error: `ModuleNotFoundError`
- El servicio inicia pero falla al importar módulos

**Solución:**

```bash
# Activar entorno virtual y verificar dependencias
cd /home/emailmonitor/mail_notification
source venv/bin/activate
pip list

# Reinstalar dependencias si es necesario
pip install -r requirements.txt
```

---

## 🔄 Recargar y Reiniciar

Después de hacer cambios:

```bash
# Recargar configuración de systemd
sudo systemctl daemon-reload

# Reiniciar el servicio
sudo systemctl restart email-monitor.service

# Verificar estado
sudo systemctl status email-monitor.service

# Ver logs en tiempo real
sudo journalctl -u email-monitor.service -f
```

---

## 📋 Comandos de Verificación

```bash
# Verificar que el servicio está habilitado
sudo systemctl is-enabled email-monitor.service

# Verificar que el servicio está activo
sudo systemctl is-active email-monitor.service

# Ver logs desde el inicio
sudo journalctl -u email-monitor.service --since "1 hour ago"

# Ver logs con timestamps
sudo journalctl -u email-monitor.service -o short-precise
```

---

## 🆘 Si Nada Funciona

### 1. Ejecutar Manualmente

```bash
# Probar ejecución manual
cd /home/emailmonitor/mail_notification
source venv/bin/activate
python main.py
```

### 2. Usar Docker como Alternativa

```bash
# Usar Docker en lugar de systemd
docker compose -f docker/docker-compose.yml up -d
```

### 3. Crear Servicio Simple

```bash
# Crear un servicio más simple sin restricciones de seguridad
sudo nano /etc/systemd/system/email-monitor-simple.service
```

**Contenido:**

```ini
[Unit]
Description=Email Monitor Service (Simple)
After=network.target

[Service]
Type=simple
User=emailmonitor
WorkingDirectory=/home/emailmonitor/mail_notification
ExecStart=/home/emailmonitor/mail_notification/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 📞 Obtener Ayuda

Si los problemas persisten:

1. **Ejecutar diagnóstico completo:**

   ```bash
   python src/utils/setup.py diagnose
   ```

2. **Recopilar información:**

   ```bash
   # Estado del sistema
   sudo systemctl status email-monitor.service

   # Logs completos
   sudo journalctl -u email-monitor.service --no-pager > logs.txt

   # Información del sistema
   uname -a > system_info.txt
   python --version > python_info.txt
   ```

3. **Abrir un issue en GitHub** con la información recopilada.
