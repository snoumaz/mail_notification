import schedule
import time
import logging
import asyncio
from datetime import datetime, timedelta
from threading import Thread
from typing import Optional, Callable, Dict, Any
import os

class EmailScheduler:
    """Programador de tareas para el bot de Gmail"""
    
    def __init__(self, gmail_client, email_sender, daily_summary, telegram_notifier):
        """
        Inicializa el programador de tareas
        
        Args:
            gmail_client: Cliente Gmail API
            email_sender: Módulo de envío de correos
            daily_summary: Generador de resúmenes diarios
            telegram_notifier: Notificador de Telegram
        """
        self.gmail_client = gmail_client
        self.email_sender = email_sender
        self.daily_summary = daily_summary
        self.telegram_notifier = telegram_notifier
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.email_processor = None
        
        # Configuración desde variables de entorno
        self.daily_summary_time = os.getenv("DAILY_SUMMARY_TIME", "21:00")
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "120"))  # segundos
        self.cleanup_days = int(os.getenv("CLEANUP_DAYS", "30"))
        self.summary_email_recipient = os.getenv("SUMMARY_EMAIL_RECIPIENT")
        
        self._setup_schedules()
    
    def _setup_schedules(self):
        """Configura todas las tareas programadas"""
        try:
            # Resumen diario a la hora especificada
            schedule.every().day.at(self.daily_summary_time).do(self._run_daily_summary)
            
            # Limpieza de base de datos semanal (domingos a medianoche)
            schedule.every().sunday.at("00:00").do(self._run_cleanup)
            
            # Resumen semanal (domingos a las 22:00)
            schedule.every().sunday.at("22:00").do(self._run_weekly_summary)
            
            # Verificación de salud del sistema cada hora
            schedule.every().hour.do(self._run_health_check)
            
            self.logger.info(f"Tareas programadas configuradas:")
            self.logger.info(f"  - Resumen diario: {self.daily_summary_time}")
            self.logger.info(f"  - Procesamiento de correos: cada {self.check_interval} segundos")
            self.logger.info(f"  - Limpieza de datos: domingos 00:00")
            self.logger.info(f"  - Resumen semanal: domingos 22:00")
            
        except Exception as e:
            self.logger.error(f"Error configurando tareas programadas: {e}")
    
    def set_email_processor(self, processor: Callable):
        """
        Establece la función de procesamiento de correos
        
        Args:
            processor (callable): Función que procesa correos nuevos
        """
        self.email_processor = processor
        self.logger.info("Procesador de correos configurado")
    
    def start(self):
        """Inicia el programador de tareas"""
        if self.running:
            self.logger.warning("El programador ya está ejecutándose")
            return
        
        self.running = True
        self.logger.info("🚀 Iniciando programador de tareas...")
        
        # Iniciar hilo de procesamiento de correos
        if self.email_processor:
            email_thread = Thread(target=self._email_processing_loop, daemon=True)
            email_thread.start()
            self.logger.info(f"Procesamiento de correos iniciado (intervalo: {self.check_interval}s)")
        
        # Loop principal del scheduler
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Programador detenido por el usuario")
        finally:
            self.stop()
    
    def stop(self):
        """Detiene el programador de tareas"""
        self.running = False
        schedule.clear()
        self.logger.info("🛑 Programador de tareas detenido")
    
    def _email_processing_loop(self):
        """Loop de procesamiento de correos en hilo separado"""
        while self.running:
            try:
                if self.email_processor:
                    self.email_processor()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error en procesamiento de correos: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    def _run_daily_summary(self):
        """Ejecuta la generación y envío del resumen diario"""
        try:
            self.logger.info("📊 Iniciando generación de resumen diario...")
            
            # Generar resumen
            summary = self.daily_summary.generate_daily_summary()
            
            if summary:
                # Enviar por Telegram
                telegram_success = self._send_telegram_summary(summary)
                
                # Enviar por email si está configurado
                email_success = False
                if self.summary_email_recipient:
                    email_success = self.email_sender.send_daily_summary_email(
                        summary, self.summary_email_recipient
                    )
                
                # Marcar como enviado si al menos uno fue exitoso
                if telegram_success or email_success:
                    self.daily_summary.mark_summary_sent(summary['date'])
                    self.logger.info(f"✅ Resumen diario enviado - {summary['total_emails']} correos procesados")
                else:
                    self.logger.error("❌ Error enviando resumen diario")
            else:
                self.logger.info("ℹ️ No hay correos para el resumen diario")
                
        except Exception as e:
            self.logger.error(f"Error en resumen diario: {e}")
    
    def _run_weekly_summary(self):
        """Ejecuta la generación y envío del resumen semanal"""
        try:
            self.logger.info("📅 Iniciando generación de resumen semanal...")
            
            # Generar resumen semanal
            weekly_summary = self.daily_summary.get_weekly_summary()
            
            if weekly_summary:
                # Enviar por Telegram
                telegram_success = self._send_telegram_weekly_summary(weekly_summary)
                
                # Enviar por email si está configurado
                email_success = False
                if self.summary_email_recipient:
                    email_success = self.email_sender.send_weekly_summary_email(
                        weekly_summary, self.summary_email_recipient
                    )
                
                if telegram_success or email_success:
                    self.logger.info(f"✅ Resumen semanal enviado - {weekly_summary['total_emails']} correos")
                else:
                    self.logger.error("❌ Error enviando resumen semanal")
            else:
                self.logger.info("ℹ️ No hay datos para el resumen semanal")
                
        except Exception as e:
            self.logger.error(f"Error en resumen semanal: {e}")
    
    def _run_cleanup(self):
        """Ejecuta la limpieza de datos antiguos"""
        try:
            self.logger.info("🧹 Iniciando limpieza de datos antiguos...")
            
            success = self.daily_summary.cleanup_old_data(self.cleanup_days)
            
            if success:
                self.logger.info(f"✅ Limpieza completada - datos anteriores a {self.cleanup_days} días eliminados")
            else:
                self.logger.error("❌ Error en limpieza de datos")
                
        except Exception as e:
            self.logger.error(f"Error en limpieza de datos: {e}")
    
    def _run_health_check(self):
        """Ejecuta verificación de salud del sistema"""
        try:
            self.logger.debug("🔍 Ejecutando verificación de salud...")
            
            # Verificar conexión Gmail API
            gmail_healthy = self._check_gmail_health()
            
            # Verificar base de datos
            db_healthy = self._check_database_health()
            
            # Verificar Telegram
            telegram_healthy = self._check_telegram_health()
            
            # Log del estado general
            if gmail_healthy and db_healthy and telegram_healthy:
                self.logger.debug("✅ Sistema saludable")
            else:
                health_status = {
                    'gmail': gmail_healthy,
                    'database': db_healthy,
                    'telegram': telegram_healthy
                }
                self.logger.warning(f"⚠️ Problemas de salud detectados: {health_status}")
                
        except Exception as e:
            self.logger.error(f"Error en verificación de salud: {e}")
    
    def _check_gmail_health(self) -> bool:
        """Verifica la salud de la conexión Gmail API"""
        try:
            profile = self.gmail_client.get_profile()
            return profile is not None
        except Exception as e:
            self.logger.warning(f"Gmail API no saludable: {e}")
            return False
    
    def _check_database_health(self) -> bool:
        """Verifica la salud de la base de datos"""
        try:
            stats = self.daily_summary.get_database_stats()
            return len(stats) > 0
        except Exception as e:
            self.logger.warning(f"Base de datos no saludable: {e}")
            return False
    
    def _check_telegram_health(self) -> bool:
        """Verifica la salud de la conexión Telegram"""
        try:
            # Implementar verificación básica de Telegram
            # Por ahora, asumimos que está saludable si no hay errores
            return True
        except Exception as e:
            self.logger.warning(f"Telegram no saludable: {e}")
            return False
    
    def _send_telegram_summary(self, summary: Dict) -> bool:
        """
        Envía resumen por Telegram
        
        Args:
            summary (dict): Resumen diario
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Crear mensaje formateado para Telegram
            message = self._format_telegram_summary(summary)
            
            # Enviar usando el notificador de Telegram
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.telegram_notifier.send_daily_summary(message)
            )
            loop.close()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error enviando resumen por Telegram: {e}")
            return False
    
    def _send_telegram_weekly_summary(self, summary: Dict) -> bool:
        """
        Envía resumen semanal por Telegram
        
        Args:
            summary (dict): Resumen semanal
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Crear mensaje formateado para Telegram
            message = self._format_telegram_weekly_summary(summary)
            
            # Enviar usando el notificador de Telegram
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.telegram_notifier.send_weekly_summary(message)
            )
            loop.close()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error enviando resumen semanal por Telegram: {e}")
            return False
    
    def _format_telegram_summary(self, summary: Dict) -> str:
        """
        Formatea resumen diario para Telegram
        
        Args:
            summary (dict): Resumen diario
            
        Returns:
            str: Mensaje formateado
        """
        try:
            # Top 3 remitentes
            top_senders = list(summary.get('senders', {}).items())[:3]
            senders_text = "\n".join([
                f"  • {sender}: {count}" for sender, count in top_senders
            ])
            
            # Categorías
            classifications = summary.get('classifications', {})
            
            message = f"""📊 **Resumen Diario** - {summary.get('date', 'N/A')}

📈 **Estadísticas:**
• Total de correos: {summary.get('total_emails', 0)}
• Urgentes: {summary.get('urgent_count', 0)} ({summary.get('percentage_urgent', 0)}%)
• Importantes: {summary.get('important_count', 0)} ({summary.get('percentage_important', 0)}%)
• Hora más activa: {summary.get('most_active_hour', 'N/A')}:00

📬 **Top Remitentes:**
{senders_text}

🏷️ **Por Categorías:**
• Urgente: {classifications.get('Urgente', 0)}
• Importante: {classifications.get('Importante', 0)}
• Otros: {classifications.get('Otros', 0)}

👥 **Grupos Activos:**"""
            
            # Grupos de remitentes
            for group, count in summary.get('sender_groups', {}).items():
                if count > 0:
                    message += f"\n• {group}: {count}"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formateando resumen para Telegram: {e}")
            return f"Error generando resumen para {summary.get('date', 'N/A')}"
    
    def _format_telegram_weekly_summary(self, summary: Dict) -> str:
        """
        Formatea resumen semanal para Telegram
        
        Args:
            summary (dict): Resumen semanal
            
        Returns:
            str: Mensaje formateado
        """
        try:
            message = f"""📅 **Resumen Semanal**
{summary.get('week_start', 'N/A')} → {summary.get('week_end', 'N/A')}

📊 **Totales de la Semana:**
• Total de correos: {summary.get('total_emails', 0)}
• Urgentes: {summary.get('total_urgent', 0)}
• Importantes: {summary.get('total_important', 0)}
• Promedio diario: {summary.get('avg_daily_emails', 0)}
• Día más activo: {summary.get('busiest_day', 'N/A')}

📈 **Actividad Diaria:**"""
            
            # Desglose diario
            for day_data in summary.get('daily_breakdown', []):
                message += f"\n• {day_data['date']}: {day_data['total_emails']} correos"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error formateando resumen semanal para Telegram: {e}")
            return f"Error generando resumen semanal"
    
    def trigger_daily_summary(self):
        """Dispara manualmente la generación del resumen diario"""
        self.logger.info("Ejecutando resumen diario manualmente...")
        self._run_daily_summary()
    
    def trigger_cleanup(self):
        """Dispara manualmente la limpieza de datos"""
        self.logger.info("Ejecutando limpieza de datos manualmente...")
        self._run_cleanup()
    
    def get_schedule_info(self) -> Dict:
        """
        Obtiene información sobre las tareas programadas
        
        Returns:
            dict: Información de las tareas
        """
        try:
            jobs = schedule.jobs
            
            schedule_info = {
                'total_jobs': len(jobs),
                'daily_summary_time': self.daily_summary_time,
                'check_interval': self.check_interval,
                'cleanup_days': self.cleanup_days,
                'email_recipient': self.summary_email_recipient is not None,
                'running': self.running,
                'next_runs': []
            }
            
            # Obtener próximas ejecuciones
            for job in jobs:
                try:
                    next_run = job.next_run.strftime('%Y-%m-%d %H:%M:%S') if job.next_run else "No programado"
                    schedule_info['next_runs'].append({
                        'job': str(job.job_func.__name__),
                        'next_run': next_run
                    })
                except:
                    pass
            
            return schedule_info
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información de programación: {e}")
            return {'error': str(e)}
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del scheduler
        
        Returns:
            dict: Estadísticas del scheduler
        """
        return {
            'running': self.running,
            'daily_summary_time': self.daily_summary_time,
            'check_interval_seconds': self.check_interval,
            'cleanup_days': self.cleanup_days,
            'email_notifications_enabled': self.summary_email_recipient is not None,
            'total_scheduled_jobs': len(schedule.jobs),
            'email_processor_set': self.email_processor is not None
        }