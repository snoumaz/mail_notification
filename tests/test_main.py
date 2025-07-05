"""
Tests para el monitor de correos electrónicos
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import email
import json
import tempfile
import os

from src.core import EmailMonitor, EmailMessage
from src.core.email_monitor import EmailClassifier, SenderGroupManager, TelegramNotifier


# Test EmailClassifier
class TestEmailClassifier:
    def test_classifier_initialization(self):
        """Test de inicialización del clasificador"""
        classifier = EmailClassifier("Urgente,Importante,Otros")
        assert classifier.label_candidates == ["Urgente", "Importante", "Otros"]
        assert classifier.classifier is None

    @patch("src.core.email_monitor.pipeline")
    def test_classifier_lazy_loading(self, mock_pipeline):
        """Test de carga lazy del clasificador"""
        mock_classifier = MagicMock()
        mock_pipeline.return_value = mock_classifier
        mock_classifier.return_value = {"labels": ["Urgente"], "scores": [0.8]}

        classifier = EmailClassifier()
        result = classifier.classify("Test subject", "Test body")

        assert mock_pipeline.called
        assert result == "Urgente"

    def test_fallback_classification(self):
        """Test de clasificación de fallback"""
        classifier = EmailClassifier()

        # Test urgente
        result = classifier._classify_fallback(
            "URGENTE: Problema crítico", "Necesitamos ayuda inmediata"
        )
        assert result == "Urgente"

        # Test importante
        result = classifier._classify_fallback(
            "Factura pendiente", "Su factura está por vencer"
        )
        assert result == "Importante"

        # Test otros
        result = classifier._classify_fallback("Newsletter", "Aquí tienes las noticias")
        assert result == "Otros"


# Test SenderGroupManager
class TestSenderGroupManager:
    def test_load_groups_success(self):
        """Test de carga exitosa de grupos"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {"Trabajo": ["cliente@empresa.com"], "Familia": ["mama@gmail.com"]}, f
            )
            temp_file = f.name

        try:
            manager = SenderGroupManager(temp_file)
            groups = manager.get_groups()

            assert "Trabajo" in groups
            assert "Familia" in groups
            assert groups["Trabajo"] == ["cliente@empresa.com"]
        finally:
            os.unlink(temp_file)

    def test_load_groups_file_not_found(self):
        """Test de carga cuando el archivo no existe"""
        manager = SenderGroupManager("nonexistent.json")
        groups = manager.get_groups()
        assert groups == {}

    def test_get_label_for_sender(self):
        """Test de obtención de etiqueta para remitente"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {"Trabajo": ["cliente@empresa.com"], "Familia": ["mama@gmail.com"]}, f
            )
            temp_file = f.name

        try:
            manager = SenderGroupManager(temp_file)

            # Sender conocido
            label = manager.get_label_for_sender("cliente@empresa.com")
            assert label == "Trabajo"

            # Sender desconocido
            label = manager.get_label_for_sender("unknown@example.com")
            assert label == "Otros"
        finally:
            os.unlink(temp_file)


# Test TelegramNotifier
class TestTelegramNotifier:
    @patch("src.core.email_monitor.Bot")
    @pytest.mark.asyncio
    async def test_send_notification_success(self, mock_bot_class):
        """Test de envío exitoso de notificación"""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier("test_token", "12345")

        success = await notifier.send_notification(
            "Test Subject", "test@example.com", "Test snippet", "Urgente", "Trabajo"
        )

        assert success
        assert mock_bot.send_message.called

        args, kwargs = mock_bot.send_message.call_args
        assert kwargs["chat_id"] == "12345"
        assert "Test Subject" in kwargs["text"]
        assert "test@example.com" in kwargs["text"]
        assert "Urgente" in kwargs["text"]
        assert "Trabajo" in kwargs["text"]

    @patch('src.core.email_monitor.Bot')
    @pytest.mark.asyncio
    async def test_send_notification_failure(self, mock_bot_class):
        """Test de fallo en envío de notificación"""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock(side_effect=Exception("Network error"))
        mock_bot_class.return_value = mock_bot

        notifier = TelegramNotifier("test_token", "12345")

        success = await notifier.send_notification(
            "Test Subject", "test@example.com", "Test snippet"
        )

        assert not success


# Test EmailMonitor
class TestEmailMonitor:
    def test_monitor_initialization(self):
        """Test de inicialización del monitor"""
        config = {
            "IMAP_SERVER": "imap.gmail.com",
            "MAIL": "test@gmail.com",
            "PASS": "password",
            "TELEGRAM_TOKEN": "token",
            "TELEGRAM_CHAT_ID": "12345",
            "NOTIFY_DOMAINS": "gmail.com,hotmail.com",
            "LABEL_CANDIDATES": "Urgente,Importante,Otros",
        }

        monitor = EmailMonitor(config)

        assert monitor.config == config
        assert monitor.notify_domains == ["gmail.com", "hotmail.com"]
        assert isinstance(monitor.classifier, EmailClassifier)
        assert isinstance(monitor.sender_groups, SenderGroupManager)
        assert isinstance(monitor.telegram_notifier, TelegramNotifier)

    def test_clean_text(self):
        """Test de limpieza de texto"""
        config = {
            "IMAP_SERVER": "test",
            "MAIL": "test",
            "PASS": "test",
            "TELEGRAM_TOKEN": "test",
            "TELEGRAM_CHAT_ID": "test",
        }
        monitor = EmailMonitor(config)

        text = "  This is   a test\n\n"
        cleaned = monitor._clean_text(text)
        assert cleaned == "This is a test"

    def test_get_domain(self):
        """Test de extracción de dominio"""
        config = {
            "IMAP_SERVER": "test",
            "MAIL": "test",
            "PASS": "test",
            "TELEGRAM_TOKEN": "test",
            "TELEGRAM_CHAT_ID": "test",
        }
        monitor = EmailMonitor(config)

        domain = monitor._get_domain("test@gmail.com")
        assert domain == "gmail.com"

        domain = monitor._get_domain("invalid-email")
        assert domain == ""

    def test_should_notify(self):
        """Test de lógica de notificación"""
        config = {
            "IMAP_SERVER": "test",
            "MAIL": "test",
            "PASS": "test",
            "TELEGRAM_TOKEN": "test",
            "TELEGRAM_CHAT_ID": "test",
            "NOTIFY_DOMAINS": "gmail.com",
        }
        monitor = EmailMonitor(config)

        email_msg = EmailMessage(
            subject="Test",
            sender="test@gmail.com",
            sender_domain="gmail.com",
            body="Test body",
            message_id="123",
            date="2023-01-01",
        )

        # Test con etiqueta urgente
        should_notify = monitor._should_notify(email_msg, "Urgente")
        assert should_notify

        # Test con dominio en lista
        should_notify = monitor._should_notify(email_msg, "Otros")
        assert should_notify

        # Test sin criterios
        email_msg.sender_domain = "other.com"
        should_notify = monitor._should_notify(email_msg, "Otros")
        assert not should_notify

    @patch("src.core.email_monitor.imaplib.IMAP4_SSL")
    def test_check_emails_no_new_messages(self, mock_imap):
        """Test de verificación de emails sin mensajes nuevos"""
        config = {
            "IMAP_SERVER": "test",
            "MAIL": "test",
            "PASS": "test",
            "TELEGRAM_TOKEN": "test",
            "TELEGRAM_CHAT_ID": "test",
        }
        monitor = EmailMonitor(config)

        # Mock IMAP responses
        mock_connection = MagicMock()
        mock_imap.return_value = mock_connection
        mock_connection.search.return_value = ("OK", [b""])  # No messages

        monitor.check_emails()

        mock_connection.login.assert_called_once_with("test", "test")
        mock_connection.select.assert_called_once_with("inbox")

    def test_decode_mixed_header(self):
        """Test de decodificación de headers mixtos"""
        config = {
            "IMAP_SERVER": "test",
            "MAIL": "test",
            "PASS": "test",
            "TELEGRAM_TOKEN": "test",
            "TELEGRAM_CHAT_ID": "test",
        }
        monitor = EmailMonitor(config)

        # Simple ASCII
        header = "Test Subject"
        decoded = monitor._decode_mixed_header(header)
        assert decoded == "Test Subject"

        # Encoded header
        encoded_header = email.header.make_header([(b"Test Subject", "utf-8")])
        decoded = monitor._decode_mixed_header(str(encoded_header))
        assert decoded == "Test Subject"


# Test EmailMessage
class TestEmailMessage:
    def test_email_message_creation(self):
        """Test de creación de EmailMessage"""
        email_msg = EmailMessage(
            subject="Test Subject",
            sender="test@example.com",
            sender_domain="example.com",
            body="Test body content",
            message_id="12345",
            date="2023-01-01",
        )

        assert email_msg.subject == "Test Subject"
        assert email_msg.sender == "test@example.com"
        assert email_msg.sender_domain == "example.com"
        assert email_msg.body == "Test body content"
        assert email_msg.message_id == "12345"
        assert email_msg.date == "2023-01-01"


# Test de integración
class TestIntegration:
    @patch("src.core.email_monitor.Bot")
    @pytest.mark.asyncio
    async def test_full_notification_flow(self, mock_bot_class):
        """Test del flujo completo de notificación"""
        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot_class.return_value = mock_bot

        config = {
            "IMAP_SERVER": "test",
            "MAIL": "test",
            "PASS": "test",
            "TELEGRAM_TOKEN": "test",
            "TELEGRAM_CHAT_ID": "test",
        }
        monitor = EmailMonitor(config)

        # Test conexión a Telegram
        success = await monitor.test_telegram_connection()
        assert success

        # Test clasificación
        result = monitor.test_classification("Factura urgente", "Su factura ha vencido")
        assert result in ["Urgente", "Importante", "Otros"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
