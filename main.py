import imaplib
import email
from email.header import decode_header
import email.utils
import os
from dotenv import load_dotenv
import re
import json
import time
from telegram import Bot
import itertools
import asyncio
import html
from transformers import pipeline

# Cargar variables de entorno
load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL_ACCOUNT = os.getenv("MAIL")
EMAIL_PASSWORD = os.getenv("PASS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

NOTIFY_DOMAINS = os.getenv("NOTIFY_DOMAINS", "")
NOTIFY_DOMAINS_LIST = [
    d.strip().lower() for d in NOTIFY_DOMAINS.split(",") if d.strip()
]

required_vars = {
    "IMAP_SERVER": IMAP_SERVER,
    "MAIL": EMAIL_ACCOUNT,
    "PASS": EMAIL_PASSWORD,
    "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
    "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
}
for key, value in required_vars.items():
    if not value:
        raise ValueError(f"Falta la variable de entorno: {key}")

KEYWORDS = ["urgente", "problema", "factura", "fallo", "error grave"]


def load_sender_groups(json_path="sender_groups.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] No se pudo cargar sender_groups.json: {e}")
        return {}


SENDER_GROUPS = load_sender_groups()

# Inicializar clasificador de manera lazy para evitar errores de importación
classifier = None
LABEL_CANDIDATES = os.getenv("LABEL_CANDIDATES", "Urgente,Importante,Otros")


def get_classifier():
    """Inicializa el clasificador de manera lazy"""
    global classifier
    if classifier is None:
        try:
            classifier = pipeline(
                "zero-shot-classification", model="facebook/bart-large-mnli"
            )
            print("[INFO] Clasificador de IA inicializado correctamente")
        except Exception as e:
            print(f"[WARN] No se pudo inicializar el clasificador de IA: {e}")
            print("[INFO] Continuando sin clasificación automática")
    return classifier


def classify_email(subject, body, threshold=0.5):
    """Clasifica un email usando IA o reglas básicas como fallback"""
    # Intentar usar IA
    ia_classifier = get_classifier()
    if ia_classifier is not None:
        try:
            full_text = f"{subject}\n{body}"
            result = ia_classifier(
                full_text, candidate_labels=LABEL_CANDIDATES.split(",")
            )

            # Verificar que el resultado sea válido y tenga la estructura esperada
            if not result or not isinstance(result, dict):
                print("[WARN] Error en la clasificación de email - resultado inválido")
                return classify_email_fallback(subject, body)

            labels = result.get("labels", [])
            scores = result.get("scores", [])

            if not labels or not scores:
                print(
                    "[WARN] Error en la clasificación de email - sin etiquetas o puntuaciones"
                )
                return classify_email_fallback(subject, body)

            top_label = labels[0]
            top_score = scores[0]
            print(f"[IA] Clasificado como: {top_label} (score: {top_score:.2f})")
            return str(top_label) if top_score >= threshold else "Otros"
        except Exception as e:
            print(f"[WARN] Error en clasificación IA: {e}. Usando fallback.")
            return classify_email_fallback(subject, body)
    else:
        return classify_email_fallback(subject, body)


def classify_email_fallback(subject, body):
    """Clasificación básica usando palabras clave cuando la IA no está disponible"""
    text = f"{subject} {body}".lower()

    # Palabras clave para cada categoría
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
        print("[FALLBACK] Clasificado como: Urgente")
        return "Urgente"
    elif any(keyword in text for keyword in important_keywords):
        print("[FALLBACK] Clasificado como: Importante")
        return "Importante"
    else:
        print("[FALLBACK] Clasificado como: Otros")
        return "Otros"


async def notify_telegram(subject, sender, snippet, label="Otros"):
    """Envía notificación a Telegram de manera asíncrona"""
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        subject_esc = html.escape(subject)
        sender_esc = html.escape(sender)
        snippet_esc = html.escape(snippet)
        label_esc = html.escape(str(label))

        # Obtener grupo del remitente para información adicional
        sender_group = get_label_for_sender(sender)
        group_info = f" ({sender_group})" if sender_group != "Otros" else ""

        mensaje = (
            f"📩 <b>Correo importante - {label_esc}</b>\n"
            f"<b>De:</b> <code>{sender_esc}</code>{group_info}\n"
            f"<b>Asunto:</b> <code>{subject_esc}</code>\n\n"
            f"<code>{snippet_esc}</code>"
        )

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, text=mensaje, parse_mode="HTML"
        )
        print(f"[INFO] ✅ Notificación enviada para: {subject}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar mensaje a Telegram: {e}")


def check_emails():
    """Revisa emails no leídos y envía notificaciones según criterios definidos"""
    mail = None
    try:
        print(f"[INFO] Conectando a {IMAP_SERVER}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, "(UNSEEN)")
        if status != "OK":
            print("[WARN] No se pudieron buscar correos.")
            return

        email_ids = messages[0].split()

        if not email_ids:
            print("[INFO] No hay correos nuevos.")
            return

        print(f"[INFO] Procesando {len(email_ids)} correos nuevos...")

        for e_id in email_ids:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    try:
                        msg = email.message_from_bytes(response_part[1])
                        subject = clean_text(decode_mixed_header(msg["Subject"]))
                        from_ = msg.get("From")
                        sender = email.utils.parseaddr(from_)[1]
                        sender_domain = get_domain(sender)

                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_dispo = str(part.get("Content-Disposition"))
                                if (
                                    content_type == "text/plain"
                                    and "attachment" not in content_dispo
                                ):
                                    charset = part.get_content_charset() or "utf-8"
                                    body = part.get_payload(decode=True).decode(
                                        charset, errors="ignore"
                                    )
                                    break
                        else:
                            charset = msg.get_content_charset() or "utf-8"
                            body = msg.get_payload(decode=True).decode(
                                charset, errors="ignore"
                            )

                        body = clean_text(body)

                        ia_label = classify_email(subject, body)
                        contenido_relevante = any(
                            keyword.lower() in field
                            for keyword, field in itertools.product(
                                KEYWORDS, [subject.lower(), body.lower()]
                            )
                        )

                        # Verificar si el remitente está en grupos importantes
                        sender_group = get_label_for_sender(sender)
                        sender_in_groups = sender_group != "Otros"

                        # Debug: mostrar información detallada
                        print(f"[DEBUG] Remitente: {sender}")
                        print(f"[DEBUG] Grupo del remitente: {sender_group}")
                        print(f"[DEBUG] IA Label: {ia_label}")
                        print(f"[DEBUG] Contenido relevante: {contenido_relevante}")
                        print(
                            f"[DEBUG] Dominio en lista: {sender_domain in NOTIFY_DOMAINS_LIST}"
                        )
                        print(f"[DEBUG] En grupos importantes: {sender_in_groups}")

                        if (
                            ia_label != "Otros"
                            or contenido_relevante
                            or sender_domain in NOTIFY_DOMAINS_LIST
                            or ia_label == "Urgente"
                            or sender_in_groups
                        ):
                            snippet = body[:200] + ("..." if len(body) > 200 else "")
                            print(
                                f"[INFO] ✅ ENVIANDO NOTIFICACIÓN - Motivo: {'IA' if ia_label != 'Otros' else 'Grupo' if sender_in_groups else 'Palabras clave' if contenido_relevante else 'Dominio' if sender_domain in NOTIFY_DOMAINS_LIST else 'Urgente'}"
                            )
                            asyncio.run(
                                notify_telegram(subject, sender, snippet, ia_label)
                            )
                        else:
                            print(
                                f"[INFO] ❌ NO se envía notificación - Todos los criterios son False"
                            )

                        print(
                            f"[INFO] Etiqueta: {ia_label} | Grupo: {sender_group} | De: {sender} | Asunto: {subject[:50]}..."
                        )
                    except Exception as e:
                        print(f"[ERROR] Fallo al procesar correo: {e}")

    except Exception as e:
        print(f"[ERROR] Error al revisar correos: {e}")
    finally:
        if mail:
            try:
                mail.logout()
            except:
                pass


def decode_mixed_header(header):
    decoded_parts = decode_header(header or "")
    return "".join(
        (
            part.decode(enc or "utf-8", errors="ignore")
            if isinstance(part, bytes)
            else part
        )
        for part, enc in decoded_parts
    )


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def escape_markdown(text):
    return re.sub(r"([_\*\[\]()~`>#+\-=|{}.!])", r"\\\1", text)


def get_domain(email_address):
    return email_address.lower().split("@")[1] if "@" in email_address else ""


def get_label_for_sender(sender):
    """Busca en qué grupo está un remitente"""
    for label, senders in SENDER_GROUPS.items():
        if sender in senders:
            return label
    return "Otros"


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test_telegram":
        print("[INFO] Probando conexión a Telegram...")
        asyncio.run(notify_telegram("Prueba", "Sistema", "Mensaje de prueba.", "Test"))
    elif len(sys.argv) > 1 and sys.argv[1] == "test_classify":
        print("[INFO] Probando clasificación de emails...")
        test_subject = "Factura urgente - Pago vencido"
        test_body = (
            "Su factura ha vencido. Por favor, proceda con el pago inmediatamente."
        )
        result = classify_email(test_subject, test_body)
        print(f"[TEST] Resultado de clasificación: {result}")
    else:
        print("📬 Iniciando monitor de correos... Presiona Ctrl+C para detener.")
        print(f"[INFO] Monitoreando: {EMAIL_ACCOUNT}")
        print(f"[INFO] Servidor IMAP: {IMAP_SERVER}")
        print(f"[INFO] Dominios de notificación: {NOTIFY_DOMAINS_LIST}")
        print(f"[INFO] Grupos configurados: {list(SENDER_GROUPS.keys())}")
        try:
            while True:
                check_emails()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n🛑 Monitor detenido por el usuario.")
