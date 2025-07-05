import asyncio
import html
import logging
from typing import Dict, Optional
from telegram import Bot
from telegram.error import TelegramError
import os
import time
from datetime import datetime

class TelegramNotifier:
    """Notificador avanzado de Telegram para el bot de Gmail"""
    
    def __init__(self):
        """Inicializa el notificador de Telegram"""
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.logger = logging.getLogger(__name__)
        
        # Configuración de rate limiting
        self.last_message_time = 0
        self.min_interval = 1  # 1 segundo entre mensajes
        
        # Validar configuración
        if not self.token or not self.chat_id:
            raise ValueError("TELEGRAM_TOKEN y TELEGRAM_CHAT_ID son requeridos")
        
        self.bot = Bot(token=self.token)
        self.logger.info("Notificador de Telegram inicializado")
    
    async def notify_telegram(self, subject: str, sender: str, snippet: str, 
                             classification: str = "Otros") -> bool:
        """
        Envía notificación de correo nuevo a Telegram
        
        Args:
            subject (str): Asunto del correo
            sender (str): Remitente del correo
            snippet (str): Fragmento del contenido
            classification (str): Clasificación IA
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Rate limiting
            await self._rate_limit()
            
            # Escapar caracteres especiales
            subject_esc = html.escape(subject)
            sender_esc = html.escape(sender)
            snippet_esc = html.escape(snippet)
            classification_esc = html.escape(classification)
            
            # Obtener emoji y prioridad según clasificación
            emoji, priority_text = self._get_classification_info(classification)
            
            # Obtener grupo del remitente para información adicional
            sender_group = self._get_sender_group(sender)
            group_info = f" ({sender_group})" if sender_group != "Otros" else ""
            
            # Formatear mensaje
            mensaje = f"""{emoji} <b>Correo {priority_text}</b>

📤 <b>De:</b> <code>{sender_esc}</code>{group_info}
📋 <b>Asunto:</b> <code>{subject_esc}</code>
🏷️ <b>Clasificación:</b> {classification_esc}

📄 <b>Vista previa:</b>
<code>{snippet_esc}</code>

⏰ <i>Recibido: {datetime.now().strftime('%H:%M:%S')}</i>"""
            
            # Enviar mensaje
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=mensaje,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            self.logger.info(f"✅ Notificación enviada: {subject[:30]}...")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Error de Telegram: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error enviando notificación: {e}")
            return False
    
    async def send_daily_summary(self, summary_message: str) -> bool:
        """
        Envía resumen diario a Telegram
        
        Args:
            summary_message (str): Mensaje del resumen diario
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Rate limiting
            await self._rate_limit()
            
            # Enviar mensaje
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=summary_message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
            self.logger.info("✅ Resumen diario enviado por Telegram")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Error enviando resumen diario: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error en resumen diario: {e}")
            return False
    
    async def send_weekly_summary(self, summary_message: str) -> bool:
        """
        Envía resumen semanal a Telegram
        
        Args:
            summary_message (str): Mensaje del resumen semanal
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Rate limiting
            await self._rate_limit()
            
            # Enviar mensaje
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=summary_message,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
            self.logger.info("✅ Resumen semanal enviado por Telegram")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Error enviando resumen semanal: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error en resumen semanal: {e}")
            return False
    
    async def send_urgent_alert(self, subject: str, sender: str, 
                               reason: str = "Clasificado como urgente") -> bool:
        """
        Envía alerta urgente a Telegram
        
        Args:
            subject (str): Asunto del correo urgente
            sender (str): Remitente
            reason (str): Razón de la urgencia
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Rate limiting
            await self._rate_limit()
            
            # Escapar caracteres
            subject_esc = html.escape(subject)
            sender_esc = html.escape(sender)
            reason_esc = html.escape(reason)
            
            mensaje = f"""🚨 <b>ALERTA URGENTE</b> 🚨

⚡ <b>Correo de alta prioridad detectado</b>

📤 <b>De:</b> <code>{sender_esc}</code>
📋 <b>Asunto:</b> <code>{subject_esc}</code>
🔍 <b>Motivo:</b> {reason_esc}

⚠️ <i>Se recomienda revisión inmediata</i>
⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"""
            
            # Enviar con prioridad alta
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=mensaje,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            self.logger.info(f"🚨 Alerta urgente enviada: {subject[:30]}...")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Error enviando alerta urgente: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error en alerta urgente: {e}")
            return False
    
    async def send_system_status(self, status_info: Dict) -> bool:
        """
        Envía estado del sistema a Telegram
        
        Args:
            status_info (dict): Información del estado del sistema
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Rate limiting
            await self._rate_limit()
            
            # Formatear mensaje de estado
            status_emoji = "✅" if status_info.get('healthy', True) else "⚠️"
            status_text = "SALUDABLE" if status_info.get('healthy', True) else "CON PROBLEMAS"
            
            mensaje = f"""{status_emoji} <b>Estado del Sistema</b>

🤖 <b>Gmail Bot Avanzado</b>
📊 <b>Estado:</b> {status_text}

📈 <b>Estadísticas:</b>
• Correos procesados hoy: {status_info.get('emails_today', 0)}
• Tiempo activo: {status_info.get('uptime', 'N/A')}
• Última revisión: {status_info.get('last_check', 'N/A')}

🔧 <b>Servicios:</b>
• Gmail API: {'✅' if status_info.get('gmail_ok', True) else '❌'}
• Base de datos: {'✅' if status_info.get('db_ok', True) else '❌'}
• Telegram: {'✅' if status_info.get('telegram_ok', True) else '❌'}

⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"""
            
            # Enviar mensaje
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=mensaje,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            self.logger.info("✅ Estado del sistema enviado")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Error enviando estado del sistema: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error en estado del sistema: {e}")
            return False
    
    async def send_error_alert(self, error_message: str, component: str = "Sistema") -> bool:
        """
        Envía alerta de error a Telegram
        
        Args:
            error_message (str): Mensaje de error
            component (str): Componente que falló
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Rate limiting
            await self._rate_limit()
            
            # Escapar caracteres
            error_esc = html.escape(error_message)
            component_esc = html.escape(component)
            
            mensaje = f"""❌ <b>ERROR DEL SISTEMA</b>

🔧 <b>Componente:</b> {component_esc}
📝 <b>Error:</b> <code>{error_esc}</code>

⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>

🔄 <i>El sistema intentará recuperarse automáticamente</i>"""
            
            # Enviar mensaje
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=mensaje,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            self.logger.info(f"❌ Alerta de error enviada: {component}")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Error enviando alerta de error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error en alerta de error: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Prueba la conexión con Telegram
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            # Rate limiting
            await self._rate_limit()
            
            # Obtener información del bot
            bot_info = await self.bot.get_me()
            
            # Enviar mensaje de prueba
            test_message = f"""🧪 <b>Prueba de Conexión</b>

✅ <b>Bot:</b> {bot_info.first_name} (@{bot_info.username})
📡 <b>Conexión:</b> EXITOSA
⏰ <b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 Gmail Bot Avanzado funcionando correctamente"""
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=test_message,
                parse_mode="HTML"
            )
            
            self.logger.info("✅ Prueba de conexión Telegram exitosa")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Error en prueba de conexión: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error en test de conexión: {e}")
            return False
    
    async def _rate_limit(self):
        """Implementa rate limiting para evitar spam"""
        current_time = time.time()
        time_since_last = current_time - self.last_message_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_message_time = time.time()
    
    def _get_classification_info(self, classification: str) -> tuple:
        """
        Obtiene emoji y texto de prioridad según clasificación
        
        Args:
            classification (str): Clasificación del correo
            
        Returns:
            tuple: (emoji, texto_prioridad)
        """
        classification_map = {
            "Urgente": ("🚨", "URGENTE"),
            "Importante": ("⚠️", "IMPORTANTE"),
            "Otros": ("📧", "NUEVO")
        }
        
        return classification_map.get(classification, ("📧", "NUEVO"))
    
    def _get_sender_group(self, sender: str) -> str:
        """
        Obtiene el grupo del remitente (implementación básica)
        
        Args:
            sender (str): Dirección del remitente
            
        Returns:
            str: Grupo del remitente
        """
        # Esta función debería integrarse con el sistema de grupos
        # Por ahora, implementación básica
        try:
            from main import load_sender_groups, get_label_for_sender
            groups = load_sender_groups()
            return get_label_for_sender(sender) if groups else "Otros"
        except:
            return "Otros"
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del notificador
        
        Returns:
            dict: Estadísticas del notificador
        """
        return {
            'token_configured': bool(self.token),
            'chat_id_configured': bool(self.chat_id),
            'min_interval_seconds': self.min_interval,
            'last_message_time': self.last_message_time
        }