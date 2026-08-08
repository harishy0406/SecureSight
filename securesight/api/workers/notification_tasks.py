from __future__ import annotations

import httpx
from email.message import EmailMessage
import smtplib

from securesight.api.workers.celery_app import app as celery_app
from securesight.api.core.config import get_settings
from securesight.api.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="notification_tasks.dispatch_notification")
def dispatch_notification(channel_type: str, destination: str, message: str, metadata: dict | None = None) -> bool:
    """
    Dispatch a notification to the specified channel.
    channel_type can be: email, slack, teams, telegram, webhook
    destination is the specific target (e.g., email address, webhook URL, chat ID)
    """
    logger.info("notification.dispatch_started", channel_type=channel_type, destination=destination)

    try:
        if channel_type == "email":
            return _send_email(destination, message)
        elif channel_type == "slack":
            return _send_slack(destination, message)
        elif channel_type == "teams":
            return _send_teams(destination, message)
        elif channel_type == "telegram":
            return _send_telegram(destination, message)
        elif channel_type == "webhook":
            return _send_webhook(destination, message, metadata)
        else:
            logger.error("notification.unknown_channel", channel_type=channel_type)
            return False
    except Exception as e:
        logger.error("notification.dispatch_failed", channel_type=channel_type, error=str(e))
        return False


def _send_email(to_address: str, message: str) -> bool:
    settings = get_settings()
    host = getattr(settings, "alert_email_smtp_host", "localhost")
    port = int(getattr(settings, "alert_email_smtp_port", 1025))
    sender = getattr(settings, "alert_email_sender", "alerts@securesight.local")

    msg = EmailMessage()
    msg.set_content(message)
    msg["Subject"] = "SecureSight Alert"
    msg["From"] = sender
    msg["To"] = to_address

    try:
        with smtplib.SMTP(host, port) as server:
            # If auth is required in production, it would be added here
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error("notification.email_failed", error=str(e))
        return False


def _send_slack(webhook_url: str, message: str) -> bool:
    payload = {"text": message}
    try:
        response = httpx.post(webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()
        return True
    except httpx.HTTPError as e:
        logger.error("notification.slack_failed", error=str(e))
        return False


def _send_teams(webhook_url: str, message: str) -> bool:
    payload = {"text": message}
    try:
        response = httpx.post(webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()
        return True
    except httpx.HTTPError as e:
        logger.error("notification.teams_failed", error=str(e))
        return False


def _send_telegram(chat_id: str, message: str) -> bool:
    settings = get_settings()
    bot_token = getattr(settings, "alert_telegram_bot_token", None)
    if not bot_token:
        logger.error("notification.telegram_missing_token")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        return True
    except httpx.HTTPError as e:
        logger.error("notification.telegram_failed", error=str(e))
        return False


def _send_webhook(url: str, message: str, metadata: dict | None) -> bool:
    payload = {"message": message, "metadata": metadata or {}}
    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        return True
    except httpx.HTTPError as e:
        logger.error("notification.webhook_failed", error=str(e))
        return False
