#!/usr/bin/env python3
import imaplib
import email
import os
from dotenv import load_dotenv


def test_gmail():
    """Prueba simple de conexión a Gmail"""
    load_dotenv()

    email_user = os.getenv("MAIL")
    email_pass = os.getenv("PASS")

    print(f"📧 Probando Gmail...")
    print(f"Usuario: {email_user}")

    try:
        # Conectar
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        print("✅ Conexión establecida")

        # Login
        mail.login(email_user, email_pass)
        print("✅ Login exitoso")

        # Buscar correos no leídos
        mail.select("INBOX")
        status, messages = mail.search(None, "UNSEEN")

        email_ids = messages[0].split()
        print(f"📨 Correos no leídos: {len(email_ids)}")

        if len(email_ids) > 0:
            print("\n📋 Últimos correos:")
            for i, email_id in enumerate(email_ids[-2:]):  # Últimos 2
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)

                subject = email_message["subject"] or "Sin asunto"
                sender = email_message["from"] or "Desconocido"

                print(f"📧 {i+1}. De: {sender}")
                print(f"    Asunto: {subject}")
                print("-" * 30)

        mail.close()
        mail.logout()
        print("✅ Prueba completada")

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


if __name__ == "__main__":
    test_gmail()
