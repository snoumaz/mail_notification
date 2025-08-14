"""
Punto de entrada principal para el monitor de correos electrónicos
"""

import os
import sys
import time
import logging
import asyncio
from dotenv import load_dotenv
from src.core import EmailMonitor

# Configurar logging avanzado
from src.core import setup_logging, EmailMonitorLogger

# Configurar logging con rotación de archivos
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"), log_file="logs/email_monitor.log"
)


def load_config() -> dict:
    """Carga la configuración desde variables de entorno"""
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
        raise ValueError(
            f"Faltan las siguientes variables de entorno: {', '.join(missing_vars)}"
        )

    # Variables opcionales
    config = required_vars.copy()
    config.update(
        {
            "NOTIFY_DOMAINS": os.getenv("NOTIFY_DOMAINS", ""),
            "LABEL_CANDIDATES": os.getenv(
                "LABEL_CANDIDATES", "Urgente,Importante,Otros"
            ),
            "DAILY_SUMMARY_TIME": os.getenv("DAILY_SUMMARY_TIME", "21:00"),
        }
    )

    return config


def main():
    """Función principal del programa"""
    logger = EmailMonitorLogger(__name__)

    try:
        # Cargar configuración
        config = load_config()
        logger.success("Configuración cargada correctamente")

        # Crear monitor de emails
        monitor = EmailMonitor(config)
        logger.success("Monitor de emails inicializado")

        # Mostrar información de configuración
        notify_domains = [
            d.strip().lower()
            for d in config.get("NOTIFY_DOMAINS", "").split(",")
            if d.strip()
        ]
        logger.info(f"Monitoreando: {config['MAIL']}")
        logger.info(f"Servidor IMAP: {config['IMAP_SERVER']}")
        logger.info(f"Dominios de notificación: {notify_domains}")
        logger.info(
            f"Grupos configurados: {list(monitor.sender_groups.get_groups().keys())}"
        )
        logger.info(
            f"Resumen diario programado para las: {config.get('DAILY_SUMMARY_TIME', '21:00')}"
        )

        # Iniciar scheduler del resumen diario
        monitor.start_daily_summary_scheduler()

        # Loop principal
        logger.info("Iniciando monitor de correos... Presiona Ctrl+C para detener.")

        while True:
            monitor.check_emails()
            time.sleep(5)  # Esperar 5 segundos entre verificaciones

    except KeyboardInterrupt:
        logger.info("Monitor detenido por el usuario.")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)


def test_telegram():
    """Prueba la conexión a Telegram"""
    logger = EmailMonitorLogger(__name__)

    try:
        config = load_config()
        monitor = EmailMonitor(config)

        logger.info("Probando conexión a Telegram...")
        success = asyncio.run(monitor.test_telegram_connection())

        if success:
            logger.success("Conexión a Telegram exitosa")
        else:
            logger.error("Error en la conexión a Telegram")

    except Exception as e:
        logger.error(f"Error en prueba de Telegram: {e}")


def test_classification():
    """Prueba la clasificación de emails"""
    logger = EmailMonitorLogger(__name__)

    try:
        config = load_config()
        monitor = EmailMonitor(config)

        logger.info("Probando clasificación de emails...")

        test_cases = [
            (
                "Factura urgente - Pago vencido",
                "Su factura ha vencido. Por favor, proceda con el pago inmediatamente.",
            ),
            (
                "Reunión importante mañana",
                "Tienes una reunión importante mañana a las 10:00 AM.",
            ),
            (
                "Newsletter semanal",
                "Aquí tienes nuestro newsletter semanal con las últimas noticias.",
            ),
        ]

        for subject, body in test_cases:
            result = monitor.test_classification(subject, body)
            logger.info(f"Asunto: '{subject}' -> Clasificación: {result}")

    except Exception as e:
        logger.error(f"Error en prueba de clasificación: {e}")


def send_manual_summary():
    """Envía manualmente el resumen diario actual"""
    logger = EmailMonitorLogger(__name__)

    try:
        config = load_config()
        monitor = EmailMonitor(config)

        logger.info("Enviando resumen diario manual...")
        monitor.send_manual_daily_summary()
        logger.success("Resumen diario enviado manualmente")

    except Exception as e:
        logger.error(f"Error enviando resumen diario: {e}")


def restart_scheduler():
    """Reinicia el scheduler del resumen diario"""
    logger = EmailMonitorLogger(__name__)

    try:
        config = load_config()
        monitor = EmailMonitor(config)

        logger.info("Reiniciando scheduler del resumen diario...")
        monitor.daily_summary.restart_scheduler()
        logger.success("Scheduler reiniciado correctamente")

    except Exception as e:
        logger.error(f"Error reiniciando scheduler: {e}")


def check_scheduler_status():
    """Verifica el estado del scheduler del resumen diario"""
    logger = EmailMonitorLogger(__name__)

    try:
        config = load_config()
        monitor = EmailMonitor(config)

        logger.info("Verificando estado del scheduler...")
        status = monitor.daily_summary.get_scheduler_status()

        logger.info(f"Estado del scheduler:")
        logger.info(f"  - Tareas activas: {status.get('active_jobs', 0)}")
        logger.info(f"  - Próxima ejecución: {status.get('next_run', 'N/A')}")
        logger.info(f"  - Hora configurada: {status.get('summary_time', 'N/A')}")
        logger.info(f"  - Emails en cola: {status.get('emails_in_queue', 0)}")

    except Exception as e:
        logger.error(f"Error verificando estado del scheduler: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test_telegram":
            test_telegram()
        elif command == "test_classify":
            test_classification()
        elif command == "send_summary":
            send_manual_summary()
        elif command == "restart_scheduler":
            restart_scheduler()
        elif command == "check_scheduler":
            check_scheduler_status()
        else:
            print(f"Comando desconocido: {command}")
            print(
                "Comandos disponibles: test_telegram, test_classify, send_summary, restart_scheduler, check_scheduler"
            )
            sys.exit(1)
    else:
        main()
