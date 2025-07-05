import os
import logging
from typing import Dict, Optional, List
from jinja2 import Template, Environment, FileSystemLoader
from datetime import datetime
import email.utils
import re

class EmailSender:
    """Módulo para envío automático de correos"""
<<<<<<< HEAD

    def __init__(self, gmail_client, templates_dir: str = "templates"):
        """
        Inicializa el módulo de envío

=======
    
    def __init__(self, gmail_client, templates_dir: str = "templates"):
        """
        Inicializa el módulo de envío
        
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Args:
            gmail_client: Cliente Gmail API
            templates_dir (str): Directorio de templates
        """
        self.gmail_client = gmail_client
        self.templates_dir = templates_dir
        self.logger = logging.getLogger(__name__)
        self.auto_reply_enabled = os.getenv("AUTO_REPLY_ENABLED", "false").lower() == "true"
        self._setup_templates()
<<<<<<< HEAD

=======
    
>>>>>>> e005211167595a977bd48a5de5c490387319132d
    def _setup_templates(self):
        """Configura el sistema de templates"""
        try:
            if os.path.exists(self.templates_dir):
                self.env = Environment(loader=FileSystemLoader(self.templates_dir))
                self.logger.info(f"Templates cargados desde {self.templates_dir}")
            else:
                self.env = None
                self.logger.warning(f"Directorio de templates no encontrado: {self.templates_dir}")
        except Exception as e:
            self.logger.error(f"Error configurando templates: {e}")
            self.env = None
<<<<<<< HEAD

    def send_auto_reply(self, original_message: Dict, reply_type: str = "acknowledgment") -> bool:
        """
        Envía respuesta automática basada en clasificación

        Args:
            original_message (dict): Mensaje original
            reply_type (str): Tipo de respuesta

=======
    
    def send_auto_reply(self, original_message: Dict, reply_type: str = "acknowledgment") -> bool:
        """
        Envía respuesta automática basada en clasificación
        
        Args:
            original_message (dict): Mensaje original
            reply_type (str): Tipo de respuesta
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            if not self.auto_reply_enabled:
                self.logger.debug("Respuestas automáticas deshabilitadas")
                return True
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            # Extraer información del mensaje original
            sender = self._extract_sender(original_message)
            subject = self._extract_subject(original_message)
            message_id = original_message.get('id', '')
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            # Validar datos necesarios
            if not sender or not subject:
                self.logger.error("Datos insuficientes para respuesta automática")
                return False
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            # Verificar si ya se envió respuesta automática
            if self._already_replied(message_id):
                self.logger.debug(f"Ya se envió respuesta automática para el mensaje {message_id}")
                return True
<<<<<<< HEAD

            # Generar contenido de respuesta
            reply_content = self._generate_reply_content(sender, subject, reply_type)

            if not reply_content:
                self.logger.error("No se pudo generar contenido de respuesta")
                return False

            # Generar asunto de respuesta
            reply_subject = self._generate_reply_subject(subject)

=======
            
            # Generar contenido de respuesta
            reply_content = self._generate_reply_content(sender, subject, reply_type)
            
            if not reply_content:
                self.logger.error("No se pudo generar contenido de respuesta")
                return False
            
            # Generar asunto de respuesta
            reply_subject = self._generate_reply_subject(subject)
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            # Enviar respuesta
            result = self.gmail_client.send_message(
                to=sender,
                subject=reply_subject,
                body=reply_content,
                html=True,
                reply_to=message_id
            )
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            if result:
                self._record_auto_reply(message_id, sender, reply_type)
                self.logger.info(f"Respuesta automática enviada a {sender}")
                return True
            else:
                self.logger.error(f"Error enviando respuesta automática a {sender}")
                return False
<<<<<<< HEAD

        except Exception as e:
            self.logger.error(f"Error en respuesta automática: {e}")
            return False

    def send_daily_summary_email(self, summary_data: Dict, recipient: str) -> bool:
        """
        Envía resumen diario por correo electrónico

        Args:
            summary_data (dict): Datos del resumen diario
            recipient (str): Destinatario del resumen

=======
                
        except Exception as e:
            self.logger.error(f"Error en respuesta automática: {e}")
            return False
    
    def send_daily_summary_email(self, summary_data: Dict, recipient: str) -> bool:
        """
        Envía resumen diario por correo electrónico
        
        Args:
            summary_data (dict): Datos del resumen diario
            recipient (str): Destinatario del resumen
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Generar contenido del resumen
            summary_content = self._generate_summary_content(summary_data)
<<<<<<< HEAD

            if not summary_content:
                self.logger.error("No se pudo generar contenido del resumen")
                return False

            # Generar asunto
            subject = f"📊 Resumen Diario de Correos - {summary_data['date']}"

=======
            
            if not summary_content:
                self.logger.error("No se pudo generar contenido del resumen")
                return False
            
            # Generar asunto
            subject = f"📊 Resumen Diario de Correos - {summary_data['date']}"
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            # Enviar resumen
            result = self.gmail_client.send_message(
                to=recipient,
                subject=subject,
                body=summary_content,
                html=True
            )
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            if result:
                self.logger.info(f"Resumen diario enviado a {recipient}")
                return True
            else:
                self.logger.error(f"Error enviando resumen diario a {recipient}")
                return False
<<<<<<< HEAD

        except Exception as e:
            self.logger.error(f"Error enviando resumen diario: {e}")
            return False

    def send_weekly_summary_email(self, summary_data: Dict, recipient: str) -> bool:
        """
        Envía resumen semanal por correo electrónico

        Args:
            summary_data (dict): Datos del resumen semanal
            recipient (str): Destinatario del resumen

=======
                
        except Exception as e:
            self.logger.error(f"Error enviando resumen diario: {e}")
            return False
    
    def send_weekly_summary_email(self, summary_data: Dict, recipient: str) -> bool:
        """
        Envía resumen semanal por correo electrónico
        
        Args:
            summary_data (dict): Datos del resumen semanal
            recipient (str): Destinatario del resumen
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Generar contenido del resumen
            summary_content = self._generate_weekly_summary_content(summary_data)
<<<<<<< HEAD

            if not summary_content:
                self.logger.error("No se pudo generar contenido del resumen semanal")
                return False

            # Generar asunto
            subject = f"📅 Resumen Semanal de Correos - {summary_data['week_start']} a {summary_data['week_end']}"

=======
            
            if not summary_content:
                self.logger.error("No se pudo generar contenido del resumen semanal")
                return False
            
            # Generar asunto
            subject = f"📅 Resumen Semanal de Correos - {summary_data['week_start']} a {summary_data['week_end']}"
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            # Enviar resumen
            result = self.gmail_client.send_message(
                to=recipient,
                subject=subject,
                body=summary_content,
                html=True
            )
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            if result:
                self.logger.info(f"Resumen semanal enviado a {recipient}")
                return True
            else:
                self.logger.error(f"Error enviando resumen semanal a {recipient}")
                return False
<<<<<<< HEAD

        except Exception as e:
            self.logger.error(f"Error enviando resumen semanal: {e}")
            return False

    def send_urgent_notification(self, message_info: Dict, recipient: str) -> bool:
        """
        Envía notificación urgente por correo

        Args:
            message_info (dict): Información del mensaje urgente
            recipient (str): Destinatario de la notificación

=======
                
        except Exception as e:
            self.logger.error(f"Error enviando resumen semanal: {e}")
            return False
    
    def send_urgent_notification(self, message_info: Dict, recipient: str) -> bool:
        """
        Envía notificación urgente por correo
        
        Args:
            message_info (dict): Información del mensaje urgente
            recipient (str): Destinatario de la notificación
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Generar contenido de notificación
            notification_content = self._generate_urgent_notification_content(message_info)
<<<<<<< HEAD

            if not notification_content:
                self.logger.error("No se pudo generar contenido de notificación urgente")
                return False

            # Generar asunto
            subject = f"🚨 URGENTE: {message_info.get('subject', 'Correo sin asunto')}"

=======
            
            if not notification_content:
                self.logger.error("No se pudo generar contenido de notificación urgente")
                return False
            
            # Generar asunto
            subject = f"🚨 URGENTE: {message_info.get('subject', 'Correo sin asunto')}"
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            # Enviar notificación
            result = self.gmail_client.send_message(
                to=recipient,
                subject=subject,
                body=notification_content,
                html=True
            )
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            if result:
                self.logger.info(f"Notificación urgente enviada a {recipient}")
                return True
            else:
                self.logger.error(f"Error enviando notificación urgente a {recipient}")
                return False
<<<<<<< HEAD

        except Exception as e:
            self.logger.error(f"Error enviando notificación urgente: {e}")
            return False

    def _generate_reply_content(self, sender: str, subject: str, reply_type: str) -> Optional[str]:
        """
        Genera contenido de respuesta automática

=======
                
        except Exception as e:
            self.logger.error(f"Error enviando notificación urgente: {e}")
            return False
    
    def _generate_reply_content(self, sender: str, subject: str, reply_type: str) -> Optional[str]:
        """
        Genera contenido de respuesta automática
        
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Args:
            sender (str): Remitente original
            subject (str): Asunto original
            reply_type (str): Tipo de respuesta
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            str: Contenido HTML de la respuesta
        """
        try:
            # Extraer nombre del remitente
            sender_name = self._extract_sender_name(sender)
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            # Intentar usar template si está disponible
            if self.env:
                try:
                    template = self.env.get_template('auto_reply.html')
                    return template.render(
                        sender_name=sender_name,
                        original_subject=subject,
                        reply_type=reply_type,
                        current_date=datetime.now().strftime('%Y-%m-%d %H:%M')
                    )
                except Exception as e:
                    self.logger.warning(f"Error usando template: {e}")
<<<<<<< HEAD

            # Fallback: generar respuesta básica
            return self._generate_basic_reply(sender_name, subject, reply_type)

        except Exception as e:
            self.logger.error(f"Error generando contenido de respuesta: {e}")
            return None

    def _generate_basic_reply(self, sender_name: str, subject: str, reply_type: str) -> str:
        """
        Genera respuesta básica sin template

=======
            
            # Fallback: generar respuesta básica
            return self._generate_basic_reply(sender_name, subject, reply_type)
            
        except Exception as e:
            self.logger.error(f"Error generando contenido de respuesta: {e}")
            return None
    
    def _generate_basic_reply(self, sender_name: str, subject: str, reply_type: str) -> str:
        """
        Genera respuesta básica sin template
        
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Args:
            sender_name (str): Nombre del remitente
            subject (str): Asunto original
            reply_type (str): Tipo de respuesta
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            str: Contenido HTML básico
        """
        reply_messages = {
            "acknowledgment": "He recibido tu mensaje y te responderé tan pronto como sea posible.",
            "urgente": "He detectado que tu mensaje es urgente. Te responderé con prioridad.",
            "importante": "Tu mensaje ha sido clasificado como importante y será revisado pronto.",
            "fuera_horario": "Tu mensaje se ha recibido fuera del horario laboral. Te responderé el próximo día hábil."
        }
<<<<<<< HEAD

        message = reply_messages.get(reply_type, reply_messages["acknowledgment"])

=======
        
        message = reply_messages.get(reply_type, reply_messages["acknowledgment"])
        
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        return f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Respuesta Automática</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4285f4;">🤖 Respuesta Automática</h2>
<<<<<<< HEAD

            <p>Hola {sender_name},</p>

            <p>Gracias por tu correo con asunto "<strong>{subject}</strong>".</p>

            <p>{message}</p>

            <p>Gracias por tu paciencia.</p>

=======
            
            <p>Hola {sender_name},</p>
            
            <p>Gracias por tu correo con asunto "<strong>{subject}</strong>".</p>
            
            <p>{message}</p>
            
            <p>Gracias por tu paciencia.</p>
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            <hr style="margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                Este es un mensaje automático generado por Gmail Bot Avanzado - {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </p>
        </body>
        </html>
        """
<<<<<<< HEAD

    def _generate_summary_content(self, summary_data: Dict) -> Optional[str]:
        """
        Genera contenido del resumen diario

        Args:
            summary_data (dict): Datos del resumen

=======
    
    def _generate_summary_content(self, summary_data: Dict) -> Optional[str]:
        """
        Genera contenido del resumen diario
        
        Args:
            summary_data (dict): Datos del resumen
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            str: Contenido HTML del resumen
        """
        try:
            # Intentar usar template si está disponible
            if self.env:
                try:
                    template = self.env.get_template('daily_summary.html')
                    return template.render(**summary_data)
                except Exception as e:
                    self.logger.warning(f"Error usando template de resumen: {e}")
<<<<<<< HEAD

            # Fallback: generar resumen básico
            return self._generate_basic_summary(summary_data)

        except Exception as e:
            self.logger.error(f"Error generando contenido de resumen: {e}")
            return None

    def _generate_basic_summary(self, summary_data: Dict) -> str:
        """
        Genera resumen básico sin template

        Args:
            summary_data (dict): Datos del resumen

=======
            
            # Fallback: generar resumen básico
            return self._generate_basic_summary(summary_data)
            
        except Exception as e:
            self.logger.error(f"Error generando contenido de resumen: {e}")
            return None
    
    def _generate_basic_summary(self, summary_data: Dict) -> str:
        """
        Genera resumen básico sin template
        
        Args:
            summary_data (dict): Datos del resumen
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            str: Contenido HTML básico
        """
        # Generar listas HTML
        top_senders = "\n".join([
<<<<<<< HEAD
            f"<li>{sender}: {count} correos</li>"
            for sender, count in list(summary_data.get('senders', {}).items())[:5]
        ])

        categories = "\n".join([
            f"<li>{cat}: {count} correos</li>"
            for cat, count in summary_data.get('classifications', {}).items()
        ])

        groups = "\n".join([
            f"<li>{group}: {count} correos</li>"
            for group, count in summary_data.get('sender_groups', {}).items()
        ])

=======
            f"<li>{sender}: {count} correos</li>" 
            for sender, count in list(summary_data.get('senders', {}).items())[:5]
        ])
        
        categories = "\n".join([
            f"<li>{cat}: {count} correos</li>" 
            for cat, count in summary_data.get('classifications', {}).items()
        ])
        
        groups = "\n".join([
            f"<li>{group}: {count} correos</li>" 
            for group, count in summary_data.get('sender_groups', {}).items()
        ])
        
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        return f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Resumen Diario</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #4285f4;">📊 Resumen Diario de Correos</h1>
            <h2 style="color: #666;">{summary_data.get('date', 'N/A')}</h2>
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #333;">📈 Estadísticas Generales</h3>
                <ul>
                    <li><strong>Total de correos procesados:</strong> {summary_data.get('total_emails', 0)}</li>
                    <li><strong>Correos urgentes:</strong> {summary_data.get('urgent_count', 0)} ({summary_data.get('percentage_urgent', 0)}%)</li>
                    <li><strong>Correos importantes:</strong> {summary_data.get('important_count', 0)} ({summary_data.get('percentage_important', 0)}%)</li>
                    <li><strong>Hora más activa:</strong> {summary_data.get('most_active_hour', 'N/A')}:00</li>
                </ul>
            </div>
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            <div style="display: flex; gap: 20px; margin: 20px 0;">
                <div style="flex: 1; background-color: #e3f2fd; padding: 15px; border-radius: 8px;">
                    <h3 style="color: #333;">📬 Top Remitentes</h3>
                    <ul>
                        {top_senders}
                    </ul>
                </div>
<<<<<<< HEAD

=======
                
>>>>>>> e005211167595a977bd48a5de5c490387319132d
                <div style="flex: 1; background-color: #f3e5f5; padding: 15px; border-radius: 8px;">
                    <h3 style="color: #333;">🏷️ Por Categorías</h3>
                    <ul>
                        {categories}
                    </ul>
                </div>
            </div>
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #333;">👥 Grupos de Remitentes</h3>
                <ul>
                    {groups}
                </ul>
            </div>
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            <hr style="margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">
                Resumen generado automáticamente por Gmail Bot Avanzado - {summary_data.get('date', 'N/A')} 21:00
            </p>
        </body>
        </html>
        """
<<<<<<< HEAD

    def _generate_weekly_summary_content(self, summary_data: Dict) -> Optional[str]:
        """
        Genera contenido del resumen semanal

        Args:
            summary_data (dict): Datos del resumen semanal

=======
    
    def _generate_weekly_summary_content(self, summary_data: Dict) -> Optional[str]:
        """
        Genera contenido del resumen semanal
        
        Args:
            summary_data (dict): Datos del resumen semanal
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            str: Contenido HTML del resumen
        """
        try:
            # Generar breakdown diario
            daily_breakdown = ""
            for day_data in summary_data.get('daily_breakdown', []):
                daily_breakdown += f"""
                <tr>
                    <td>{day_data['date']}</td>
                    <td>{day_data['total_emails']}</td>
                    <td>{day_data['urgent_emails']}</td>
                    <td>{day_data['important_emails']}</td>
                    <td>{day_data['other_emails']}</td>
                </tr>
                """
<<<<<<< HEAD

=======
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
            return f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Resumen Semanal</title>
            </head>
            <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4285f4;">📅 Resumen Semanal de Correos</h1>
                <h2 style="color: #666;">{summary_data.get('week_start', 'N/A')} a {summary_data.get('week_end', 'N/A')}</h2>
<<<<<<< HEAD

=======
                
>>>>>>> e005211167595a977bd48a5de5c490387319132d
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #333;">📊 Resumen de la Semana</h3>
                    <ul>
                        <li><strong>Total de correos:</strong> {summary_data.get('total_emails', 0)}</li>
                        <li><strong>Correos urgentes:</strong> {summary_data.get('total_urgent', 0)}</li>
                        <li><strong>Correos importantes:</strong> {summary_data.get('total_important', 0)}</li>
                        <li><strong>Promedio diario:</strong> {summary_data.get('avg_daily_emails', 0)}</li>
                        <li><strong>Día más activo:</strong> {summary_data.get('busiest_day', 'N/A')}</li>
                    </ul>
                </div>
<<<<<<< HEAD

=======
                
>>>>>>> e005211167595a977bd48a5de5c490387319132d
                <div style="margin: 20px 0;">
                    <h3 style="color: #333;">📈 Desglose Diario</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background-color: #f0f0f0;">
                                <th style="border: 1px solid #ddd; padding: 8px;">Fecha</th>
                                <th style="border: 1px solid #ddd; padding: 8px;">Total</th>
                                <th style="border: 1px solid #ddd; padding: 8px;">Urgentes</th>
                                <th style="border: 1px solid #ddd; padding: 8px;">Importantes</th>
                                <th style="border: 1px solid #ddd; padding: 8px;">Otros</th>
                            </tr>
                        </thead>
                        <tbody>
                            {daily_breakdown}
                        </tbody>
                    </table>
                </div>
<<<<<<< HEAD

=======
                
>>>>>>> e005211167595a977bd48a5de5c490387319132d
                <hr style="margin: 20px 0;">
                <p style="font-size: 12px; color: #666;">
                    Resumen semanal generado automáticamente por Gmail Bot Avanzado - {datetime.now().strftime('%Y-%m-%d %H:%M')}
                </p>
            </body>
            </html>
            """
<<<<<<< HEAD

        except Exception as e:
            self.logger.error(f"Error generando resumen semanal: {e}")
            return None

    def _generate_urgent_notification_content(self, message_info: Dict) -> Optional[str]:
        """
        Genera contenido de notificación urgente

        Args:
            message_info (dict): Información del mensaje urgente

=======
            
        except Exception as e:
            self.logger.error(f"Error generando resumen semanal: {e}")
            return None
    
    def _generate_urgent_notification_content(self, message_info: Dict) -> Optional[str]:
        """
        Genera contenido de notificación urgente
        
        Args:
            message_info (dict): Información del mensaje urgente
            
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            str: Contenido HTML de la notificación
        """
        try:
            return f"""
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Notificación Urgente</title>
            </head>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #f44336;">🚨 CORREO URGENTE DETECTADO</h1>
<<<<<<< HEAD

=======
                
>>>>>>> e005211167595a977bd48a5de5c490387319132d
                <div style="background-color: #ffebee; padding: 20px; border-radius: 8px; border-left: 4px solid #f44336;">
                    <h3 style="color: #333;">Detalles del mensaje:</h3>
                    <ul>
                        <li><strong>De:</strong> {message_info.get('sender', 'N/A')}</li>
                        <li><strong>Asunto:</strong> {message_info.get('subject', 'N/A')}</li>
                        <li><strong>Recibido:</strong> {message_info.get('date', 'N/A')}</li>
                        <li><strong>Clasificación:</strong> {message_info.get('classification', 'N/A')}</li>
                    </ul>
                </div>
<<<<<<< HEAD

=======
                
>>>>>>> e005211167595a977bd48a5de5c490387319132d
                <div style="margin: 20px 0;">
                    <h3 style="color: #333;">Vista previa del contenido:</h3>
                    <p style="background-color: #f5f5f5; padding: 15px; border-radius: 4px; font-style: italic;">
                        {message_info.get('snippet', 'No hay vista previa disponible')[:200]}...
                    </p>
                </div>
<<<<<<< HEAD

                <p style="color: #666; font-size: 14px;">
                    Este correo ha sido clasificado como urgente por el sistema de IA.
                    Se recomienda revisar y responder lo antes posible.
                </p>

=======
                
                <p style="color: #666; font-size: 14px;">
                    Este correo ha sido clasificado como urgente por el sistema de IA. 
                    Se recomienda revisar y responder lo antes posible.
                </p>
                
>>>>>>> e005211167595a977bd48a5de5c490387319132d
                <hr style="margin: 20px 0;">
                <p style="font-size: 12px; color: #666;">
                    Notificación generada automáticamente por Gmail Bot Avanzado - {datetime.now().strftime('%Y-%m-%d %H:%M')}
                </p>
            </body>
            </html>
            """
<<<<<<< HEAD

        except Exception as e:
            self.logger.error(f"Error generando notificación urgente: {e}")
            return None

=======
            
        except Exception as e:
            self.logger.error(f"Error generando notificación urgente: {e}")
            return None
    
>>>>>>> e005211167595a977bd48a5de5c490387319132d
    def _extract_sender(self, message: Dict) -> str:
        """Extrae el remitente del mensaje"""
        try:
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
<<<<<<< HEAD

            for header in headers:
                if header['name'].lower() == 'from':
                    return header['value']

            return ""
        except:
            return ""

=======
            
            for header in headers:
                if header['name'].lower() == 'from':
                    return header['value']
            
            return ""
        except:
            return ""
    
>>>>>>> e005211167595a977bd48a5de5c490387319132d
    def _extract_subject(self, message: Dict) -> str:
        """Extrae el asunto del mensaje"""
        try:
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
<<<<<<< HEAD

            for header in headers:
                if header['name'].lower() == 'subject':
                    return header['value']

            return "Sin asunto"
        except:
            return "Sin asunto"

=======
            
            for header in headers:
                if header['name'].lower() == 'subject':
                    return header['value']
            
            return "Sin asunto"
        except:
            return "Sin asunto"
    
>>>>>>> e005211167595a977bd48a5de5c490387319132d
    def _extract_sender_name(self, sender: str) -> str:
        """Extrae el nombre del remitente"""
        try:
            # Formato: "Nombre <email@domain.com>"
            if '<' in sender:
                name_part = sender.split('<')[0].strip()
                return name_part if name_part else sender.split('<')[1].split('>')[0].split('@')[0]
            else:
                return sender.split('@')[0]
        except:
            return "Usuario"
<<<<<<< HEAD

=======
    
>>>>>>> e005211167595a977bd48a5de5c490387319132d
    def _generate_reply_subject(self, original_subject: str) -> str:
        """Genera asunto para respuesta"""
        if not original_subject.lower().startswith('re:'):
            return f"Re: {original_subject}"
        return original_subject
<<<<<<< HEAD

=======
    
>>>>>>> e005211167595a977bd48a5de5c490387319132d
    def _already_replied(self, message_id: str) -> bool:
        """Verifica si ya se envió respuesta automática"""
        # Implementar lógica para evitar respuestas duplicadas
        # Por ahora, retorna False (permitir respuestas)
        return False
<<<<<<< HEAD

=======
    
>>>>>>> e005211167595a977bd48a5de5c490387319132d
    def _record_auto_reply(self, message_id: str, recipient: str, reply_type: str):
        """Registra respuesta automática enviada"""
        # Implementar lógica para registrar respuestas enviadas
        self.logger.debug(f"Respuesta automática registrada: {message_id} -> {recipient} ({reply_type})")
<<<<<<< HEAD

    def get_sender_stats(self) -> Dict:
        """
        Obtiene estadísticas del módulo de envío

=======
    
    def get_sender_stats(self) -> Dict:
        """
        Obtiene estadísticas del módulo de envío
        
>>>>>>> e005211167595a977bd48a5de5c490387319132d
        Returns:
            dict: Estadísticas del módulo
        """
        return {
            'auto_reply_enabled': self.auto_reply_enabled,
            'templates_available': self.env is not None,
            'templates_dir': self.templates_dir
<<<<<<< HEAD
        }
=======
        }
>>>>>>> e005211167595a977bd48a5de5c490387319132d
