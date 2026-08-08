from __future__ import annotations

import httpx
import pytest
from unittest.mock import patch, MagicMock

from securesight.api.workers.notification_tasks import (
    dispatch_notification,
    _send_email,
    _send_slack,
    _send_teams,
    _send_telegram,
    _send_webhook,
)


def test_dispatch_notification_email():
    with patch("securesight.api.workers.notification_tasks._send_email", return_value=True) as mock_send:
        result = dispatch_notification("email", "test@example.com", "Alert!")
        assert result is True
        mock_send.assert_called_once_with("test@example.com", "Alert!")


def test_dispatch_notification_unknown_channel():
    result = dispatch_notification("unknown", "dest", "Alert!")
    assert result is False


@patch("securesight.api.workers.notification_tasks.smtplib.SMTP")
def test_send_email(mock_smtp_class):
    mock_smtp = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp
    
    result = _send_email("test@example.com", "Test Message")
    
    assert result is True
    mock_smtp.send_message.assert_called_once()
    msg = mock_smtp.send_message.call_args[0][0]
    assert msg["To"] == "test@example.com"


@patch("securesight.api.workers.notification_tasks.httpx.post")
def test_send_slack(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = _send_slack("https://hooks.slack.com/test", "Slack Message")
    
    assert result is True
    mock_post.assert_called_once_with(
        "https://hooks.slack.com/test",
        json={"text": "Slack Message"},
        timeout=10.0
    )


@patch("securesight.api.workers.notification_tasks.httpx.post")
def test_send_telegram(mock_post, monkeypatch):
    from securesight.api.core.config import get_settings
    
    settings = get_settings()
    monkeypatch.setattr(settings, "alert_telegram_bot_token", "fake_token")
    
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = _send_telegram("123456789", "Telegram Message")
    
    assert result is True
    mock_post.assert_called_once_with(
        "https://api.telegram.org/botfake_token/sendMessage",
        json={"chat_id": "123456789", "text": "Telegram Message"},
        timeout=10.0
    )


@patch("securesight.api.workers.notification_tasks.httpx.post")
def test_send_webhook_http_error(mock_post):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Error", request=MagicMock(), response=MagicMock())
    mock_post.return_value = mock_response

    result = _send_webhook("http://example.com/webhook", "Webhook Message", {"key": "value"})
    
    assert result is False
