#!/bin/bash

echo "🔧 DIAGNÓSTICO Y CORRECCIÓN COMPLETA DEL SERVIDOR"
echo "=================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con colores
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detener servicio si está corriendo
print_status "Deteniendo servicio si está activo..."
systemctl stop email-monitor.service 2>/dev/null || true

# Verificar y crear usuario si no existe
print_status "Verificando usuario emailmonitor..."
if ! id "emailmonitor" &>/dev/null; then
    print_warning "Usuario emailmonitor no existe. Creando..."
    useradd -m -s /bin/bash emailmonitor
    print_success "Usuario emailmonitor creado"
else
    print_success "Usuario emailmonitor ya existe"
fi

# Verificar directorio del proyecto
PROJECT_DIR="/home/emailmonitor/mail_notification"
print_status "Verificando directorio del proyecto: $PROJECT_DIR"

if [ ! -d "$PROJECT_DIR" ]; then
    print_warning "Directorio del proyecto no existe. Creando..."
    mkdir -p "$PROJECT_DIR"
    print_success "Directorio creado"
else
    print_success "Directorio del proyecto existe"
fi

# Verificar si hay archivos del proyecto
if [ ! -f "$PROJECT_DIR/main.py" ]; then
    print_error "Archivo main.py no encontrado. Necesitas subir el código del proyecto primero."
    print_status "Puedes clonar desde tu repositorio:"
    echo "cd /home/emailmonitor"
    echo "git clone https://github.com/snoumaz/mail_notification.git"
    exit 1
fi

# Verificar entorno virtual
print_status "Verificando entorno virtual..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    print_warning "Entorno virtual no existe. Creando..."
    cd "$PROJECT_DIR"
    python3 -m venv venv
    print_success "Entorno virtual creado"
else
    print_success "Entorno virtual ya existe"
fi

# Activar entorno virtual e instalar dependencias
print_status "Instalando dependencias..."
cd "$PROJECT_DIR"
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencias instaladas"
else
    print_warning "requirements.txt no encontrado. Instalando dependencias básicas..."
    pip install python-dotenv python-telegram-bot transformers torch schedule jinja2
    print_success "Dependencias básicas instaladas"
fi

# Verificar archivo .env
print_status "Verificando archivo .env..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    print_warning "Archivo .env no existe. Creando con configuración básica..."
    cat > "$PROJECT_DIR/.env" << 'EOF'
# MAIL configuration details
MAIL=danielarribasvelazquez@gmail.com
PASS=gyqm ylwc ublw czah
MAIL_PROVIDER=gmail
PORT_MAIL=587
SMTP_SERVER=smtp.gmail.com
IMAP_SERVER=imap.gmail.com

# Telegram configuration details
TELEGRAM_TOKEN=7911843286:AAEIO570RoCzGtp-ufI8gUOB1ZyeNdBk980
TELEGRAM_CHAT_ID=7909693129

NOTIFY_DOMAINS=sepe.es,jmgalindo.es
LABEL_CANDIDATES=Trabajo,Personal,Bancos,Logan,Piso_F_Galindo,Facturas,Urgente,Promociones,Spam,Otros

# Configuración del scheduler (opcional)
DAILY_SUMMARY_TIME=21:00
CHECK_INTERVAL=120
CLEANUP_DAYS=30
SUMMARY_EMAIL_RECIPIENT=danielarribasvelazquez@gmail.com
EOF
    print_success "Archivo .env creado"
else
    print_success "Archivo .env ya existe"
fi

# Crear directorio de logs
print_status "Creando directorio de logs..."
mkdir -p "$PROJECT_DIR/logs"
print_success "Directorio de logs creado"

# Corregir permisos
print_status "Corrigiendo permisos..."
chown -R emailmonitor:emailmonitor "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
chmod 600 "$PROJECT_DIR/.env"
chmod 755 "$PROJECT_DIR/logs"
print_success "Permisos corregidos"

# Crear archivo de servicio systemd
print_status "Creando archivo de servicio systemd..."
cat > /etc/systemd/system/email-monitor.service << 'EOF'
[Unit]
Description=Email Monitor Service
After=network.target

[Service]
Type=simple
User=emailmonitor
Group=emailmonitor
WorkingDirectory=/home/emailmonitor/mail_notification
Environment=PATH=/home/emailmonitor/mail_notification/venv/bin
ExecStart=/home/emailmonitor/mail_notification/venv/bin/python /home/emailmonitor/mail_notification/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
print_success "Archivo de servicio creado"

# Recargar systemd
print_status "Recargando systemd..."
systemctl daemon-reload
print_success "Systemd recargado"

# Habilitar servicio
print_status "Habilitando servicio..."
systemctl enable email-monitor.service
print_success "Servicio habilitado"

# Probar ejecución manual
print_status "Probando ejecución manual..."
cd "$PROJECT_DIR"
source venv/bin/activate

print_status "Probando conexión a Telegram..."
if timeout 30s python main.py test_telegram; then
    print_success "✅ Conexión a Telegram exitosa"
else
    print_error "❌ Error en conexión a Telegram"
fi

print_status "Verificando estado del scheduler..."
if timeout 10s python main.py check_scheduler; then
    print_success "✅ Scheduler funcionando"
else
    print_error "❌ Error en scheduler"
fi

# Iniciar servicio
print_status "Iniciando servicio..."
systemctl start email-monitor.service

# Esperar un momento y verificar estado
sleep 3
print_status "Verificando estado del servicio..."
if systemctl is-active --quiet email-monitor.service; then
    print_success "✅ Servicio iniciado correctamente"
else
    print_error "❌ Error iniciando servicio"
    print_status "Verificando logs..."
    journalctl -u email-monitor.service --no-pager -n 10
fi

# Mostrar estado final
echo ""
echo "📊 ESTADO FINAL DEL SISTEMA"
echo "============================"
systemctl status email-monitor.service --no-pager

echo ""
echo "📋 COMANDOS ÚTILES"
echo "=================="
echo "Ver estado del servicio: systemctl status email-monitor.service"
echo "Ver logs en tiempo real: journalctl -u email-monitor.service -f"
echo "Ver logs del archivo: tail -f /home/emailmonitor/mail_notification/logs/email_monitor.log"
echo "Reiniciar servicio: systemctl restart email-monitor.service"
echo "Detener servicio: systemctl stop email-monitor.service"
echo "Probar Telegram: cd /home/emailmonitor/mail_notification && source venv/bin/activate && python main.py test_telegram"
echo "Probar resumen: cd /home/emailmonitor/mail_notification && source venv/bin/activate && python main.py send_summary"

echo ""
print_success "🏁 Configuración completada"
