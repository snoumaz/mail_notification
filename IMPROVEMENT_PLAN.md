# Plan de Mejoras: Bot de Gmail Avanzado

## Resumen de Nuevas Funcionalidades

El objetivo es transformar el bot actual en un **sistema completo de gestión de Gmail** con las siguientes capacidades:

1. **📧 Envío Automático de Correos**
2. **🏷️ Clasificación y Etiquetado Automático**
3. **📊 Resumen Diario de Actividad**
4. **🤖 Interacción Completa con Gmail API**

## Análisis de Cambios Necesarios

### 🔄 Migración de IMAP a Gmail API

**Razones para el cambio:**
- IMAP es read-only para la mayoría de operaciones
- Gmail API permite etiquetado, envío, y gestión completa
- Mejor integración con funcionalidades avanzadas de Gmail
- Rate limiting y cuotas más predecibles

**Impacto:**
- Cambio significativo en la arquitectura de autenticación
- Necesidad de credenciales OAuth2
- Mayor complejidad pero mucho más funcional

### 📋 Funcionalidades a Implementar

#### 1. **Envío Automático de Correos**
- Respuestas automáticas basadas en clasificación IA
- Envío programado de correos
- Templates personalizables
- Confirmaciones de lectura automáticas

#### 2. **Sistema de Etiquetado Inteligente**
- Creación automática de etiquetas basadas en clasificación IA
- Aplicación de etiquetas existentes
- Organización por prioridad, remitente, y contenido
- Sincronización con grupos de remitentes

#### 3. **Resumen Diario**
- Recopilación de estadísticas diarias
- Análisis de remitentes y destinatarios
- Generación de reportes hasta las 21:00
- Envío automático del resumen vía Telegram

## Arquitectura Propuesta

### 🏗️ Componentes del Sistema

```
📦 Gmail Bot Avanzado
├── 📄 main.py                    # Orquestador principal
├── 📄 gmail_client.py            # Cliente Gmail API
├── 📄 email_classifier.py        # Clasificador IA mejorado
├── 📄 email_sender.py            # Módulo de envío
├── 📄 label_manager.py           # Gestor de etiquetas
├── 📄 daily_summary.py           # Generador de resúmenes
├── 📄 scheduler.py               # Programador de tareas
├── 📄 database.py                # Almacenamiento local
├── 📄 config.py                  # Configuración centralizada
├── 📄 requirements.txt           # Dependencias actualizadas
├── 📄 credentials.json           # Credenciales OAuth2
└── 📄 templates/                 # Templates de correos
    ├── 📄 auto_reply.html
    ├── 📄 daily_summary.html
    └── 📄 confirmation.html
```

## Implementación Detallada

### 1. 🔐 Configuración OAuth2 para Gmail API

```python
# gmail_client.py
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

class GmailClient:
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.labels',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, credentials_file='credentials.json'):
        self.credentials_file = credentials_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Autentica con Gmail API usando OAuth2"""
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
```

### 2. 📧 Módulo de Envío Automático

```python
# email_sender.py
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from jinja2 import Template

class EmailSender:
    def __init__(self, gmail_client):
        self.gmail_client = gmail_client
        self.templates_dir = "templates"
    
    def send_auto_reply(self, original_message, reply_type="acknowledgment"):
        """Envía respuesta automática basada en clasificación"""
        template_path = f"{self.templates_dir}/auto_reply.html"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        # Extraer información del mensaje original
        sender = self._extract_sender(original_message)
        subject = self._extract_subject(original_message)
        
        # Generar respuesta
        reply_content = template.render(
            sender_name=sender,
            original_subject=subject,
            reply_type=reply_type
        )
        
        # Crear mensaje de respuesta
        reply_msg = MIMEMultipart()
        reply_msg['To'] = sender
        reply_msg['Subject'] = f"Re: {subject}"
        reply_msg['In-Reply-To'] = original_message['id']
        
        reply_msg.attach(MIMEText(reply_content, 'html'))
        
        # Enviar
        raw_message = base64.urlsafe_b64encode(reply_msg.as_bytes()).decode()
        
        self.gmail_client.service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
    
    def send_daily_summary(self, summary_data, recipient):
        """Envía resumen diario vía Gmail"""
        template_path = f"{self.templates_dir}/daily_summary.html"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        summary_content = template.render(
            date=summary_data['date'],
            total_emails=summary_data['total_emails'],
            senders=summary_data['senders'],
            recipients=summary_data['recipients'],
            categories=summary_data['categories']
        )
        
        msg = MIMEMultipart()
        msg['To'] = recipient
        msg['Subject'] = f"📊 Resumen Diario de Correos - {summary_data['date']}"
        
        msg.attach(MIMEText(summary_content, 'html'))
        
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        
        self.gmail_client.service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
```

### 3. 🏷️ Gestor de Etiquetas Inteligente

```python
# label_manager.py
class LabelManager:
    def __init__(self, gmail_client):
        self.gmail_client = gmail_client
        self.existing_labels = self._get_existing_labels()
    
    def _get_existing_labels(self):
        """Obtiene etiquetas existentes"""
        results = self.gmail_client.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        return {label['name']: label['id'] for label in labels}
    
    def create_label_if_not_exists(self, label_name, color='#4285f4'):
        """Crea etiqueta si no existe"""
        if label_name not in self.existing_labels:
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show',
                'color': {
                    'backgroundColor': color,
                    'textColor': '#ffffff'
                }
            }
            
            result = self.gmail_client.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            self.existing_labels[label_name] = result['id']
            return result['id']
        
        return self.existing_labels[label_name]
    
    def apply_smart_labels(self, message_id, classification, sender_group):
        """Aplica etiquetas basadas en clasificación IA"""
        labels_to_apply = []
        
        # Etiqueta por clasificación IA
        if classification != "Otros":
            label_id = self.create_label_if_not_exists(f"IA/{classification}")
            labels_to_apply.append(label_id)
        
        # Etiqueta por grupo de remitente
        if sender_group != "Otros":
            label_id = self.create_label_if_not_exists(f"Grupos/{sender_group}")
            labels_to_apply.append(label_id)
        
        # Aplicar etiquetas
        if labels_to_apply:
            self.gmail_client.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': labels_to_apply}
            ).execute()
    
    def organize_by_priority(self, message_id, priority_level):
        """Organiza por nivel de prioridad"""
        priority_colors = {
            'Alta': '#ff0000',
            'Media': '#ffaa00',
            'Baja': '#00ff00'
        }
        
        label_name = f"Prioridad/{priority_level}"
        color = priority_colors.get(priority_level, '#4285f4')
        
        label_id = self.create_label_if_not_exists(label_name, color)
        
        self.gmail_client.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]}
        ).execute()
```

### 4. 📊 Generador de Resúmenes Diarios

```python
# daily_summary.py
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class DailySummary:
    def __init__(self, db_path="email_stats.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa base de datos para estadísticas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                classification TEXT NOT NULL,
                sender_group TEXT NOT NULL,
                message_id TEXT UNIQUE NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_email(self, sender, recipient, subject, classification, sender_group, message_id):
        """Registra un correo en las estadísticas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
            INSERT OR REPLACE INTO email_stats 
            (date, time, sender, recipient, subject, classification, sender_group, message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            now.strftime('%Y-%m-%d'),
            now.strftime('%H:%M:%S'),
            sender,
            recipient,
            subject,
            classification,
            sender_group,
            message_id
        ))
        
        conn.commit()
        conn.close()
    
    def generate_daily_summary(self, target_date=None):
        """Genera resumen diario hasta las 21:00"""
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener correos del día hasta las 21:00
        cursor.execute('''
            SELECT sender, recipient, classification, sender_group, time
            FROM email_stats
            WHERE date = ? AND time <= '21:00:00'
            ORDER BY time
        ''', (target_date,))
        
        emails = cursor.fetchall()
        conn.close()
        
        if not emails:
            return None
        
        # Analizar datos
        senders = Counter(email[0] for email in emails)
        recipients = Counter(email[1] for email in emails)
        classifications = Counter(email[2] for email in emails)
        sender_groups = Counter(email[3] for email in emails)
        
        # Análisis por horas
        hourly_activity = defaultdict(int)
        for email in emails:
            hour = email[4].split(':')[0]
            hourly_activity[hour] += 1
        
        summary = {
            'date': target_date,
            'total_emails': len(emails),
            'senders': dict(senders.most_common(10)),
            'recipients': dict(recipients.most_common(10)),
            'categories': dict(classifications),
            'sender_groups': dict(sender_groups),
            'hourly_activity': dict(hourly_activity),
            'most_active_hour': max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None
        }
        
        return summary
```

### 5. ⏰ Programador de Tareas

```python
# scheduler.py
import schedule
import time
from datetime import datetime
import asyncio
from threading import Thread

class EmailScheduler:
    def __init__(self, gmail_client, email_sender, daily_summary, telegram_notifier):
        self.gmail_client = gmail_client
        self.email_sender = email_sender
        self.daily_summary = daily_summary
        self.telegram_notifier = telegram_notifier
        self.setup_schedules()
    
    def setup_schedules(self):
        """Configura tareas programadas"""
        # Resumen diario a las 21:00
        schedule.every().day.at("21:00").do(self.send_daily_summary)
        
        # Limpieza de base de datos semanal
        schedule.every().sunday.at("00:00").do(self.cleanup_old_data)
        
        # Verificación de correos cada 2 minutos
        schedule.every(2).minutes.do(self.process_emails)
    
    def send_daily_summary(self):
        """Envía resumen diario"""
        try:
            summary = self.daily_summary.generate_daily_summary()
            
            if summary:
                # Enviar por Telegram
                asyncio.run(self.telegram_notifier.send_daily_summary(summary))
                
                # Opcional: enviar por email
                recipient = os.getenv("SUMMARY_EMAIL_RECIPIENT")
                if recipient:
                    self.email_sender.send_daily_summary(summary, recipient)
                
                print(f"[INFO] ✅ Resumen diario enviado - {summary['total_emails']} correos procesados")
            else:
                print("[INFO] No hay correos para el resumen diario")
                
        except Exception as e:
            print(f"[ERROR] Error enviando resumen diario: {e}")
    
    def cleanup_old_data(self):
        """Limpia datos antiguos de la base de datos"""
        try:
            conn = sqlite3.connect(self.daily_summary.db_path)
            cursor = conn.cursor()
            
            # Eliminar registros más antiguos de 30 días
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            cursor.execute('DELETE FROM email_stats WHERE date < ?', (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            print("[INFO] ✅ Limpieza de datos antiguos completada")
            
        except Exception as e:
            print(f"[ERROR] Error en limpieza de datos: {e}")
    
    def process_emails(self):
        """Procesa correos nuevos"""
        # Esta función reemplazará el loop principal del main.py original
        pass
    
    def run(self):
        """Ejecuta el scheduler"""
        print("[INFO] 📅 Iniciando programador de tareas...")
        
        while True:
            schedule.run_pending()
            time.sleep(1)
```

### 6. 🔄 Main.py Refactorizado

```python
# main.py (versión mejorada)
import os
import asyncio
from threading import Thread
from dotenv import load_dotenv

from gmail_client import GmailClient
from email_classifier import EmailClassifier
from email_sender import EmailSender
from label_manager import LabelManager
from daily_summary import DailySummary
from scheduler import EmailScheduler
from telegram_notifier import TelegramNotifier

load_dotenv()

class GmailBotAdvanced:
    def __init__(self):
        self.gmail_client = GmailClient()
        self.email_classifier = EmailClassifier()
        self.email_sender = EmailSender(self.gmail_client)
        self.label_manager = LabelManager(self.gmail_client)
        self.daily_summary = DailySummary()
        self.telegram_notifier = TelegramNotifier()
        self.scheduler = EmailScheduler(
            self.gmail_client,
            self.email_sender,
            self.daily_summary,
            self.telegram_notifier
        )
    
    def process_new_emails(self):
        """Procesa correos nuevos con funcionalidades avanzadas"""
        try:
            # Obtener correos no leídos
            results = self.gmail_client.service.users().messages().list(
                userId='me', 
                q='is:unread'
            ).execute()
            
            messages = results.get('messages', [])
            
            for message in messages:
                message_id = message['id']
                
                # Obtener detalles del mensaje
                msg = self.gmail_client.service.users().messages().get(
                    userId='me',
                    id=message_id
                ).execute()
                
                # Extraer información
                sender = self._extract_sender(msg)
                subject = self._extract_subject(msg)
                body = self._extract_body(msg)
                
                # Clasificar con IA
                classification = self.email_classifier.classify_email(subject, body)
                sender_group = self._get_sender_group(sender)
                
                # Aplicar etiquetas inteligentes
                self.label_manager.apply_smart_labels(message_id, classification, sender_group)
                
                # Determinar prioridad
                priority = self._determine_priority(classification, sender_group)
                if priority != 'Baja':
                    self.label_manager.organize_by_priority(message_id, priority)
                
                # Registrar en estadísticas
                self.daily_summary.record_email(
                    sender, 'me', subject, classification, sender_group, message_id
                )
                
                # Enviar notificación si es necesario
                if self._should_notify(classification, sender_group):
                    await self.telegram_notifier.notify_telegram(
                        subject, sender, body[:200], classification
                    )
                
                # Respuesta automática si es necesario
                if self._should_auto_reply(classification, sender_group):
                    self.email_sender.send_auto_reply(msg, classification.lower())
                
                print(f"[INFO] ✅ Procesado: {subject[:50]}... | {classification} | {sender_group}")
                
        except Exception as e:
            print(f"[ERROR] Error procesando correos: {e}")
    
    def run(self):
        """Ejecuta el bot avanzado"""
        print("🚀 Iniciando Gmail Bot Avanzado...")
        print("📧 Funcionalidades: Lectura, Envío, Etiquetado, Resúmenes")
        
        # Ejecutar scheduler en hilo separado
        scheduler_thread = Thread(target=self.scheduler.run, daemon=True)
        scheduler_thread.start()
        
        # Loop principal
        try:
            while True:
                asyncio.run(self.process_new_emails())
                time.sleep(120)  # Revisar cada 2 minutos
                
        except KeyboardInterrupt:
            print("\n🛑 Bot detenido por el usuario")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "setup":
            print("🔧 Configurando credenciales OAuth2...")
            client = GmailClient()
            print("✅ Configuración completada")
        elif sys.argv[1] == "test_summary":
            summary = DailySummary()
            data = summary.generate_daily_summary()
            print(f"📊 Resumen de hoy: {data}")
        else:
            print("Comandos disponibles: setup, test_summary")
    else:
        bot = GmailBotAdvanced()
        bot.run()
```

## Configuración y Dependencias

### 📋 Requirements.txt Actualizado

```txt
# requirements.txt
google-api-python-client>=2.70.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=0.8.0
google-auth>=2.15.0
python-dotenv>=1.0.0
python-telegram-bot>=20.0
transformers>=4.21.0
torch>=1.12.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
schedule>=1.2.0
jinja2>=3.1.0
sqlite3
```

### 🔐 Variables de Entorno Nuevas

```bash
# .env
# Configuración original
IMAP_SERVER=imap.gmail.com
MAIL=tu_email@gmail.com
PASS=tu_contraseña_de_aplicacion
TELEGRAM_TOKEN=tu_token_de_telegram
TELEGRAM_CHAT_ID=tu_chat_id
NOTIFY_DOMAINS=dominio1.com,dominio2.com
LABEL_CANDIDATES=Urgente,Importante,Otros

# Nuevas configuraciones
GMAIL_CREDENTIALS_FILE=credentials.json
SUMMARY_EMAIL_RECIPIENT=tu_email@gmail.com
AUTO_REPLY_ENABLED=true
DAILY_SUMMARY_TIME=21:00
DATABASE_PATH=email_stats.db
TEMPLATES_DIR=templates
LOG_LEVEL=INFO
```

## Templates HTML

### 📧 Template de Respuesta Automática

```html
<!-- templates/auto_reply.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Respuesta Automática</title>
</head>
<body>
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>🤖 Respuesta Automática</h2>
        
        <p>Hola {{ sender_name }},</p>
        
        <p>Gracias por tu correo con asunto "<strong>{{ original_subject }}</strong>".</p>
        
        {% if reply_type == "acknowledgment" %}
        <p>He recibido tu mensaje y te responderé tan pronto como sea posible.</p>
        {% elif reply_type == "urgente" %}
        <p>He detectado que tu mensaje es urgente. Te responderé con prioridad.</p>
        {% elif reply_type == "importante" %}
        <p>Tu mensaje ha sido clasificado como importante y será revisado pronto.</p>
        {% endif %}
        
        <p>Gracias por tu paciencia.</p>
        
        <hr>
        <p><small>Este es un mensaje automático generado por Gmail Bot Avanzado.</small></p>
    </div>
</body>
</html>
```

### 📊 Template de Resumen Diario

```html
<!-- templates/daily_summary.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Resumen Diario</title>
</head>
<body>
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
        <h1>📊 Resumen Diario de Correos</h1>
        <h2>{{ date }}</h2>
        
        <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>📈 Estadísticas Generales</h3>
            <ul>
                <li><strong>Total de correos procesados:</strong> {{ total_emails }}</li>
                <li><strong>Hora más activa:</strong> {{ hourly_activity.keys() | max }}:00</li>
            </ul>
        </div>
        
        <div style="display: flex; gap: 20px; margin: 20px 0;">
            <div style="flex: 1; background-color: #e3f2fd; padding: 15px; border-radius: 8px;">
                <h3>📬 Top Remitentes</h3>
                <ul>
                    {% for sender, count in senders.items() %}
                    <li>{{ sender }}: {{ count }} correos</li>
                    {% endfor %}
                </ul>
            </div>
            
            <div style="flex: 1; background-color: #f3e5f5; padding: 15px; border-radius: 8px;">
                <h3>🏷️ Por Categorías</h3>
                <ul>
                    {% for category, count in categories.items() %}
                    <li>{{ category }}: {{ count }} correos</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        
        <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>👥 Grupos de Remitentes</h3>
            <ul>
                {% for group, count in sender_groups.items() %}
                <li>{{ group }}: {{ count }} correos</li>
                {% endfor %}
            </ul>
        </div>
        
        <hr>
        <p><small>Resumen generado automáticamente por Gmail Bot Avanzado - {{ date }} 21:00</small></p>
    </div>
</body>
</html>
```

## Plan de Implementación

### 🚀 Fases de Desarrollo

#### **Fase 1: Configuración Base (1-2 días)**
1. ✅ Configurar Gmail API y OAuth2
2. ✅ Migrar de IMAP a Gmail API
3. ✅ Probar autenticación y permisos

#### **Fase 2: Funcionalidades Core (3-4 días)**
1. ✅ Implementar sistema de etiquetado
2. ✅ Desarrollar módulo de envío automático
3. ✅ Crear base de datos para estadísticas
4. ✅ Integrar clasificación mejorada

#### **Fase 3: Resúmenes y Programación (2-3 días)**
1. ✅ Implementar generador de resúmenes diarios
2. ✅ Crear scheduler para tareas programadas
3. ✅ Diseñar templates HTML
4. ✅ Configurar notificaciones Telegram mejoradas

#### **Fase 4: Testing y Optimización (1-2 días)**
1. ✅ Pruebas completas del sistema
2. ✅ Optimización de rendimiento
3. ✅ Documentación actualizada
4. ✅ Configuración Docker mejorada

### 📋 Checklist de Implementación

- [ ] Configurar credenciales OAuth2 de Gmail
- [ ] Migrar código de IMAP a Gmail API
- [ ] Implementar sistema de etiquetado automático
- [ ] Crear módulo de envío de correos
- [ ] Desarrollar base de datos SQLite
- [ ] Implementar generador de resúmenes
- [ ] Crear scheduler de tareas
- [ ] Diseñar templates HTML
- [ ] Actualizar sistema de notificaciones
- [ ] Probar todas las funcionalidades
- [ ] Actualizar documentación
- [ ] Configurar despliegue Docker

## Consideraciones Importantes

### 🔐 Seguridad
- Credenciales OAuth2 seguras
- Tokens de acceso con expiración
- Validación de permisos
- Logs sin información sensible

### 📊 Rendimiento
- Rate limiting para Gmail API
- Cache para etiquetas frecuentes
- Optimización de consultas SQL
- Procesamiento asíncrono

### 🛠️ Mantenimiento
- Rotación automática de logs
- Backup de base de datos
- Monitoreo de cuotas API
- Alertas de errores

## Tiempo Estimado Total

**⏱️ Desarrollo completo: 7-10 días**
- Configuración y migración: 2 días
- Desarrollo core: 4 días
- Testing y optimización: 2 días
- Documentación: 1 día
- Contingencia: 1 día

Este plan transformará el bot actual en un **sistema completo de gestión de Gmail** con capacidades avanzadas de automatización, clasificación inteligente, y reporting comprehensivo.