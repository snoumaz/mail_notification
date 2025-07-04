# Email to Telegram Notification Bot

Este programa es un bot inteligente que monitorea una cuenta de correo electrónico para detectar nuevos mensajes no leídos y envía notificaciones a un chat de Telegram. Utiliza clasificación por IA y reglas configurables para determinar la importancia de los correos.

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

## Archivos principales

- `main.py`: Código principal del bot con todas las mejoras
- `sender_groups.json`: Configuración de grupos de remitentes
- `requirements.txt`: Dependencias del proyecto
- `.env`: Variables de entorno (crear desde `.env.example`)
- `test_main.py`: Suite completa de pruebas unitarias
- `dockerfile`: Configuración para contenedor Docker

## Instalación y Configuración

### 1. Clonar e instalar dependencias

```bash
git clone <repository-url>
cd organizador
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 3. Configurar grupos de remitentes

Edita `sender_groups.json` con tus contactos organizados por categorías.

## Variables de entorno necesarias

El archivo `.env` debe contener:

- `IMAP_SERVER`: Servidor IMAP (ej: imap.gmail.com)
- `MAIL`: Tu dirección de correo electrónico
- `PASS`: Contraseña de aplicación (no tu contraseña normal)
- `TELEGRAM_TOKEN`: Token del bot de Telegram
- `TELEGRAM_CHAT_ID`: ID del chat donde recibir notificaciones
- `NOTIFY_DOMAINS`: Dominios prioritarios (separados por comas)
- `LABEL_CANDIDATES`: Etiquetas de clasificación (opcional)

## Uso

### Ejecutar el monitor principal

```bash
python main.py
```

### Probar notificación de Telegram

```bash
python main.py test_telegram
```

### Probar clasificación de IA

```bash
python main.py test_classify
```

### Ejecutar pruebas

```bash
python -m pytest test_main.py -v
```

## Docker

El proyecto incluye un `dockerfile` y un `docker-compose.yml` para ejecutar el bot en un contenedor Docker.

### Construcción y ejecución básica

```bash
docker-compose up --build
```

### Configuración con Docker

1. **Crear el archivo .env**:

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

2. **Ajustar docker-compose.yml** (opcional):

```yaml
services:
  organizador:
    build: .
    container_name: organizador_email_bot
    volumes:
      - ./sender_groups.json:/app/sender_groups.json:ro
      - ./.env:/app/.env:ro
    restart: unless-stopped
    environment:
      - TZ=Europe/Madrid
```

3. **Ejecutar en segundo plano**:

```bash
docker-compose up -d
```

4. **Ver logs**:

```bash
docker-compose logs -f
```

5. **Detener el servicio**:

```bash
docker-compose down
```

## Integración en Servidor Debian

### Instalación directa en Debian/Ubuntu

#### 1. Preparar el sistema

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv git

# Crear usuario para el servicio (opcional pero recomendado)
sudo useradd -r -s /bin/false emailbot
sudo mkdir -p /opt/organizador
sudo chown emailbot:emailbot /opt/organizador
```

#### 2. Clonar e instalar

```bash
# Clonar el repositorio
cd /opt/organizador
sudo -u emailbot git clone <repository-url> .

# Crear entorno virtual
sudo -u emailbot python3 -m venv venv

# Activar entorno virtual e instalar dependencias
sudo -u emailbot bash -c "source venv/bin/activate && pip install -r requirements.txt"
```

#### 3. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
sudo -u emailbot cp .env.example .env

# Editar configuración
sudo -u emailbot nano .env
```

#### 4. Configurar como servicio systemd

```bash
# Crear archivo de servicio
sudo tee /etc/systemd/system/organizador.service > /dev/null <<EOF
[Unit]
Description=Email to Telegram Notification Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=emailbot
Group=emailbot
WorkingDirectory=/opt/organizador
Environment=PATH=/opt/organizador/venv/bin
ExecStart=/opt/organizador/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=organizador

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectHome=yes
ProtectSystem=strict
ReadWritePaths=/opt/organizador

[Install]
WantedBy=multi-user.target
EOF
```

#### 5. Habilitar e iniciar el servicio

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar el servicio para que inicie automáticamente
sudo systemctl enable organizador

# Iniciar el servicio
sudo systemctl start organizador

# Verificar estado
sudo systemctl status organizador
```

#### 6. Gestión del servicio

```bash
# Ver logs en tiempo real
sudo journalctl -u organizador -f

# Reiniciar servicio
sudo systemctl restart organizador

# Detener servicio
sudo systemctl stop organizador

# Ver logs de los últimos 100 registros
sudo journalctl -u organizador -n 100
```

### Integración con Docker en Debian

#### 1. Instalar Docker

```bash
# Actualizar el sistema
sudo apt update

# Instalar dependencias
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Añadir clave GPG oficial de Docker
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Añadir repositorio de Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose

# Añadir usuario al grupo docker (opcional)
sudo usermod -aG docker $USER
# Reloguearse para aplicar cambios de grupo
```

#### 2. Desplegar con Docker

```bash
# Crear directorio del proyecto
mkdir -p /opt/organizador
cd /opt/organizador

# Clonar repositorio
git clone <repository-url> .

# Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con tus credenciales

# Ejecutar con Docker Compose
docker-compose up -d

# Verificar que funciona
docker-compose logs -f
```

#### 3. Configurar inicio automático con systemd

```bash
# Crear servicio para Docker Compose
sudo tee /etc/systemd/system/organizador-docker.service > /dev/null <<EOF
[Unit]
Description=Organizador Email Bot Docker
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/organizador
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Habilitar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable organizador-docker
sudo systemctl start organizador-docker
```

### Monitoreo y Mantenimiento

#### Logs y debugging

```bash
# Para instalación directa
sudo journalctl -u organizador -f

# Para Docker
docker-compose logs -f organizador

# Ver uso de recursos
htop  # o top
docker stats  # para Docker
```

#### Actualizaciones

```bash
# Instalación directa
cd /opt/organizador
sudo -u emailbot git pull
sudo -u emailbot bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo systemctl restart organizador

# Docker
cd /opt/organizador
git pull
docker-compose down
docker-compose up --build -d
```

#### Configuración de firewall (si es necesario)

```bash
# Permitir conexiones salientes HTTPS (para Telegram y modelo de IA)
sudo ufw allow out 443

# Permitir conexiones salientes IMAP SSL
sudo ufw allow out 993

# Si usas un servidor IMAP personalizado
sudo ufw allow out <puerto_imap>
```

## Configuración Avanzada

### Variables de entorno adicionales

Añade estas variables a tu archivo `.env` para personalización avanzada:

```bash
# Intervalo de revisión de correos (en segundos, default: 60)
CHECK_INTERVAL=60

# Zona horaria para logs
TZ=Europe/Madrid

# Nivel de logging (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Límite de caracteres en el snippet (default: 200)
SNIPPET_LENGTH=200
```

### Configuración de grupos de remitentes

El archivo `sender_groups.json` permite organizar contactos por categorías:

```json
{
  "Trabajo": ["jefe@empresa.com", "rrhh@empresa.com"],
  "Personal": ["familia@email.com", "amigo@email.com"],
  "Servicios": ["banco@entidad.com", "facturacion@servicio.com"]
}
```

### Monitoreo del servicio

El bot revisa correos **cada 60 segundos** por defecto. Puedes monitorear su funcionamiento:

#### Verificar funcionamiento

```bash
# Ver logs en tiempo real
sudo journalctl -u organizador -f

# Estado del servicio
sudo systemctl status organizador

# Últimos errores
sudo journalctl -u organizador --priority=err
```

#### Métricas de rendimiento

```bash
# Uso de CPU y memoria
ps aux | grep python
systemctl show organizador --property=MainPID --value | xargs ps -o pid,ppid,cmd,%mem,%cpu -p
```

### Solución de problemas comunes

#### El bot no envía notificaciones

1. Verificar configuración de Telegram
2. Comprobar grupos en `sender_groups.json`
3. Revisar logs para errores de conexión

#### Problemas de conexión IMAP

1. Verificar credenciales en `.env`
2. Confirmar que tienes habilitado IMAP en tu correo
3. Para Gmail: usar contraseña de aplicación, no la contraseña normal

#### Errores de clasificación IA

1. El sistema funciona con fallback básico si falla la IA
2. Verificar que PyTorch está instalado correctamente
3. En servidores con poca memoria, la IA puede deshabilitarse automáticamente

### Backup y restauración

#### Respaldar configuración

```bash
# Crear backup de configuración
tar -czf organizador-backup-$(date +%Y%m%d).tar.gz \
  .env sender_groups.json

# Restaurar desde backup
tar -xzf organizador-backup-YYYYMMDD.tar.gz
```

## Notas

- **Frecuencia de revisión**: El bot revisa correos nuevos cada **60 segundos** (1 minuto)
- Asegúrese de que el archivo `sender_groups.json` esté correctamente configurado con los grupos y remitentes deseados
- El bot utiliza formato HTML para los mensajes en Telegram, con caracteres especiales escapados automáticamente
- Para Gmail, debe usar una **contraseña de aplicación**, no su contraseña normal
- El bot funciona incluso si la IA falla, usando clasificación básica por palabras clave
- En producción se recomienda usar la instalación con systemd para mayor estabilidad
- El contenedor Docker se reinicia automáticamente en caso de fallo

### Compatibilidad

- **Python**: 3.8+
- **Sistemas operativos**: Linux (Debian/Ubuntu recomendado), Windows, macOS
- **Servidores de correo**: Gmail, Outlook, servidores IMAP personalizados
- **Docker**: 20.10+

## Licencia

Este proyecto es de código abierto y puede ser modificado y distribuido libremente.

## Mejoras Implementadas ✨

### 🔧 Resolución de Problemas Críticos

- **Inicialización Lazy de IA**: El clasificador se carga solo cuando es necesario, evitando errores de inicio
- **Sistema de Fallback**: Clasificación básica por palabras clave cuando la IA no está disponible
- **Manejo Robusto de Errores**: Mejor gestión de excepciones y reconexión automática

### 🚀 Optimizaciones de Rendimiento

- **Logging Mejorado**: Información detallada del estado del sistema
- **Validación de Datos**: Verificaciones exhaustivas antes del procesamiento
- **Gestión de Memoria**: Optimización del uso de recursos

### 🧪 Testing y Calidad

- **Suite de Pruebas Completa**: Tests unitarios para todas las funciones críticas
- **Soporte Async**: Pruebas asíncronas para funciones de Telegram
- **Requirements.txt**: Gestión adecuada de dependencias

### 🛡️ Seguridad y Estabilidad

- **Manejo de Conexiones**: Cierre adecuado de conexiones IMAP
- **Validación de Entrada**: Verificación de datos antes del procesamiento
- **Escape de Caracteres**: Protección contra inyección en mensajes de Telegram

---

Si necesita ayuda adicional o desea contribuir, por favor abra un issue o un pull request en el repositorio correspondiente.
