#!/bin/bash

echo "🔧 CORRECCIÓN DEL SERVICIO EMAIL-MONITOR"
echo "========================================"

# Detener el servicio
echo "🛑 Deteniendo servicio..."
sudo systemctl stop email-monitor.service

# Verificar y crear directorio si no existe
echo "📁 Verificando directorio..."
if [ ! -d "/home/emailmonitor" ]; then
    echo "Creando usuario emailmonitor..."
    sudo useradd -m -s /bin/bash emailmonitor
fi

# Verificar y crear entorno virtual
echo "🐍 Verificando entorno virtual..."
cd /home/emailmonitor/mail_notification
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Entorno virtual ya existe"
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Verificar archivo .env
echo "📄 Verificando archivo .env..."
if [ ! -f ".env" ]; then
    echo "❌ Archivo .env no existe. Crea el archivo .env con las credenciales correctas"
    exit 1
fi

# Corregir permisos
echo "🔐 Corrigiendo permisos..."
sudo chown -R emailmonitor:emailmonitor /home/emailmonitor/mail_notification
sudo chmod -R 755 /home/emailmonitor/mail_notification
sudo chmod 600 /home/emailmonitor/mail_notification/.env

# Crear directorio de logs
echo "📋 Creando directorio de logs..."
sudo mkdir -p /home/emailmonitor/mail_notification/logs
sudo chown emailmonitor:emailmonitor /home/emailmonitor/mail_notification/logs
sudo chmod 755 /home/emailmonitor/mail_notification/logs

# Actualizar archivo de servicio
echo "📄 Actualizando archivo de servicio..."
sudo tee /etc/systemd/system/email-monitor.service > /dev/null <<EOF
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

# Recargar systemd
echo "🔄 Recargando systemd..."
sudo systemctl daemon-reload

# Habilitar servicio
echo "✅ Habilitando servicio..."
sudo systemctl enable email-monitor.service

# Probar ejecución manual
echo "🧪 Probando ejecución manual..."
cd /home/emailmonitor/mail_notification
source venv/bin/activate
timeout 10s python main.py test_telegram

# Iniciar servicio
echo "🚀 Iniciando servicio..."
sudo systemctl start email-monitor.service

# Verificar estado
echo "📊 Estado del servicio:"
sudo systemctl status email-monitor.service --no-pager

echo ""
echo "🏁 Corrección completada"
echo "📋 Comandos útiles:"
echo "  - Ver estado: sudo systemctl status email-monitor.service"
echo "  - Ver logs: sudo journalctl -u email-monitor.service -f"
echo "  - Reiniciar: sudo systemctl restart email-monitor.service"
echo "  - Detener: sudo systemctl stop email-monitor.service"
