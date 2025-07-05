#!/usr/bin/env python3
"""
Script de prueba para verificar que todos los imports funcionan correctamente
"""


def test_imports():
    """Prueba todos los imports del proyecto"""
    print("🔍 Probando imports del proyecto...")

    try:
        # Test imports principales
        print("📦 Probando imports de src.core...")
        from src.core import (
            EmailMonitor,
            EmailMessage,
            setup_logging,
            EmailMonitorLogger,
        )

        print("✅ src.core imports OK")

        # Test imports específicos
        print("📧 Probando imports de email_monitor...")
        from src.core.email_monitor import (
            EmailClassifier,
            SenderGroupManager,
            TelegramNotifier,
        )

        print("✅ email_monitor imports OK")

        # Test imports de utils
        print("🛠️ Probando imports de utils...")
        from src.utils import SetupManager

        print("✅ utils imports OK")

        # Test imports de tests
        print("🧪 Probando imports de tests...")
        import tests.test_main

        print("✅ tests imports OK")

        print("\n🎉 ¡Todos los imports funcionan correctamente!")
        return True

    except ImportError as e:
        print(f"❌ Error de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def test_basic_functionality():
    """Prueba funcionalidad básica"""
    print("\n🔧 Probando funcionalidad básica...")

    try:
        # Test EmailMessage
        from src.core import EmailMessage

        email_msg = EmailMessage(
            subject="Test",
            sender="test@example.com",
            sender_domain="example.com",
            body="Test body",
            message_id="123",
            date="2023-01-01",
        )
        print("✅ EmailMessage creation OK")

        # Test EmailClassifier
        from src.core.email_monitor import EmailClassifier

        classifier = EmailClassifier()
        print("✅ EmailClassifier creation OK")

        # Test SenderGroupManager
        from src.core.email_monitor import SenderGroupManager

        manager = SenderGroupManager()
        print("✅ SenderGroupManager creation OK")

        # Test logging
        from src.core import setup_logging, EmailMonitorLogger

        setup_logging(log_level="INFO")
        logger = EmailMonitorLogger(__name__)
        logger.info("Test log message")
        print("✅ Logging setup OK")

        print("🎉 ¡Funcionalidad básica funciona correctamente!")
        return True

    except Exception as e:
        print(f"❌ Error en funcionalidad básica: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Iniciando pruebas de imports y funcionalidad...\n")

    imports_ok = test_imports()
    functionality_ok = test_basic_functionality()

    if imports_ok and functionality_ok:
        print("\n🎉 ¡Todas las pruebas pasaron! El proyecto está listo para usar.")
        exit(0)
    else:
        print("\n❌ Algunas pruebas fallaron. Revisa los errores arriba.")
        exit(1)
