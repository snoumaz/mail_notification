import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import email

import main

# Test load_sender_groups


def test_load_sender_groups():
    groups = main.load_sender_groups("sender_groups.json")
    assert isinstance(groups, dict)
    assert (
        "Clientes" in groups
        or "FincasGalindo" in groups
        or "Sepe/Soc" in groups
        or "Soporte" in groups
    )


# Test get_label_for_sender


def test_get_label_for_sender():
    # Known sender
    sender = "cliente@example.com"
    main.SENDER_GROUPS = {"Clientes": ["cliente@example.com"]}
    label = main.get_label_for_sender(sender)
    assert label == "Clientes"

    # Unknown sender
    sender = "unknown@example.com"
    label = main.get_label_for_sender(sender)
    assert label == "Otros"


# Test decode_mixed_header


def test_decode_mixed_header():
    # Simple ASCII
    header = "Test Subject"
    assert main.decode_mixed_header(header) == "Test Subject"

    # Encoded header
    encoded_header = email.header.make_header([(b"Test Subject", "utf-8")])
    assert main.decode_mixed_header(str(encoded_header)) == "Test Subject"


# Test clean_text


def test_clean_text():
    text = "  This is   a test\n\n"
    cleaned = main.clean_text(text)
    assert cleaned == "This is a test"


# Test escape_markdown


def test_escape_markdown():
    text = "_ * [ ] ( ) ~ ` > # + - = | { } . !"
    escaped = main.escape_markdown(text)
    # Check that all special characters are escaped
    for ch in "_ * [ ] ( ) ~ ` > # + - = | { } . !".split():
        assert f"\\{ch}" in escaped


# Test notify_telegram mock


@patch("main.Bot")
@pytest.mark.asyncio
async def test_notify_telegram(mock_bot_class):
    import html

    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    mock_bot_class.return_value = mock_bot

    main.TELEGRAM_CHAT_ID = "12345"
    main.TELEGRAM_TOKEN = "token"

    subject = "Subject"
    sender = "sender@example.com"
    snippet = "Snippet"
    label = "Label"

    await main.notify_telegram(subject, sender, snippet, label)

    assert mock_bot.send_message.called
    args, kwargs = mock_bot.send_message.call_args
    assert kwargs["chat_id"] == "12345"
    assert html.escape(subject) in kwargs["text"]
    assert html.escape(sender) in kwargs["text"]
    assert html.escape(snippet) in kwargs["text"]
    assert html.escape(label) in kwargs["text"]


# Note: Testing check_emails fully requires mocking imaplib and email fetching, which is complex and not included here.

if __name__ == "__main__":
    pytest.main()
