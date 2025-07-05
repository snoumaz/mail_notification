import sqlite3
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple
import os

class DailySummary:
    """Generador de resúmenes diarios de correos"""
    
    def __init__(self, db_path: str = "email_stats.db"):
        """
        Inicializa el gestor de resúmenes diarios
        
        Args:
            db_path (str): Ruta a la base de datos SQLite
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos para estadísticas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla principal de estadísticas de correos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    sender_domain TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    sender_group TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    message_id TEXT UNIQUE NOT NULL,
                    has_attachments BOOLEAN DEFAULT 0,
                    body_length INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla para estadísticas diarias consolidadas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    total_emails INTEGER DEFAULT 0,
                    urgent_emails INTEGER DEFAULT 0,
                    important_emails INTEGER DEFAULT 0,
                    other_emails INTEGER DEFAULT 0,
                    top_sender TEXT,
                    top_domain TEXT,
                    most_active_hour INTEGER,
                    summary_sent BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para mejorar el rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON email_stats(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_id ON email_stats(message_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sender ON email_stats(sender)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_classification ON email_stats(classification)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Base de datos inicializada correctamente")
            
        except sqlite3.Error as e:
            self.logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    def record_email(self, sender: str, recipient: str, subject: str, 
                    classification: str, sender_group: str, priority: str,
                    message_id: str, has_attachments: bool = False, 
                    body_length: int = 0) -> bool:
        """
        Registra un correo en las estadísticas
        
        Args:
            sender (str): Remitente del correo
            recipient (str): Destinatario del correo
            subject (str): Asunto del correo
            classification (str): Clasificación IA
            sender_group (str): Grupo del remitente
            priority (str): Prioridad del correo
            message_id (str): ID único del mensaje
            has_attachments (bool): Si tiene archivos adjuntos
            body_length (int): Longitud del cuerpo del mensaje
            
        Returns:
            bool: True si se registró exitosamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now()
            sender_domain = self._extract_domain(sender)
            
            cursor.execute('''
                INSERT OR REPLACE INTO email_stats 
                (date, time, sender, sender_domain, recipient, subject, 
                 classification, sender_group, priority, message_id, 
                 has_attachments, body_length)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                now.strftime('%Y-%m-%d'),
                now.strftime('%H:%M:%S'),
                sender,
                sender_domain,
                recipient,
                subject,
                classification,
                sender_group,
                priority,
                message_id,
                has_attachments,
                body_length
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Correo registrado: {sender} -> {recipient[:50]}...")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Error registrando correo: {e}")
            return False
    
    def generate_daily_summary(self, target_date: Optional[str] = None) -> Optional[Dict]:
        """
        Genera resumen diario hasta las 21:00
        
        Args:
            target_date (str): Fecha objetivo (formato YYYY-MM-DD)
            
        Returns:
            dict: Resumen diario o None si no hay datos
        """
        try:
            if target_date is None:
                target_date = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener correos del día hasta las 21:00
            cursor.execute('''
                SELECT sender, sender_domain, recipient, subject, classification, 
                       sender_group, priority, time, has_attachments, body_length
                FROM email_stats
                WHERE date = ? AND time <= '21:00:00'
                ORDER BY time
            ''', (target_date,))
            
            emails = cursor.fetchall()
            conn.close()
            
            if not emails:
                self.logger.info(f"No hay correos para generar resumen del {target_date}")
                return None
            
            # Procesar datos
            summary = self._process_email_data(emails, target_date)
            
            # Guardar estadísticas diarias consolidadas
            self._save_daily_stats(summary)
            
            self.logger.info(f"Resumen diario generado para {target_date}: {summary['total_emails']} correos")
            return summary
            
        except sqlite3.Error as e:
            self.logger.error(f"Error generando resumen diario: {e}")
            return None
    
    def _process_email_data(self, emails: List[Tuple], target_date: str) -> Dict:
        """
        Procesa los datos de correos para generar estadísticas
        
        Args:
            emails (list): Lista de tuplas con datos de correos
            target_date (str): Fecha objetivo
            
        Returns:
            dict: Estadísticas procesadas
        """
        # Contadores principales
        senders = Counter()
        domains = Counter()
        recipients = Counter()
        classifications = Counter()
        sender_groups = Counter()
        priorities = Counter()
        
        # Análisis por horas
        hourly_activity = defaultdict(int)
        
        # Estadísticas adicionales
        total_attachments = 0
        total_body_length = 0
        
        for email in emails:
            sender, domain, recipient, subject, classification, sender_group, priority, time_str, has_attachments, body_length = email
            
            # Contadores básicos
            senders[sender] += 1
            domains[domain] += 1
            recipients[recipient] += 1
            classifications[classification] += 1
            sender_groups[sender_group] += 1
            priorities[priority] += 1
            
            # Análisis por hora
            try:
                hour = int(time_str.split(':')[0])
                hourly_activity[hour] += 1
            except (ValueError, IndexError):
                pass
            
            # Estadísticas adicionales
            if has_attachments:
                total_attachments += 1
            total_body_length += body_length or 0
        
        # Calcular estadísticas derivadas
        total_emails = len(emails)
        avg_body_length = total_body_length / total_emails if total_emails > 0 else 0
        
        # Hora más activa
        most_active_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else 12
        
        # Construir resumen
        summary = {
            'date': target_date,
            'total_emails': total_emails,
            'senders': dict(senders.most_common(10)),
            'domains': dict(domains.most_common(10)),
            'recipients': dict(recipients.most_common(10)),
            'classifications': dict(classifications),
            'sender_groups': dict(sender_groups),
            'priorities': dict(priorities),
            'hourly_activity': dict(hourly_activity),
            'most_active_hour': most_active_hour,
            'total_attachments': total_attachments,
            'avg_body_length': round(avg_body_length, 1),
            'top_sender': senders.most_common(1)[0][0] if senders else "N/A",
            'top_domain': domains.most_common(1)[0][0] if domains else "N/A",
            'urgent_count': classifications.get('Urgente', 0),
            'important_count': classifications.get('Importante', 0),
            'other_count': classifications.get('Otros', 0),
            'work_emails': sender_groups.get('Trabajo', 0),
            'personal_emails': sender_groups.get('Personal', 0),
            'percentage_urgent': round((classifications.get('Urgente', 0) / total_emails) * 100, 1) if total_emails > 0 else 0,
            'percentage_important': round((classifications.get('Importante', 0) / total_emails) * 100, 1) if total_emails > 0 else 0
        }
        
        return summary
    
    def _save_daily_stats(self, summary: Dict) -> bool:
        """
        Guarda estadísticas diarias consolidadas
        
        Args:
            summary (dict): Resumen diario
            
        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO daily_stats 
                (date, total_emails, urgent_emails, important_emails, other_emails,
                 top_sender, top_domain, most_active_hour)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                summary['date'],
                summary['total_emails'],
                summary['urgent_count'],
                summary['important_count'],
                summary['other_count'],
                summary['top_sender'],
                summary['top_domain'],
                summary['most_active_hour']
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Estadísticas diarias guardadas para {summary['date']}")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Error guardando estadísticas diarias: {e}")
            return False
    
    def get_weekly_summary(self, target_date: Optional[str] = None) -> Optional[Dict]:
        """
        Genera resumen semanal
        
        Args:
            target_date (str): Fecha objetivo (se calculará la semana)
            
        Returns:
            dict: Resumen semanal
        """
        try:
            if target_date is None:
                target_date = datetime.now().strftime('%Y-%m-%d')
            
            # Calcular rango de la semana
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            start_of_week = target_dt - timedelta(days=target_dt.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT date, total_emails, urgent_emails, important_emails, other_emails,
                       top_sender, top_domain, most_active_hour
                FROM daily_stats
                WHERE date BETWEEN ? AND ?
                ORDER BY date
            ''', (start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d')))
            
            weekly_data = cursor.fetchall()
            conn.close()
            
            if not weekly_data:
                return None
            
            # Procesar datos semanales
            total_emails = sum(row[1] for row in weekly_data)
            total_urgent = sum(row[2] for row in weekly_data)
            total_important = sum(row[3] for row in weekly_data)
            total_other = sum(row[4] for row in weekly_data)
            
            daily_breakdown = []
            for row in weekly_data:
                daily_breakdown.append({
                    'date': row[0],
                    'total_emails': row[1],
                    'urgent_emails': row[2],
                    'important_emails': row[3],
                    'other_emails': row[4]
                })
            
            weekly_summary = {
                'week_start': start_of_week.strftime('%Y-%m-%d'),
                'week_end': end_of_week.strftime('%Y-%m-%d'),
                'total_emails': total_emails,
                'total_urgent': total_urgent,
                'total_important': total_important,
                'total_other': total_other,
                'daily_breakdown': daily_breakdown,
                'avg_daily_emails': round(total_emails / len(weekly_data), 1),
                'busiest_day': max(daily_breakdown, key=lambda x: x['total_emails'])['date'] if daily_breakdown else None
            }
            
            self.logger.info(f"Resumen semanal generado: {total_emails} correos en la semana")
            return weekly_summary
            
        except Exception as e:
            self.logger.error(f"Error generando resumen semanal: {e}")
            return None
    
    def get_monthly_summary(self, year: int, month: int) -> Optional[Dict]:
        """
        Genera resumen mensual
        
        Args:
            year (int): Año
            month (int): Mes
            
        Returns:
            dict: Resumen mensual
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener datos del mes
            cursor.execute('''
                SELECT date, total_emails, urgent_emails, important_emails, other_emails
                FROM daily_stats
                WHERE date LIKE ?
                ORDER BY date
            ''', (f"{year}-{month:02d}-%",))
            
            monthly_data = cursor.fetchall()
            conn.close()
            
            if not monthly_data:
                return None
            
            total_emails = sum(row[1] for row in monthly_data)
            total_urgent = sum(row[2] for row in monthly_data)
            total_important = sum(row[3] for row in monthly_data)
            total_other = sum(row[4] for row in monthly_data)
            
            monthly_summary = {
                'year': year,
                'month': month,
                'total_emails': total_emails,
                'total_urgent': total_urgent,
                'total_important': total_important,
                'total_other': total_other,
                'days_with_emails': len(monthly_data),
                'avg_daily_emails': round(total_emails / len(monthly_data), 1),
                'busiest_day': max(monthly_data, key=lambda x: x[1])[0] if monthly_data else None
            }
            
            self.logger.info(f"Resumen mensual generado para {year}-{month:02d}: {total_emails} correos")
            return monthly_summary
            
        except Exception as e:
            self.logger.error(f"Error generando resumen mensual: {e}")
            return None
    
    def mark_summary_sent(self, date: str) -> bool:
        """
        Marca un resumen como enviado
        
        Args:
            date (str): Fecha del resumen
            
        Returns:
            bool: True si se marcó exitosamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE daily_stats 
                SET summary_sent = 1 
                WHERE date = ?
            ''', (date,))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Resumen marcado como enviado para {date}")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Error marcando resumen como enviado: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> bool:
        """
        Limpia datos antiguos de la base de datos
        
        Args:
            days_to_keep (int): Días de datos a mantener
            
        Returns:
            bool: True si se limpió exitosamente
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Limpiar datos detallados
            cursor.execute('DELETE FROM email_stats WHERE date < ?', (cutoff_date,))
            detailed_deleted = cursor.rowcount
            
            # Limpiar estadísticas diarias (mantener más tiempo)
            cutoff_date_stats = (datetime.now() - timedelta(days=days_to_keep * 2)).strftime('%Y-%m-%d')
            cursor.execute('DELETE FROM daily_stats WHERE date < ?', (cutoff_date_stats,))
            stats_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Limpieza completada: {detailed_deleted} registros detallados, {stats_deleted} estadísticas diarias")
            return True
            
        except sqlite3.Error as e:
            self.logger.error(f"Error en limpieza de datos: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """
        Obtiene estadísticas de la base de datos
        
        Returns:
            dict: Estadísticas de la base de datos
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar registros
            cursor.execute('SELECT COUNT(*) FROM email_stats')
            total_emails = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM daily_stats')
            total_daily_stats = cursor.fetchone()[0]
            
            # Fechas de rango
            cursor.execute('SELECT MIN(date), MAX(date) FROM email_stats')
            date_range = cursor.fetchone()
            
            # Tamaño de archivo
            file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            conn.close()
            
            stats = {
                'total_emails': total_emails,
                'total_daily_stats': total_daily_stats,
                'date_range': {
                    'start': date_range[0],
                    'end': date_range[1]
                },
                'database_size_mb': round(file_size / (1024 * 1024), 2)
            }
            
            self.logger.info(f"Estadísticas de BD: {stats}")
            return stats
            
        except sqlite3.Error as e:
            self.logger.error(f"Error obteniendo estadísticas de BD: {e}")
            return {}
    
    def _extract_domain(self, email_address: str) -> str:
        """
        Extrae el dominio de una dirección de email
        
        Args:
            email_address (str): Dirección de email
            
        Returns:
            str: Dominio extraído
        """
        try:
            # Extraer email de formato "Nombre <email@domain.com>"
            if '<' in email_address and '>' in email_address:
                email_address = email_address.split('<')[1].split('>')[0]
            
            return email_address.split('@')[1].lower() if '@' in email_address else 'unknown'
        except:
            return 'unknown'