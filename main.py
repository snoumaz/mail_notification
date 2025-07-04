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
NOTIFY_DOMAINS_LIST = [d.strip().lower() for d in NOTIFY_DOMAINS.split(",") if d.strip()]

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
bot = Bot(token=TELEGRAM_TOKEN)

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
LABEL_CANDIDATES = os.getenv("LABEL_CANDIDATES")

def decode_mixed_header(header):
    decoded_parts = decode_header(header or "")
    return "".join(
        part.decode(enc or "utf-8", errors="ignore") if isinstance(part, bytes) else part
        for part, enc in decoded_parts
    )

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def escape_markdown(text):
    return re.sub(r"([_\*\[\]()~`>#+\-=|{}.!])", r"\\\1", text)

def get_domain(email_address):
    return email_address.lower().split("@")[1] if "@" in email_address else ""

def classify_email(subject, body, threshold=0.5):
    full_text = f"{subject}\n{body}"
    result = classifier(full_text, candidate_labels=LABEL_CANDIDATES)
    top_label = result['labels'][0]
    top_score = result['scores'][0]
    print(f"[IA] Clasificado como: {top_label} (score: {top_score:.2f})")
    return top_label if top_score >= threshold else "Otros"

async def notify_telegram(subject, sender, snippet, label="Otros"):
    bot = Bot(token=TELEGRAM_TOKEN)
    subject_esc = html.escape(subject)
    sender_esc = html.escape(sender)
    snippet_esc = html.escape(snippet)
    label_esc = html.escape(label)

    mensaje = (
        f"📩 <b>Correo importante - {label_esc}</b>\n"
        f"<b>De:</b> <code>{sender_esc}</code>\n"
        f"<b>Asunto:</b> <code>{subject_esc}</code>\n\n"
        f"<code>{snippet_esc}</code>"
    )
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, text=mensaje, parse_mode="HTML"
        )
    except Exception as e:
        print(f"[ERROR] No se pudo enviar mensaje a Telegram: {e}")

def check_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, "(UNSEEN)")
        if status != "OK":
            print("[WARN] No se pudieron buscar correos.")
            return

        email_ids = messages[0].split()

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
                                if content_type == "text/plain" and "attachment" not in content_dispo:
                                    charset = part.get_content_charset() or "utf-8"
                                    body = part.get_payload(decode=True).decode(charset, errors="ignore")
                                    break
                        else:
                            charset = msg.get_content_charset() or "utf-8"
                            body = msg.get_payload(decode=True).decode(charset, errors="ignore")

                        body = clean_text(body)

                        ia_label = classify_email(subject, body)
                        contenido_relevante = any(
                            keyword.lower() in field
                            for keyword, field in itertools.product(
                                KEYWORDS, [subject.lower(), body.lower()]
                            )
                        )

                        if (
                            ia_label != "Otros"
                            or contenido_relevante
                            or sender_domain in NOTIFY_DOMAINS_LIST
                            or ia_label == "Urgente"
                        ):
                            snippet = body[:200] + ("..." if len(body) > 200 else "")
                            asyncio.run(notify_telegram(subject, sender, snippet, ia_label))

                        print(f"Etiqueta IA: {ia_label} | Correo de: {sender} | Asunto: {subject}")
                    except Exception as e:
                        print(f"[ERROR] Fallo al procesar correo: {e}")

        mail.logout()

    except Exception as e:
        print(f"[ERROR] Error al revisar correos: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test_telegram":
        asyncio.run(notify_telegram("Prueba", "Sistema", "Mensaje de prueba.", "Test"))
    else:
        print("📬 Iniciando monitor de correos... Presiona Ctrl+C para detener.")
        try:
            while True:
                check_emails()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 Monitor detenido por el usuario.")
