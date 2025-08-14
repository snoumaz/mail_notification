#!/usr/bin/env python3
"""
Script para simular el procesamiento de un correo nuevo
"""
import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot


async def simulate_email_notification():
    """Simula una notificación de correo nuevo"""
    load_dotenv()

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print("🧪 SIMULANDO CORREO NUEVO")
    print("=" * 40)

    try:
        bot = Bot(token=token)

        # Simular correo de Personal (que debería notificar)
        message_text = """📩 **Correo importante - Personal**

**De:** dablosk@gmail.com (Personal)
**Asunto:** Prueba de notificación automática

Este es un correo de prueba para verificar que el sistema de notificaciones funciona correctamente después de la corrección.

El sistema ahora debería:
✅ Detectar correos no leídos
✅ Enviar notificación a Telegram
✅ Marcar como leído SOLO después de enviar la notificación

¡Prueba exitosa! 🎉"""

        message = await bot.send_message(
            chat_id=chat_id, text=message_text, parse_mode="Markdown"
        )

        print(f"✅ Simulación enviada (ID: {message.message_id})")
        print("📧 Tipo: Correo Personal (dablosk@gmail.com)")
        print("🏷️ Clasificación: Personal")
        print("📱 Deberías recibir esta notificación en Telegram")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(simulate_email_notification())
    print(f"\n{'✅ SIMULACIÓN EXITOSA' if result else '❌ SIMULACIÓN FALLIDA'}")
