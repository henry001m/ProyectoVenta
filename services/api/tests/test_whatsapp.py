import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import User, WhatsAppAccount, WhatsAppConversation, WhatsAppMessage
from app.whatsapp import outside_service_window, process_webhook, verify_signature


def test_webhook_signature_requires_exact_raw_body_and_secret() -> None:
    body = b'{"object":"whatsapp_business_account"}'
    secret = "test-app-secret"
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, f"sha256={digest}", secret)
    assert not verify_signature(body + b" ", f"sha256={digest}", secret)
    assert not verify_signature(body, f"sha256={digest}", None)


def test_inbound_message_is_persisted_once_and_echo_is_outbound() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(email="wa@example.test", password_hash="x")
        db.add(user)
        db.flush()
        account = WhatsAppAccount(owner_user_id=user.id, waba_id="waba-1", phone_number_id="phone-1", status="connected")
        db.add(account)
        db.flush()
        incoming = {"entry": [{"changes": [{"field": "messages", "value": {"metadata": {"phone_number_id": "phone-1"}, "contacts": [{"wa_id": "59170000000", "profile": {"name": "Cliente"}}], "messages": [{"id": "wamid-in", "from": "59170000000", "timestamp": "1761000000", "type": "text", "text": {"body": "¿Tienes Jordan talla 42?"}}]}}]}]}
        assert process_webhook(db, incoming) == 1
        assert process_webhook(db, incoming) == 0
        echo = {"entry": [{"changes": [{"field": "smb_message_echoes", "value": {"metadata": {"phone_number_id": "phone-1"}, "messages": [{"id": "wamid-out", "from": "phone-1", "to": "59170000000", "timestamp": "1761000001", "type": "text", "text": {"body": "Sí, disponible"}}]}}]}]}
        assert process_webhook(db, echo) == 1
        db.flush()
        messages = list(db.scalars(select(WhatsAppMessage).order_by(WhatsAppMessage.id)))
        conversation = db.scalar(select(WhatsAppConversation))
        assert [message.direction for message in messages] == ["inbound", "outbound"]
        assert conversation is not None and conversation.unread_count == 1
        assert conversation.last_customer_message_at.replace(tzinfo=timezone.utc) == datetime.fromtimestamp(1761000000, tz=timezone.utc)
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_service_window_uses_last_customer_message() -> None:
    conversation = WhatsAppConversation(last_customer_message_at=datetime.now(timezone.utc) - timedelta(hours=23))
    assert not outside_service_window(conversation)
    conversation.last_customer_message_at = datetime.now(timezone.utc) - timedelta(hours=25)
    assert outside_service_window(conversation)
    conversation.last_customer_message_at = None
    assert outside_service_window(conversation)
