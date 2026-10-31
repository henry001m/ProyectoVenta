from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .core.database import Base


class ObservationStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    REVIEW = "review"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), default="")
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(50), default="analyst")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(50), default="manual")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    observations: Mapped[list["Observation"]] = relationship(back_populates="source")


class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    content_type: Mapped[str] = mapped_column(String(40), default="text")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    seller_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    size: Mapped[str | None] = mapped_column(String(30), nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    availability: Mapped[str] = mapped_column(String(40), default="unknown")
    status: Mapped[str] = mapped_column(String(40), default=ObservationStatus.PENDING.value)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    source: Mapped[Source | None] = relationship(back_populates="observations")
    signals: Mapped[list["Signal"]] = relationship(back_populates="observation", cascade="all, delete-orphan")


class Signal(Base):
    __tablename__ = "signals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    observation_id: Mapped[int] = mapped_column(ForeignKey("observations.id"))
    kind: Mapped[str] = mapped_column(String(60))
    intensity: Mapped[str] = mapped_column(String(30), default="medium")
    text: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    observation: Mapped[Observation] = relationship(back_populates="signals")


class WhatsAppAccount(Base):
    __tablename__ = "whatsapp_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    waba_id: Mapped[str] = mapped_column(String(100))
    phone_number_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_phone_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="connected")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WhatsAppContact(Base):
    __tablename__ = "whatsapp_contacts"
    __table_args__ = (UniqueConstraint("account_id", "wa_id", name="uq_whatsapp_contact_account_wa"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_accounts.id"), index=True)
    wa_id: Mapped[str] = mapped_column(String(128))
    phone_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(160), nullable=True)


class WhatsAppConversation(Base):
    __tablename__ = "whatsapp_conversations"
    __table_args__ = (UniqueConstraint("account_id", "contact_id", name="uq_whatsapp_conversation_contact"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_accounts.id"), index=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_contacts.id"), index=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_customer_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"
    __table_args__ = (UniqueConstraint("account_id", "meta_message_id", name="uq_whatsapp_message_meta_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_accounts.id"), index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_conversations.id"), index=True)
    meta_message_id: Mapped[str] = mapped_column(String(160))
    direction: Mapped[str] = mapped_column(String(12))
    message_type: Mapped[str] = mapped_column(String(30), default="text")
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(24), default="received")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    media_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WhatsAppMedia(Base):
    __tablename__ = "whatsapp_media"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_accounts.id"), index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_messages.id"), index=True)
    meta_media_id: Mapped[str] = mapped_column(String(160), index=True)
    media_type: Mapped[str] = mapped_column(String(30))
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WhatsAppMessageTemplate(Base):
    __tablename__ = "whatsapp_message_templates"
    __table_args__ = (UniqueConstraint("account_id", "name", "language_code", name="uq_whatsapp_template_account_name_language"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_accounts.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    language_code: Mapped[str] = mapped_column(String(20))
    category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="unknown")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class WhatsAppWebhookEvent(Base):
    __tablename__ = "whatsapp_webhook_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_key: Mapped[str] = mapped_column(String(128), unique=True)
    event_type: Mapped[str] = mapped_column(String(80))
    payload: Mapped[str] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

