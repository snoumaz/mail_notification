"""
Monitor de correos electrónicos con clasificación inteligente
"""

import imaplib
import email
from email.header import decode_header
import email.utils
import os
import re
import json
import time
import asyncio
import html
import schedule
import threading
from datetime import datetime, date
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from transformers import pipeline
from telegram import Bot
import logging


@dataclass
class EmailMessage:
    """Clase para representar un mensaje de email procesado"""

    subject: str
    sender: str
    sender_domain: str
    body: str
    message_id: str
    date: str


class EmailClassifier:
    """Clasificador de emails usando IA y reglas de fallback"""

    def __init__(self, label_candidates: str = "Urgente,Importante,Otros"):
        self.label_candidates = label_candidates.split(",")
        self.classifier = None
        self.logger = logging.getLogger(__name__)

    def _get_classifier(self):
        """Inicializa el clasificador de manera lazy"""
        if self.classifier is None:
            try:
                self.classifier = pipeline(
                    "zero-shot-classification", model="facebook/bart-large-mnli"
                )
                self.logger.info("Clasificador de IA inicializado correctamente")
            except Exception as e:
                self.logger.warning(
                    f"No se pudo inicializar el clasificador de IA: {e}"
                )
                self.logger.info("Continuando sin clasificación automática")
        return self.classifier

    def classify(self, subject: str, body: str, threshold: float = 0.5) -> str:
        """Clasifica un email usando IA o reglas básicas como fallback"""
        # Intentar usar IA
        classifier = self._get_classifier()
        if classifier is not None:
            try:
                full_text = f"{subject}\n{body}"
                result = classifier(full_text, candidate_labels=self.label_candidates)

                if not result or not isinstance(result, dict):
                    self.logger.warning(
                        "Error en la clasificación de email - resultado inválido"
                    )
                    return self._classify_fallback(subject, body)

                labels = result.get("labels", [])
                scores = result.get("scores", [])

                if not labels or not scores:
                    self.logger.warning(
                        "Error en la clasificación de email - sin etiquetas o puntuaciones"
                    )
                    return self._classify_fallback(subject, body)

                top_label = labels[0]
                top_score = scores[0]
                self.logger.info(
                    f"[IA] Clasificado como: {top_label} (score: {top_score:.2f})"
                )
                return str(top_label) if top_score >= threshold else "Otros"

            except Exception as e:
                self.logger.warning(f"Error en clasificación IA: {e}. Usando fallback.")
                return self._classify_fallback(subject, body)
        else:
            return self._classify_fallback(subject, body)

    def _classify_fallback(self, subject: str, body: str) -> str:
        """Clasificación básica usando palabras clave cuando la IA no está disponible"""
        text = f"{subject} {body}".lower()

        urgent_keywords = [
            "urgente",
            "emergency",
            "critical",
            "critico",
            "inmediato",
            "importante",
        ]
        important_keywords = [
            "factura",
            "invoice",
            "payment",
            "pago",
            "vencimiento",
            "deadline",
        ]

        if any(keyword in text for keyword in urgent_keywords):
            self.logger.info("[FALLBACK] Clasificado como: Urgente")
            return "Urgente"
        elif any(keyword in text for keyword in important_keywords):
            self.logger.info("[FALLBACK] Clasificado como: Importante")
            return "Importante"
        else:
            self.logger.info("[FALLBACK] Clasificado como: Otros")
            return "Otros"


class SenderGroupManager:
    """Gestor de grupos de remitentes"""

    def __init__(self, json_path: str = "sender_groups.json"):
        self.json_path = json_path
        self.logger = logging.getLogger(__name__)
        self.groups = self._load_groups()

    def _load_groups(self) -> Dict[str, List[str]]:
        """Carga los grupos de remitentes desde JSON"""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"No se pudo cargar {self.json_path}: {e}")
            return {}

    def get_label_for_sender(self, sender: str) -> str:
        """Busca en qué grupo está un remitente"""
        for label, senders in self.groups.items():
            if sender in senders:
                return label
        return "Otros"

    def get_groups(self) -> Dict[str, List[str]]:
        """Retorna todos los grupos"""
        return self.groups.copy()


class TelegramNotifier:
    """Notificador de Telegram"""

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(token=token)
        self.logger = logging.getLogger(__name__)

    async def send_notification(
        self,
        subject: str,
        sender: str,
        snippet: str,
        label: str = "Otros",
        sender_group: str = "Otros",
    ) -> bool:
        """Envía notificación a Telegram de manera asíncrona"""
        try:
            subject_esc = html.escape(subject)
            sender_esc = html.escape(sender)
            snippet_esc = html.escape(snippet)
            label_esc = html.escape(str(label))

            group_info = f" ({sender_group})" if sender_group != "Otros" else ""

            mensaje = (
                f"📩 <b>Correo importante - {label_esc}</b>\n"
                f"<b>De:</b> <code>{sender_esc}</code>{group_info}\n"
                f"<b>Asunto:</b> <code>{subject_esc}</code>\n\n"
                f"<code>{snippet_esc}</code>"
            )

            await self.bot.send_message(
                chat_id=self.chat_id, text=mensaje, parse_mode="HTML"
            )
            self.logger.info(f"✅ Notificación enviada para: {subject}")
            return True

        except Exception as e:
            self.logger.error(f"No se pudo enviar mensaje a Telegram: {e}")
            return False

    async def send_daily_summary(self, summary_text: str) -> bool:
        """Envía el resumen diario a Telegram"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=summary_text,
                parse_mode="HTML"
            )
            self.logger.info("✅ Resumen diario enviado correctamente")
            return True
        except Exception as e:
            self.logger.error(f"No se pudo enviar resumen diario: {e}")
            return False


class DailySummaryManager:
    """Gestor de resúmenes diarios de correos"""

    def __init__(
        self, telegram_notifier: TelegramNotifier, summary_time: str = "21:00"
    ):
        self.telegram_notifier = telegram_notifier
        self.summary_time = summary_time
        self.daily_emails: List[Dict] = []
        self.logger = logging.getLogger(__name__)
        self._setup_scheduler()

    def _setup_scheduler(self):
        """Configura el scheduler para enviar resúmenes diarios"""
        try:
            schedule.every().day.at(self.summary_time).do(self._send_daily_summary)
            self.logger.info(
                f"📅 Resumen diario programado para las {self.summary_time}"
            )
        except Exception as e:
            self.logger.error(f"Error configurando scheduler: {e}")

    def add_email(self, email_data: Dict):
        """Agrega un email al registro diario"""
        self.daily_emails.append(email_data)

    def _send_daily_summary(self):
        """Envía el resumen diario de correos"""
        if not self.daily_emails:
            self.logger.info("📊 No hay correos para incluir en el resumen diario")
            return

        try:
            today = date.today().strftime("%d/%m/%Y")
            summary_text = self._generate_summary_text(today)

            # Enviar resumen de manera asíncrona
            asyncio.run(self.telegram_notifier.send_daily_summary(summary_text))

            # Limpiar la lista después de enviar
            self.daily_emails.clear()
            self.logger.info(f"📊 Resumen diario enviado para {today}")

        except Exception as e:
            self.logger.error(f"Error enviando resumen diario: {e}")

    def _generate_summary_text(self, date_str: str) -> str:
        """Genera el texto del resumen diario"""
        total_emails = len(self.daily_emails)

        # Agrupar por clasificación
        by_label = {}
        by_sender_group = {}

        for email_data in self.daily_emails:
            label = email_data.get("label", "Otros")
            sender_group = email_data.get("sender_group", "Otros")

            by_label[label] = by_label.get(label, 0) + 1
            by_sender_group[sender_group] = by_sender_group.get(sender_group, 0) + 1

        # Generar texto del resumen
        summary = f"📊 <b>Resumen Diario - {date_str}</b>\n\n"
        summary += f"📧 <b>Total de correos procesados:</b> {total_emails}\n\n"

        # Resumen por clasificación
        summary += "🏷️ <b>Por clasificación:</b>\n"
        for label, count in by_label.items():
            summary += f"  • {label}: {count}\n"

        summary += "\n👥 <b>Por grupos de remitentes:</b>\n"
        for group, count in by_sender_group.items():
            summary += f"  • {group}: {count}\n"

        # Lista de correos
        summary += f"\n📋 <b>Detalle de correos ({total_emails}):</b>\n"
        for i, email_data in enumerate(self.daily_emails, 1):
            sender = email_data.get("sender", "Desconocido")
            subject = email_data.get("subject", "Sin asunto")
            label = email_data.get("label", "Otros")
            sender_group = email_data.get("sender_group", "Otros")

            summary += f"{i}. <b>{sender}</b> ({sender_group})\n"
            summary += f"   📝 {subject}\n"
            summary += f"   🏷️ {label}\n\n"

        return summary

    def run_scheduler(self):
        """Ejecuta el scheduler en un hilo separado"""

        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Revisar cada minuto

        scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
        scheduler_thread.start()
        self.logger.info("🔄 Scheduler de resumen diario iniciado")


class EmailMonitor:
    """Monitor principal de correos electrónicos"""

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Inicializar componentes
        self.classifier = EmailClassifier(
            config.get("LABEL_CANDIDATES", "Urgente,Importante,Otros")
        )
        self.sender_groups = SenderGroupManager()
        self.telegram_notifier = TelegramNotifier(
            config["TELEGRAM_TOKEN"], config["TELEGRAM_CHAT_ID"]
        )

        # Inicializar gestor de resumen diario
        summary_time = config.get("DAILY_SUMMARY_TIME", "21:00")
        self.daily_summary = DailySummaryManager(self.telegram_notifier, summary_time)

        # Configuración
        self.notify_domains = [
            d.strip().lower()
            for d in config.get("NOTIFY_DOMAINS", "").split(",")
            if d.strip()
        ]
        self.keywords = ["urgente", "problema", "factura", "fallo", "error grave"]

    def _decode_mixed_header(self, header: str) -> str:
        """Decodifica headers de email con codificación mixta"""
        decoded_parts = decode_header(header or "")
        return "".join(
            (
                part.decode(enc or "utf-8", errors="ignore")
                if isinstance(part, bytes)
                else part
            )
            for part, enc in decoded_parts
        )

    def _clean_text(self, text: str) -> str:
        """Limpia texto eliminando espacios extra"""
        return re.sub(r"\s+", " ", text).strip()

    def _get_domain(self, email_address: str) -> str:
        """Extrae el dominio de una dirección de email"""
        return email_address.lower().split("@")[1] if "@" in email_address else ""

    def _extract_email_body(self, msg: email.message.Message) -> str:
        """Extrae el cuerpo del email manejando multipart"""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_dispo = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_dispo:
                    charset = part.get_content_charset() or "utf-8"
                    body = part.get_payload(decode=True).decode(
                        charset, errors="ignore"
                    )
                    break
        else:
            charset = msg.get_content_charset() or "utf-8"
            body = msg.get_payload(decode=True).decode(charset, errors="ignore")

        return self._clean_text(body)

    def _should_notify(self, email_msg: EmailMessage, label: str) -> bool:
        """Determina si se debe enviar notificación basándose en múltiples criterios"""
        # Verificar clasificación de IA
        if label != "Otros":
            return True

        # Verificar palabras clave
        contenido_relevante = any(
            keyword.lower() in field
            for keyword, field in [
                (kw, email_msg.subject.lower()) for kw in self.keywords
            ]
            + [(kw, email_msg.body.lower()) for kw in self.keywords]
        )
        if contenido_relevante:
            return True

        # Verificar dominio
        if email_msg.sender_domain in self.notify_domains:
            return True

        # Verificar grupo del remitente
        sender_group = self.sender_groups.get_label_for_sender(email_msg.sender)
        if sender_group != "Otros":
            return True

        return False

    def _process_email_message(
        self, msg: email.message.Message
    ) -> Optional[EmailMessage]:
        """Procesa un mensaje de email y retorna un objeto EmailMessage"""
        try:
            subject = self._clean_text(self._decode_mixed_header(msg["Subject"]))
            from_ = msg.get("From")
            sender = email.utils.parseaddr(from_)[1]
            sender_domain = self._get_domain(sender)
            body = self._extract_email_body(msg)

            return EmailMessage(
                subject=subject,
                sender=sender,
                sender_domain=sender_domain,
                body=body,
                message_id=msg.get("Message-ID", ""),
                date=msg.get("Date", ""),
            )

        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {e}")
            return None

    def check_emails(self) -> None:
        """Revisa emails no leídos y envía notificaciones según criterios definidos"""
        mail = None
        try:
            self.logger.info(f"Conectando a {self.config['IMAP_SERVER']}...")
            mail = imaplib.IMAP4_SSL(self.config["IMAP_SERVER"])
            mail.login(self.config["MAIL"], self.config["PASS"])
            mail.select("inbox")

            status, messages = mail.search(None, "(UNSEEN)")
            if status != "OK":
                self.logger.warning("No se pudieron buscar correos.")
                return

            email_ids = messages[0].split()

            if not email_ids:
                self.logger.info("No hay correos nuevos.")
                return

            self.logger.info(f"Procesando {len(email_ids)} correos nuevos...")

            for e_id in email_ids:
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        try:
                            msg = email.message_from_bytes(response_part[1])
                            email_msg = self._process_email_message(msg)

                            if email_msg is None:
                                continue

                            # Clasificar email
                            label = self.classifier.classify(
                                email_msg.subject, email_msg.body
                            )

                            # Obtener grupo del remitente
                            sender_group = self.sender_groups.get_label_for_sender(
                                email_msg.sender
                            )

                            # Debug information
                            self.logger.debug(f"Remitente: {email_msg.sender}")
                            self.logger.debug(f"Grupo del remitente: {sender_group}")
                            self.logger.debug(f"IA Label: {label}")
                            self.logger.debug(
                                f"Dominio en lista: {email_msg.sender_domain in self.notify_domains}"
                            )

                            # Verificar si debe notificar
                            if self._should_notify(email_msg, label):
                                snippet = email_msg.body[:200] + (
                                    "..." if len(email_msg.body) > 200 else ""
                                )
                                self.logger.info(
                                    f"✅ ENVIANDO NOTIFICACIÓN - Motivo: {'IA' if label != 'Otros' else 'Grupo' if sender_group != 'Otros' else 'Palabras clave' if any(kw in email_msg.subject.lower() or kw in email_msg.body.lower() for kw in self.keywords) else 'Dominio' if email_msg.sender_domain in self.notify_domains else 'Urgente'}"
                                )

                                asyncio.run(
                                    self.telegram_notifier.send_notification(
                                        email_msg.subject,
                                        email_msg.sender,
                                        snippet,
                                        label,
                                        sender_group,
                                    )
                                )
                            else:
                                self.logger.info(
                                    f"❌ NO se envía notificación - Todos los criterios son False"
                                )

                            # Registrar email en el resumen diario
                            email_data = {
                                'sender': email_msg.sender,
                                'subject': email_msg.subject,
                                'label': label,
                                'sender_group': sender_group,
                                'date': email_msg.date
                            }
                            self.daily_summary.add_email(email_data)

                            self.logger.info(
                                f"Etiqueta: {label} | Grupo: {sender_group} | De: {email_msg.sender} | Asunto: {email_msg.subject[:50]}..."
                            )

                        except Exception as e:
                            self.logger.error(f"Fallo al procesar correo: {e}")

        except Exception as e:
            self.logger.error(f"Error al revisar correos: {e}")
        finally:
            if mail:
                try:
                    mail.logout()
                except:
                    pass

    async def test_telegram_connection(self) -> bool:
        """Prueba la conexión a Telegram"""
        return await self.telegram_notifier.send_notification(
            "Prueba", "Sistema", "Mensaje de prueba.", "Test"
        )

    def test_classification(self, subject: str, body: str) -> str:
        """Prueba la clasificación de emails"""
        return self.classifier.classify(subject, body)

    def start_daily_summary_scheduler(self):
        """Inicia el scheduler del resumen diario"""
        self.daily_summary.run_scheduler()
        self.logger.info("🔄 Scheduler de resumen diario iniciado")

    def send_manual_daily_summary(self):
        """Envía manualmente el resumen diario actual"""
        self.daily_summary._send_daily_summary()
