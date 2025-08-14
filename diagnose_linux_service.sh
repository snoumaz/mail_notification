#!/bin/bash

echo "🔧 DIAGNÓSTICO DEL SERVICIO EMAIL-MONITOR EN LINUX"
echo "=================================================="

# Verificar si el directorio existe
echo "📁 Verificando directorio del proyecto..."
if [ -d "/home/emailmonitor/mail_notification" ]; then
    echo "✅ Directorio existe: /home/emailmonitor/mail_notification"
    ls -la /home/emailmonitor/mail_notification/
else
    echo "❌ Directorio NO existe: /home/emailmonitor/mail_notification"
    exit 1
fi

echo ""
echo "🐍 Verificando entorno virtual..."
if [ -d "/home/emailmonitor/mail_notification/venv" ]; then
    echo "✅ Entorno virtual existe"
    ls -la /home/emailmonitor/mail_notification/venv/bin/
else
    echo "❌ Entorno virtual NO existe"
    echo "Creando entorno virtual..."
    cd /home/emailmonitor/mail_notification
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

echo ""
echo "📄 Verificando archivo main.py..."
if [ -f "/home/emailmonitor/mail_notification/main.py" ]; then
    echo "✅ main.py existe"
    ls -la /home/emailmonitor/mail_notification/main.py
else
    echo "❌ main.py NO existe"
    exit 1
fi

echo ""
echo "🔐 Verificando permisos..."
echo "Usuario actual: $(whoami)"
echo "Propietario del directorio: $(stat -c '%U' /home/emailmonitor/mail_notification)"
echo "Permisos del directorio: $(stat -c '%a' /home/emailmonitor/mail_notification)"

echo ""
echo "🐍 Verificando Python..."
if [ -f "/home/emailmonitor/mail_notification/venv/bin/python" ]; then
    echo "✅ Python del venv existe"
    /home/emailmonitor/mail_notification/venv/bin/python --version
else
    echo "❌ Python del venv NO existe"
    echo "Python del sistema:"
    python3 --version
fi

echo ""
echo "📄 Verificando archivo .env..."
if [ -f "/home/emailmonitor/mail_notification/.env" ]; then
    echo "✅ .env existe"
    echo "Variables de entorno:"
    grep -E "^(TELEGRAM_TOKEN|TELEGRAM_CHAT_ID|MAIL|PASS)" /home/emailmonitor/mail_notification/.env
else
    echo "❌ .env NO existe"
fi

echo ""
echo "📋 Verificando servicio systemd..."
echo "Estado del servicio:"
systemctl status email-monitor.service --no-pager

echo ""
echo "📄 Contenido del archivo de servicio:"
cat /etc/systemd/system/email-monitor.service

echo ""
echo "🧪 Probando ejecución manual..."
cd /home/emailmonitor/mail_notification
if [ -f "venv/bin/python" ]; then
    echo "Probando con venv..."
    timeout 10s venv/bin/python main.py test_telegram
else
    echo "Probando con Python del sistema..."
    timeout 10s python3 main.py test_telegram
fi

echo ""
echo "🏁 Diagnóstico completado"
