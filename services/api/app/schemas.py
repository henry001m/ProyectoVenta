from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    role: str


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str = Field(default="", max_length=160)


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class OAuthLoginRequest(BaseModel):
    id_token: str = Field(min_length=3)


class SourceCreate(BaseModel):
    kind: Literal["whatsapp", "tiktok", "meta", "manual"]
    name: str = Field(min_length=2, max_length=160)


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    name: str
    status: str
    last_synced_at: datetime | None


class ObservationCreate(BaseModel):
    source_id: int | None = None
    source_url: str | None = None
    content_type: Literal["text", "image", "video", "link", "export"] = "text"
    raw_text: str = Field(default="", max_length=20_000)


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source_id: int | None
    source_url: str | None
    content_type: str
    raw_text: str
    seller_name: str | None
    brand: str | None
    model_name: str | None
    size: str | None
    price: float | None
    city: str | None
    availability: str
    status: str
    confidence: float | None
    created_at: datetime


class SignalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    observation_id: int
    kind: str
    intensity: str
    text: str
    confidence: float
    created_at: datetime


class MarketSummary(BaseModel):
    observations: int
    analyzed: int
    average_price: float | None
    top_models: list[dict[str, str | int]]
    demand_signals: int
    sale_signals: int


class WhatsAppAccountCreate(BaseModel):
    display_phone_number: str | None = Field(default=None, max_length=40)


class WhatsAppAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    waba_id: str
    phone_number_id: str
    display_phone_number: str | None
    status: str


class WhatsAppContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    wa_id: str
    phone_number: str | None
    display_name: str | None


class WhatsAppConversationOut(BaseModel):
    id: int
    contact: WhatsAppContactOut
    last_message_at: datetime | None
    last_customer_message_at: datetime | None
    unread_count: int
    last_message_preview: str | None = None
    last_message_type: str | None = None
    last_message_direction: str | None = None


class WhatsAppMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    meta_message_id: str
    direction: str
    message_type: str
    body: str
    status: str
    timestamp: datetime
    media_id: str | None


class WhatsAppSendRequest(BaseModel):
    type: Literal["text", "image", "document", "audio", "template"] = "text"
    text: str | None = Field(default=None, max_length=4096)
    media_id: str | None = None
    media_url: str | None = None
    caption: str | None = Field(default=None, max_length=1024)
    filename: str | None = Field(default=None, max_length=255)
    template_name: str | None = Field(default=None, max_length=255)
    language_code: str = "es"
    template_components: list[dict] = Field(default_factory=list)

