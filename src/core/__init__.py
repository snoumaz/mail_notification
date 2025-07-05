"""
Core del sistema - Funcionalidad principal del monitor de correos
"""

from .email_monitor import EmailMonitor, EmailMessage
from .logging_config import setup_logging, EmailMonitorLogger

__all__ = ["EmailMonitor", "EmailMessage", "setup_logging", "EmailMonitorLogger"]
