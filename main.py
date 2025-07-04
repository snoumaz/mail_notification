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

# Cargar variables de entorno
load_dotenv()

# Leer variables
IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL_ACCOUNT = os.getenv("MAIL")
EMAIL_PASSWORD = os.getenv("PASS")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Leer lista de dominios permitidos para notificación desde .env
NOTIFY_DOMAINS = os.getenv("NOTIFY_DOMAINS", "")
NOTIFY_DOMAINS_LIST = [
    d.strip().lower() for d in NOTIFY_DOMAINS.split(",") if d.strip()
]

# Validación de variables requeridas
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

# Palabras clave importantes
KEYWORDS = ["urgente", "problema", "factura", "fallo", "error grave"]


# Cargar grupos de remitentes desde archivo JSON
def load_sender_groups(json_path="sender_groups.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] No se pudo cargar sender_groups.json: {e}")
        return {}


SENDER_GROUPS = load_sender_groups()

# Inicializar bot de Telegram
bot = Bot(token=TELEGRAM_TOKEN)


# Función para obtener el dominio del remitente
def get_domain(email_address):
    return email_address.lower().split("@")[-1] if "@" in email_address else ""


# Función para obtener etiqueta según remitente
def get_label_for_sender(sender):
    for label, senders in SENDER_GROUPS.items():
        if sender.lower() in (s.lower() for s in senders):
            return label
    return "Otros"


# Decodificar encabezados mixtos (con emojis)
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


# Limpiar texto plano
def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


# Escape para MarkdownV2
def escape_markdown(text):
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!])", r"\\\1", text)


import asyncio
from telegram import Bot


import html


async def notify_telegram(subject, sender, snippet, label="Otros"):
    bot = Bot(token=TELEGRAM_TOKEN)
    # Escapar texto para HTML
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


# Función principal para revisar correos
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
                        subject = decode_mixed_header(msg["Subject"])
                        subject = clean_text(subject)

                        from_ = msg.get("From")
                        sender = email.utils.parseaddr(from_)[1]
                        sender_domain = get_domain(sender)
                        label = get_label_for_sender(sender)

                        # Extraer cuerpo del mensaje
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_dispo = str(part.get("Content-Disposition"))
                                if (
                                    content_type == "text/plain"
                                    and "attachment" not in content_dispo
                                ):
                                    try:
                                        charset = part.get_content_charset() or "utf-8"
                                        body = part.get_payload(decode=True).decode(
                                            charset, errors="ignore"
                                        )
                                        break
                                    except Exception as e:
                                        print(
                                            f"[WARN] Error al leer parte del cuerpo: {e}"
                                        )
                        else:
                            charset = msg.get_content_charset() or "utf-8"
                            body = msg.get_payload(decode=True).decode(
                                charset, errors="ignore"
                            )

                        body = clean_text(body)

                        # Comprobar si el contenido es relevante
                        contenido_relevante = any(
                            keyword.lower() in field
                            for keyword, field in itertools.product(
                                KEYWORDS, [subject.lower(), body.lower()]
                            )
                        )

                        if (
                            label != "Otros"
                            or contenido_relevante
                            or sender_domain in NOTIFY_DOMAINS_LIST
                        ):
                            snippet = body[:200] + ("..." if len(body) > 200 else "")
                            asyncio.run(
                                notify_telegram(subject, sender, snippet, label)
                            )

                        print(
                            f"Etiqueta: {label} | Correo de: {sender} | Asunto: {subject}"
                        )
                    except Exception as e:
                        print(f"[ERROR] Fallo al procesar correo: {e}")

        mail.logout()

    except Exception as e:
        print(f"[ERROR] Error al revisar correos: {e}")


import asyncio

# Bucle principal


async def test_send_telegram_message():
    test_message = "Mensaje de prueba desde el bot de Telegram."
    await notify_telegram("Prueba", "Sistema", test_message, "Test")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test_telegram":
        asyncio.run(test_send_telegram_message())
    else:
        print("📬 Iniciando monitor de correos... Presiona Ctrl+C para detener.")
        try:
            while True:
                check_emails()
                time.sleep(60)  # cada 60 segundos
        except KeyboardInterrupt:
            print("\n🛑 Monitor detenido por el usuario.")
