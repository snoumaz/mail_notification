"""
Configuración avanzada de logging para el monitor de correos
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Configura el sistema de logging con rotación de archivos

    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta del archivo de log (opcional)
        max_bytes: Tamaño máximo del archivo de log antes de rotar
        backup_count: Número de archivos de backup a mantener
    """

    # Convertir string a nivel de logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configurar formato
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configurar handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)

    # Configurar handler de archivo si se especifica
    handlers = [console_handler]

    if log_file:
        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Handler con rotación
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Configurar logging raíz
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers,
        force=True,  # Sobrescribir configuración existente
    )

    # Configurar logging específico para librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para un módulo específico

    Args:
        name: Nombre del módulo (normalmente __name__)

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


class EmailMonitorLogger:
    """Logger especializado para el monitor de emails"""

    def __init__(self, name: str):
        self.logger = get_logger(name)

    def info(self, message: str) -> None:
        """Log de información"""
        self.logger.info(f"📧 {message}")

    def warning(self, message: str) -> None:
        """Log de advertencia"""
        self.logger.warning(f"⚠️ {message}")

    def error(self, message: str) -> None:
        """Log de error"""
        self.logger.error(f"❌ {message}")

    def success(self, message: str) -> None:
        """Log de éxito"""
        self.logger.info(f"✅ {message}")

    def debug(self, message: str) -> None:
        """Log de debug"""
        self.logger.debug(f"🔍 {message}")

    def telegram_sent(self, subject: str) -> None:
        """Log específico para notificaciones de Telegram enviadas"""
        self.logger.info(f"📱 Telegram enviado: {subject}")

    def email_processed(self, subject: str, classification: str) -> None:
        """Log específico para emails procesados"""
        self.logger.info(f"📨 Email procesado: {subject} -> {classification}")

    def connection_error(self, service: str, error: str) -> None:
        """Log específico para errores de conexión"""
        self.logger.error(f"🔌 Error de conexión {service}: {error}")

    def classification_error(self, error: str) -> None:
        """Log específico para errores de clasificación"""
        self.logger.warning(f"🤖 Error de clasificación: {error}")


def log_performance(func):
    """Decorador para medir el rendimiento de funciones"""

    def wrapper(*args, **kwargs):
        import time

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        logger = get_logger(func.__module__)
        logger.info(f"⏱️ {func.__name__} ejecutado en {end_time - start_time:.2f}s")

        return result

    return wrapper


def log_exceptions(func):
    """Decorador para capturar y loggear excepciones"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = get_logger(func.__module__)
            logger.error(f"💥 Excepción en {func.__name__}: {str(e)}")
            raise

    return wrapper
