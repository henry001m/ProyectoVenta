from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .core.config import Settings
from .models import WhatsAppAccount, WhatsAppContact, WhatsAppConversation, WhatsAppMedia, WhatsAppMessage


def verify_signature(raw_body: bytes, signature: str | None, app_secret: str | None) -> bool:
    if not app_secret or not signature or not signature.startswith("sha256="):
        return False
    digest = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={digest}", signature)


def message_text(message: dict[str, Any]) -> tuple[str, str, str | None]:
    kind = str(message.get("type", "unknown"))
    node = message.get(kind)
    node = node if isinstance(node, dict) else {}
    body = str(node.get("body") or node.get("caption") or node.get("name") or "")
    return kind, body, str(node["id"]) if node.get("id") else None


def _timestamp(value: Any) -> datetime:
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return datetime.now(timezone.utc)


def _contact_and_conversation(db: Session, account: WhatsAppAccount, wa_id: str, name: str | None) -> WhatsAppConversation:
    contact = db.scalar(select(WhatsAppContact).where(WhatsAppContact.account_id == account.id, WhatsAppContact.wa_id == wa_id))
    if contact is None:
        contact = WhatsAppContact(account_id=account.id, wa_id=wa_id, phone_number=wa_id if wa_id.isdigit() else None, display_name=name)
        db.add(contact)
        db.flush()
    elif name:
        contact.display_name = name
    conversation = db.scalar(select(WhatsAppConversation).where(WhatsAppConversation.account_id == account.id, WhatsAppConversation.contact_id == contact.id))
    if conversation is None:
        conversation = WhatsAppConversation(account_id=account.id, contact_id=contact.id, unread_count=0)
        db.add(conversation)
        db.flush()
    return conversation


def process_webhook(db: Session, payload: dict[str, Any], inserted_message_ids: list[int] | None = None) -> int:
    """Persist messages and delivery receipts. Caller owns transaction and event idempotency."""
    saved = 0
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            metadata = value.get("metadata") or {}
            phone_number_id = metadata.get("phone_number_id")
            account = db.scalar(select(WhatsAppAccount).where(WhatsAppAccount.phone_number_id == str(phone_number_id), WhatsAppAccount.status == "connected")) if phone_number_id else None
            if not account:
                continue
            names = {str(item.get("wa_id")): (item.get("profile") or {}).get("name") for item in value.get("contacts", [])}
            is_echo = change.get("field") == "smb_message_echoes"
            for message in value.get("messages", []):
                meta_id = str(message.get("id", ""))
                sender = str(message.get("to", "") if is_echo else message.get("from", ""))
                if not meta_id or not sender or db.scalar(select(WhatsAppMessage.id).where(WhatsAppMessage.account_id == account.id, WhatsAppMessage.meta_message_id == meta_id)):
                    continue
                kind, body, media_id = message_text(message)
                timestamp = _timestamp(message.get("timestamp"))
                conversation = _contact_and_conversation(db, account, sender, names.get(sender))
                conversation.last_message_at = timestamp
                if not is_echo:
                    conversation.last_customer_message_at = timestamp
                    conversation.unread_count += 1
                stored_message = WhatsAppMessage(account_id=account.id, conversation_id=conversation.id, meta_message_id=meta_id, direction="outbound" if is_echo else "inbound", message_type=kind, body=body, status="sent" if is_echo else "received", timestamp=timestamp, media_id=media_id)
                db.add(stored_message)
                db.flush()
                if media_id:
                    db.add(WhatsAppMedia(account_id=account.id, message_id=stored_message.id, meta_media_id=media_id, media_type=kind, mime_type=node_mime(message, kind), file_name=node_filename(message, kind), caption=body or None))
                if inserted_message_ids is not None:
                    inserted_message_ids.append(stored_message.id)
                saved += 1
            for status_item in value.get("statuses", []):
                meta_id = status_item.get("id")
                message = db.scalar(select(WhatsAppMessage).where(WhatsAppMessage.account_id == account.id, WhatsAppMessage.meta_message_id == meta_id)) if meta_id else None
                if message:
                    message.status = str(status_item.get("status", message.status))[:24]
    return saved


def node_mime(message: dict[str, Any], kind: str) -> str | None:
    media = message.get(kind)
    return str(media.get("mime_type")) if isinstance(media, dict) and media.get("mime_type") else None


def node_filename(message: dict[str, Any], kind: str) -> str | None:
    media = message.get(kind)
    return str(media.get("filename")) if isinstance(media, dict) and media.get("filename") else None


class WhatsAppCloudClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(self.settings.whatsapp_access_token and self.settings.whatsapp_phone_number_id and (self.settings.whatsapp_waba_id or self.settings.whatsapp_business_account_id))

    async def send(self, destination: str, payload: dict[str, Any]) -> str:
        if not self.settings.whatsapp_access_token or not self.settings.whatsapp_phone_number_id:
            raise HTTPException(status_code=503, detail="WhatsApp Cloud API no está configurada")
        url = f"https://graph.facebook.com/{self.settings.whatsapp_api_version}/{self.settings.whatsapp_phone_number_id}/messages"
        body = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": destination, **payload}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, headers={"Authorization": f"Bearer {self.settings.whatsapp_access_token}"}, json=body)
        if response.is_error:
            try:
                details = response.json().get("error", {}).get("message", "Meta rechazó el mensaje")
            except (ValueError, AttributeError):
                details = "Meta rechazó el mensaje"
            raise HTTPException(status_code=502, detail=details)
        result = response.json()
        messages = result.get("messages", [])
        if not messages or not messages[0].get("id"):
            raise HTTPException(status_code=502, detail="Meta no devolvió el identificador del mensaje")
        return str(messages[0]["id"])

    async def phone_details(self) -> dict[str, str | None]:
        if not self.settings.whatsapp_access_token or not self.settings.whatsapp_phone_number_id:
            raise HTTPException(status_code=503, detail="Configura el token y Phone Number ID de WhatsApp")
        url = f"https://graph.facebook.com/{self.settings.whatsapp_api_version}/{self.settings.whatsapp_phone_number_id}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers={"Authorization": f"Bearer {self.settings.whatsapp_access_token}"}, params={"fields": "id,display_phone_number,verified_name"})
        if response.is_error:
            raise HTTPException(status_code=502, detail="Meta no autorizó la consulta del número configurado")
        return response.json()


def outside_service_window(conversation: WhatsAppConversation) -> bool:
    last = conversation.last_customer_message_at
    if last is None:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - last > timedelta(hours=24)
