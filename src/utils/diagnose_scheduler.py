#!/usr/bin/env python3
"""
Script de diagnóstico para el scheduler del resumen diario
"""

import os
import sys
import time
import schedule
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core import EmailMonitor


def test_scheduler_basic():
    """Prueba básica del scheduler"""
    print("🔍 Probando funcionalidad básica del scheduler...")

    # Crear una función de prueba
    def test_function():
        print(
            f"✅ Función de prueba ejecutada a las {datetime.now().strftime('%H:%M:%S')}"
        )

    # Programar para ejecutarse en 10 segundos
    schedule.every(10).seconds.do(test_function)

    print("⏰ Programada función de prueba para ejecutarse en 10 segundos...")

    # Ejecutar por 15 segundos
    start_time = time.time()
    while time.time() - start_time < 15:
        schedule.run_pending()
        time.sleep(1)

    print("✅ Prueba básica del scheduler completada")


def test_daily_scheduler():
    """Prueba el scheduler diario"""
    print("\n🔍 Probando scheduler diario...")

    def test_daily_function():
        print(
            f"✅ Función diaria ejecutada a las {datetime.now().strftime('%H:%M:%S')}"
        )

    # Programar para ejecutarse en 1 minuto
    future_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")
    schedule.every().day.at(future_time).do(test_daily_function)

    print(f"⏰ Programada función diaria para ejecutarse a las {future_time}")

    # Ejecutar por 2 minutos
    start_time = time.time()
    while time.time() - start_time < 120:
        schedule.run_pending()
        time.sleep(10)
        print(f"⏳ Esperando... {datetime.now().strftime('%H:%M:%S')}")

    print("✅ Prueba del scheduler diario completada")


def diagnose_email_monitor():
    """Diagnostica el monitor de emails"""
    print("\n🔍 Diagnosticando monitor de emails...")

    try:
        # Cargar configuración
        load_dotenv()

        required_vars = {
            "IMAP_SERVER": os.getenv("IMAP_SERVER"),
            "MAIL": os.getenv("MAIL"),
            "PASS": os.getenv("PASS"),
            "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN"),
            "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
        }

        # Verificar variables requeridas
        missing_vars = [key for key, value in required_vars.items() if not value]
        if missing_vars:
            print(f"❌ Faltan variables de entorno: {', '.join(missing_vars)}")
            return False

        print("✅ Variables de entorno configuradas correctamente")

        # Crear monitor
        config = {
            "IMAP_SERVER": required_vars["IMAP_SERVER"],
            "MAIL": required_vars["MAIL"],
            "PASS": required_vars["PASS"],
            "TELEGRAM_TOKEN": required_vars["TELEGRAM_TOKEN"],
            "TELEGRAM_CHAT_ID": required_vars["TELEGRAM_CHAT_ID"],
            "DAILY_SUMMARY_TIME": os.getenv("DAILY_SUMMARY_TIME", "21:00"),
        }

        monitor = EmailMonitor(config)
        print("✅ Monitor de emails creado correctamente")

        # Verificar estado del scheduler
        status = monitor.daily_summary.get_scheduler_status()
        print(f"📊 Estado del scheduler:")
        print(f"  - Tareas activas: {status.get('active_jobs', 0)}")
        print(f"  - Próxima ejecución: {status.get('next_run', 'N/A')}")
        print(f"  - Hora configurada: {status.get('summary_time', 'N/A')}")
        print(f"  - Emails en cola: {status.get('emails_in_queue', 0)}")

        return True

    except Exception as e:
        print(f"❌ Error diagnosticando monitor: {e}")
        return False


def test_telegram_connection():
    """Prueba la conexión a Telegram"""
    print("\n🔍 Probando conexión a Telegram...")

    try:
        load_dotenv()
        config = {
            "IMAP_SERVER": os.getenv("IMAP_SERVER"),
            "MAIL": os.getenv("MAIL"),
            "PASS": os.getenv("PASS"),
            "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN"),
            "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
        }

        monitor = EmailMonitor(config)
        success = monitor.test_telegram_connection()

        if success:
            print("✅ Conexión a Telegram exitosa")
            return True
        else:
            print("❌ Error en la conexión a Telegram")
            return False

    except Exception as e:
        print(f"❌ Error probando Telegram: {e}")
        return False


def main():
    """Función principal de diagnóstico"""
    print("🔧 DIAGNÓSTICO DEL SCHEDULER DE RESUMEN DIARIO")
    print("=" * 50)

    # Limpiar cualquier tarea existente
    schedule.clear()

    # Ejecutar diagnósticos
    test_scheduler_basic()
    test_daily_scheduler()

    if diagnose_email_monitor():
        test_telegram_connection()

    print("\n" + "=" * 50)
    print("🏁 Diagnóstico completado")
    print("\n💡 Recomendaciones:")
    print(
        "1. Si el scheduler básico falla, verifica la instalación de la librería 'schedule'"
    )
    print("2. Si el monitor falla, verifica las variables de entorno")
    print("3. Si Telegram falla, verifica el token y chat_id")
    print("4. Para reiniciar el scheduler: python main.py restart_scheduler")
    print("5. Para verificar estado: python main.py check_scheduler")


if __name__ == "__main__":
    main()
