from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app, current_user
from app.models import User, WhatsAppAccount, WhatsAppContact, WhatsAppConversation, WhatsAppMessage


def test_conversation_filters_preview_pagination_and_owner_scope() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with TestSession() as db:
        owner = User(email="owner-wa@example.test", password_hash="x")
        other_user = User(email="other-wa@example.test", password_hash="x")
        db.add_all([owner, other_user])
        db.flush()
        owner_account = WhatsAppAccount(owner_user_id=owner.id, waba_id="waba-a", phone_number_id="phone-a", status="connected")
        other_account = WhatsAppAccount(owner_user_id=other_user.id, waba_id="waba-b", phone_number_id="phone-b", status="connected")
        db.add_all([owner_account, other_account])
        db.flush()
        jordan = WhatsAppContact(account_id=owner_account.id, wa_id="59170000001", phone_number="59170000001", display_name="Cliente Jordan")
        lebron = WhatsAppContact(account_id=owner_account.id, wa_id="59170000002", phone_number="59170000002", display_name="Cliente Nike")
        private = WhatsAppContact(account_id=other_account.id, wa_id="59170000003", phone_number="59170000003", display_name="Privado")
        db.add_all([jordan, lebron, private])
        db.flush()
        conv_jordan = WhatsAppConversation(account_id=owner_account.id, contact_id=jordan.id, unread_count=2, last_message_at=datetime.now(timezone.utc))
        conv_lebron = WhatsAppConversation(account_id=owner_account.id, contact_id=lebron.id, unread_count=0, last_message_at=datetime.now(timezone.utc))
        conv_private = WhatsAppConversation(account_id=other_account.id, contact_id=private.id, unread_count=1, last_message_at=datetime.now(timezone.utc))
        db.add_all([conv_jordan, conv_lebron, conv_private])
        db.flush()
        db.add_all([
            WhatsAppMessage(account_id=owner_account.id, conversation_id=conv_jordan.id, meta_message_id="wa-jordan", direction="inbound", message_type="text", body="¿Tienes talla 42?", status="received", timestamp=datetime.now(timezone.utc)),
            WhatsAppMessage(account_id=owner_account.id, conversation_id=conv_lebron.id, meta_message_id="wa-lebron", direction="inbound", message_type="text", body="Busco Nike Lebron", status="received", timestamp=datetime.now(timezone.utc)),
            WhatsAppMessage(account_id=other_account.id, conversation_id=conv_private.id, meta_message_id="wa-private", direction="inbound", message_type="text", body="Jordan privado", status="received", timestamp=datetime.now(timezone.utc)),
        ])
        db.commit()
        owner_id = owner.id

    def override_database():
        with TestSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_database
    app.dependency_overrides[current_user] = lambda: User(id=owner_id, email="owner-wa@example.test", full_name="Owner", password_hash="x", role="analyst")
    try:
        with TestClient(app) as client:
            all_items = client.get("/api/v1/whatsapp/conversations?limit=1&offset=0")
            assert all_items.status_code == 200
            assert len(all_items.json()) == 1
            assert all_items.json()[0]["last_message_preview"] in {"¿Tienes talla 42?", "Busco Nike Lebron"}

            unread = client.get("/api/v1/whatsapp/conversations?unread_only=true")
            assert unread.status_code == 200
            assert [item["contact"]["display_name"] for item in unread.json()] == ["Cliente Jordan"]

            search = client.get("/api/v1/whatsapp/conversations?search=Lebron")
            assert search.status_code == 200
            assert [item["contact"]["display_name"] for item in search.json()] == ["Cliente Nike"]

            history_search = client.get("/api/v1/whatsapp/conversations?search=talla%2042")
            assert history_search.status_code == 200
            assert [item["contact"]["display_name"] for item in history_search.json()] == ["Cliente Jordan"]

            page_two = client.get("/api/v1/whatsapp/conversations?limit=1&offset=1")
            assert page_two.status_code == 200
            assert page_two.json()[0]["id"] != all_items.json()[0]["id"]
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()
