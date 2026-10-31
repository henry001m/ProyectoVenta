import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .ai import AiAnalyzer
from .core.config import get_settings
from .core.database import Base, SessionLocal, engine, get_db
from .core.security import create_token, decode_token, hash_password, verify_password
from .models import Observation, ObservationStatus, Signal, Source, User, WhatsAppAccount, WhatsAppContact, WhatsAppConversation, WhatsAppMessage, WhatsAppWebhookEvent
from .schemas import (
    LoginRequest, MarketSummary, ObservationCreate, ObservationOut, OAuthLoginRequest, RefreshRequest, RegisterRequest,
    SignalOut, SourceCreate, SourceOut, TokenPair, UserOut, WhatsAppAccountCreate, WhatsAppAccountOut,
    WhatsAppConversationOut, WhatsAppMessageOut, WhatsAppSendRequest,
)
from .whatsapp import WhatsAppCloudClient, outside_service_window, process_webhook, verify_signature

settings = get_settings()
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Kicks Insight API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
analyzer = AiAnalyzer(settings)
whatsapp_client = WhatsAppCloudClient(settings)


def analyze_whatsapp_message_ids(message_ids: list[int]) -> None:
    """Analyze persisted inbound text messages after the webhook has been acknowledged."""
    if not message_ids:
        return
    db = SessionLocal()
    try:
        source = db.scalar(select(Source).where(Source.kind == "whatsapp"))
        if source is None:
            source = Source(kind="whatsapp", name="WhatsApp Business", status="connected")
            db.add(source)
            db.flush()
        for message in db.scalars(select(WhatsAppMessage).where(WhatsAppMessage.id.in_(message_ids), WhatsAppMessage.direction == "inbound", WhatsAppMessage.message_type == "text", WhatsAppMessage.body != "")):
            observation = Observation(source_id=source.id, content_type="text", raw_text=message.body, status=ObservationStatus.PROCESSING.value)
            db.add(observation)
            db.flush()
            result = analyzer.extract_product_data(message.body)
            observation.brand, observation.model_name, observation.size, observation.price = result.brand, result.model_name, result.size, result.price
            observation.city, observation.availability, observation.confidence = result.city, result.availability, result.confidence
            observation.status = ObservationStatus.ANALYZED.value if result.confidence >= 0.6 else ObservationStatus.REVIEW.value
            for signal in result.signals:
                db.add(Signal(observation_id=observation.id, kind=str(signal["kind"]), intensity=str(signal["intensity"]), text=message.body, confidence=float(signal["confidence"])))
        source.status = "connected"
        source.last_synced_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def current_user(authorization: Annotated[str | None, Header()] = None, db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticación requerida")
    payload = decode_token(authorization.split(" ", 1)[1])
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return user


def tokens_for(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_token(str(user.id), "access", timedelta(minutes=settings.access_token_minutes)),
        refresh_token=create_token(str(user.id), "refresh", timedelta(days=settings.refresh_token_days)),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "kicks-insight-api"}


@app.post("/api/v1/auth/register", response_model=TokenPair, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenPair:
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    user = User(email=payload.email.lower(), full_name=payload.full_name, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return tokens_for(user)


@app.post("/api/v1/auth/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    return tokens_for(user)


@app.post("/api/v1/auth/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    token = decode_token(payload.refresh_token)
    if token.get("typ") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    user = db.get(User, int(token["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return tokens_for(user)


@app.post("/api/v1/auth/logout")
def logout(_: User = Depends(current_user)) -> dict[str, bool]:
    return {"success": True}


@app.post("/api/v1/auth/forgot-password")
def forgot_password(_: dict) -> dict[str, str]:
    return {"message": "Si el correo existe, recibirás instrucciones para recuperar tu contraseña."}


@app.post("/api/v1/auth/oauth/{provider}", response_model=TokenPair)
def oauth_login(provider: str, payload: OAuthLoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    if provider not in {"google", "apple"}:
        raise HTTPException(status_code=400, detail="Proveedor OAuth no soportado")
    if not payload.id_token.startswith("demo:"):
        raise HTTPException(status_code=501, detail=f"Configura las credenciales OAuth de {provider} en el entorno")
    email = payload.id_token.removeprefix("demo:").lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email, full_name=email.split("@", 1)[0], password_hash=hash_password("oauth-managed"))
        db.add(user)
        db.commit()
        db.refresh(user)
    return tokens_for(user)


@app.get("/api/v1/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> User:
    return user


@app.get("/api/v1/sources", response_model=list[SourceOut])
def list_sources(_: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Source]:
    return list(db.scalars(select(Source).order_by(Source.created_at.desc())))


@app.post("/api/v1/sources", response_model=SourceOut, status_code=201)
def create_source(payload: SourceCreate, _: User = Depends(current_user), db: Session = Depends(get_db)) -> Source:
    source = Source(kind=payload.kind, name=payload.name, status="manual" if payload.kind == "manual" else "disconnected")
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@app.post("/api/v1/sources/import", response_model=ObservationOut, status_code=201)
def import_source(payload: ObservationCreate, _: User = Depends(current_user), db: Session = Depends(get_db)) -> Observation:
    observation = Observation(**payload.model_dump(), status=ObservationStatus.PENDING.value)
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


@app.get("/api/v1/observations", response_model=list[ObservationOut])
def list_observations(search: str | None = Query(default=None), _: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Observation]:
    query = select(Observation).order_by(Observation.created_at.desc())
    if search:
        query = query.where(Observation.raw_text.ilike(f"%{search}%"))
    return list(db.scalars(query.limit(100)))


@app.get("/api/v1/observations/{observation_id}", response_model=ObservationOut)
def get_observation(observation_id: int, _: User = Depends(current_user), db: Session = Depends(get_db)) -> Observation:
    item = db.get(Observation, observation_id)
    if not item:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
    return item


@app.post("/api/v1/observations/{observation_id}/analyze", response_model=ObservationOut)
def analyze_observation(observation_id: int, _: User = Depends(current_user), db: Session = Depends(get_db)) -> Observation:
    item = db.get(Observation, observation_id)
    if not item:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
    result = analyzer.extract_product_data(item.raw_text)
    item.brand, item.model_name, item.size, item.price = result.brand, result.model_name, result.size, result.price
    item.city, item.availability, item.confidence = result.city, result.availability, result.confidence
    item.status = ObservationStatus.ANALYZED.value if result.confidence >= 0.6 else ObservationStatus.REVIEW.value
    for signal in result.signals:
        db.add(Signal(observation_id=item.id, kind=str(signal["kind"]), intensity=str(signal["intensity"]), text=item.raw_text, confidence=float(signal["confidence"])))
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/v1/demand-signals", response_model=list[SignalOut])
def demand_signals(_: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Signal]:
    return list(db.scalars(select(Signal).where(Signal.kind == "demand").order_by(Signal.created_at.desc()).limit(100)))


@app.get("/api/v1/sale-signals", response_model=list[SignalOut])
def sale_signals(_: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Signal]:
    return list(db.scalars(select(Signal).where(Signal.kind == "sale").order_by(Signal.created_at.desc()).limit(100)))


@app.get("/api/v1/analytics/dashboard", response_model=MarketSummary)
def dashboard(_: User = Depends(current_user), db: Session = Depends(get_db)) -> MarketSummary:
    observations = db.scalar(select(func.count(Observation.id))) or 0
    analyzed = db.scalar(select(func.count(Observation.id)).where(Observation.status == ObservationStatus.ANALYZED.value)) or 0
    average_price = db.scalar(select(func.avg(Observation.price)).where(Observation.price.is_not(None)))
    demand = db.scalar(select(func.count(Signal.id)).where(Signal.kind == "demand")) or 0
    sales = db.scalar(select(func.count(Signal.id)).where(Signal.kind == "sale")) or 0
    rows = db.execute(select(Observation.brand, func.count(Observation.id)).where(Observation.brand.is_not(None)).group_by(Observation.brand).order_by(func.count(Observation.id).desc()).limit(5)).all()
    return MarketSummary(observations=observations, analyzed=analyzed, average_price=round(float(average_price), 2) if average_price else None, top_models=[{"model": row[0] or "Desconocido", "count": row[1]} for row in rows], demand_signals=demand, sale_signals=sales)


@app.get("/api/v1/whatsapp/accounts", response_model=list[WhatsAppAccountOut])
def list_whatsapp_accounts(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[WhatsAppAccount]:
    return list(db.scalars(select(WhatsAppAccount).where(WhatsAppAccount.owner_user_id == user.id).order_by(WhatsAppAccount.id.desc())))


@app.post("/api/v1/whatsapp/accounts", response_model=WhatsAppAccountOut, status_code=201)
async def create_whatsapp_account(payload: WhatsAppAccountCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> WhatsAppAccount:
    if not whatsapp_client.configured:
        raise HTTPException(status_code=503, detail="Completa las variables WHATSAPP_* del backend antes de conectar una cuenta")
    phone = await whatsapp_client.phone_details()
    phone_id = str(phone.get("id") or settings.whatsapp_phone_number_id)
    account = db.scalar(select(WhatsAppAccount).where(WhatsAppAccount.phone_number_id == phone_id))
    if account and account.owner_user_id != user.id:
        raise HTTPException(status_code=409, detail="El número ya está asociado a otra cuenta de Kicks Insight")
    if account is None:
        account = WhatsAppAccount(owner_user_id=user.id, waba_id=settings.whatsapp_waba_id or settings.whatsapp_business_account_id or "", phone_number_id=phone_id, display_phone_number=payload.display_phone_number or phone.get("display_phone_number"), status="connected")
        db.add(account)
    else:
        account.waba_id = settings.whatsapp_waba_id or settings.whatsapp_business_account_id or account.waba_id
        account.display_phone_number = payload.display_phone_number or phone.get("display_phone_number") or account.display_phone_number
        account.status = "connected"
    db.commit()
    db.refresh(account)
    return account


@app.post("/api/v1/whatsapp/accounts/{account_id}/connect", response_model=WhatsAppAccountOut)
async def connect_whatsapp_account(account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> WhatsAppAccount:
    account = db.scalar(select(WhatsAppAccount).where(WhatsAppAccount.id == account_id, WhatsAppAccount.owner_user_id == user.id))
    if not account:
        raise HTTPException(status_code=404, detail="Cuenta de WhatsApp no encontrada")
    await whatsapp_client.phone_details()
    account.status = "connected"
    db.commit()
    db.refresh(account)
    return account


@app.post("/api/v1/whatsapp/accounts/{account_id}/disconnect", response_model=WhatsAppAccountOut)
def disconnect_whatsapp_account(account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> WhatsAppAccount:
    account = db.scalar(select(WhatsAppAccount).where(WhatsAppAccount.id == account_id, WhatsAppAccount.owner_user_id == user.id))
    if not account:
        raise HTTPException(status_code=404, detail="Cuenta de WhatsApp no encontrada")
    account.status = "disconnected"
    db.commit()
    db.refresh(account)
    return account


@app.get("/api/v1/whatsapp/conversations", response_model=list[WhatsAppConversationOut])
def list_whatsapp_conversations(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=160),
    unread_only: bool = Query(default=False),
) -> list[dict]:
    query = (
        select(WhatsAppConversation, WhatsAppContact)
        .join(WhatsAppContact, WhatsAppContact.id == WhatsAppConversation.contact_id)
        .join(WhatsAppAccount, WhatsAppAccount.id == WhatsAppConversation.account_id)
        .where(WhatsAppAccount.owner_user_id == user.id, WhatsAppAccount.status == "connected")
    )
    if unread_only:
        query = query.where(WhatsAppConversation.unread_count > 0)
    if search and search.strip():
        term = f"%{search.strip()}%"
        matching_message = (
            select(WhatsAppMessage.id)
            .where(WhatsAppMessage.conversation_id == WhatsAppConversation.id, WhatsAppMessage.body.ilike(term))
            .exists()
        )
        query = query.where(or_(WhatsAppContact.display_name.ilike(term), WhatsAppContact.wa_id.ilike(term), matching_message))
    rows = db.execute(
        query.order_by(WhatsAppConversation.last_message_at.desc().nullslast(), WhatsAppConversation.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    result = []
    for conversation, contact in rows:
        latest = db.scalar(
            select(WhatsAppMessage)
            .where(WhatsAppMessage.conversation_id == conversation.id)
            .order_by(WhatsAppMessage.timestamp.desc(), WhatsAppMessage.id.desc())
            .limit(1)
        )
        preview = None
        if latest:
            preview = latest.body.strip() or {
                "image": "[Imagen]",
                "video": "[Video]",
                "audio": "[Audio]",
                "document": "[Archivo]",
                "sticker": "[Sticker]",
            }.get(latest.message_type, f"[{latest.message_type}]")
        result.append({
            "id": conversation.id,
            "contact": contact,
            "last_message_at": conversation.last_message_at,
            "last_customer_message_at": conversation.last_customer_message_at,
            "unread_count": conversation.unread_count,
            "last_message_preview": preview,
            "last_message_type": latest.message_type if latest else None,
            "last_message_direction": latest.direction if latest else None,
        })
    return result


@app.get("/api/v1/whatsapp/conversations/{conversation_id}/messages", response_model=list[WhatsAppMessageOut])
def list_whatsapp_messages(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db), limit: int = Query(default=50, ge=1, le=100), before_id: int | None = Query(default=None, ge=1)) -> list[WhatsAppMessage]:
    conversation = db.scalar(select(WhatsAppConversation).join(WhatsAppAccount).where(WhatsAppConversation.id == conversation_id, WhatsAppAccount.owner_user_id == user.id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    query = select(WhatsAppMessage).where(WhatsAppMessage.conversation_id == conversation_id)
    if before_id is not None:
        query = query.where(WhatsAppMessage.id < before_id)
    rows = list(db.scalars(query.order_by(WhatsAppMessage.timestamp.desc(), WhatsAppMessage.id.desc()).limit(limit)))
    conversation.unread_count = 0
    db.commit()
    return list(reversed(rows))


@app.post("/api/v1/whatsapp/conversations/{conversation_id}/messages", response_model=WhatsAppMessageOut, status_code=201)
async def send_whatsapp_message(conversation_id: int, payload: WhatsAppSendRequest, user: User = Depends(current_user), db: Session = Depends(get_db)) -> WhatsAppMessage:
    row = db.execute(select(WhatsAppConversation, WhatsAppContact, WhatsAppAccount).join(WhatsAppContact, WhatsAppContact.id == WhatsAppConversation.contact_id).join(WhatsAppAccount, WhatsAppAccount.id == WhatsAppConversation.account_id).where(WhatsAppConversation.id == conversation_id, WhatsAppAccount.owner_user_id == user.id, WhatsAppAccount.status == "connected")).first()
    if not row:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    conversation, contact, account = row
    if payload.type != "template" and outside_service_window(conversation):
        raise HTTPException(status_code=409, detail="La ventana de atención de 24 horas venció; envía una plantilla aprobada")
    request_body: dict
    if payload.type == "text":
        if not payload.text:
            raise HTTPException(status_code=422, detail="El texto es obligatorio")
        request_body = {"type": "text", "text": {"preview_url": False, "body": payload.text}}
    elif payload.type == "template":
        if not payload.template_name:
            raise HTTPException(status_code=422, detail="El nombre de plantilla es obligatorio")
        request_body = {"type": "template", "template": {"name": payload.template_name, "language": {"code": payload.language_code}, "components": payload.template_components}}
    else:
        if not payload.media_id and not payload.media_url:
            raise HTTPException(status_code=422, detail="Se requiere media_id o media_url")
        media: dict[str, str] = {"id" if payload.media_id else "link": payload.media_id or payload.media_url or ""}
        if payload.caption:
            media["caption"] = payload.caption
        if payload.type == "document" and payload.filename:
            media["filename"] = payload.filename
        request_body = {"type": payload.type, payload.type: media}
    meta_id = await whatsapp_client.send(contact.wa_id, request_body)
    now = datetime.now(timezone.utc)
    message = WhatsAppMessage(account_id=account.id, conversation_id=conversation.id, meta_message_id=meta_id, direction="outbound", message_type=payload.type, body=payload.text or payload.caption or payload.template_name or "", status="sent", timestamp=now, media_id=payload.media_id)
    conversation.last_message_at = now
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@app.get("/api/v1/integrations/whatsapp/webhook")
def verify_whatsapp_webhook(request: Request) -> PlainTextResponse:
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and settings.whatsapp_verify_token and token and hmac_compare(token, settings.whatsapp_verify_token) and challenge is not None:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Verificación de webhook inválida")


def hmac_compare(candidate: str, expected: str) -> bool:
    import hmac
    return hmac.compare_digest(candidate, expected)


@app.post("/api/v1/integrations/whatsapp/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> dict[str, bool | int]:
    raw_body = await request.body()
    if not verify_signature(raw_body, request.headers.get("X-Hub-Signature-256"), settings.whatsapp_app_secret):
        raise HTTPException(status_code=401, detail="Firma de webhook inválida o WHATSAPP_APP_SECRET no configurado")
    try:
        payload = json.loads(raw_body)
        if not isinstance(payload, dict):
            raise ValueError("Webhook JSON debe ser un objeto")
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Payload JSON inválido") from None
    event_key = hashlib.sha256(raw_body).hexdigest()
    if db.scalar(select(WhatsAppWebhookEvent.id).where(WhatsAppWebhookEvent.event_key == event_key)):
        return {"received": True, "duplicate": True, "messages": 0}
    event_type = ",".join(sorted({str(change.get("field", "unknown")) for entry in payload.get("entry", []) for change in entry.get("changes", [])})) or "unknown"
    event = WhatsAppWebhookEvent(event_key=event_key, event_type=event_type, payload=raw_body.decode("utf-8"), created_at=datetime.now(timezone.utc))
    db.add(event)
    inserted_message_ids: list[int] = []
    try:
        db.flush()
        message_count = process_webhook(db, payload, inserted_message_ids)
        event.processed_at = datetime.now(timezone.utc)
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"received": True, "duplicate": True, "messages": 0}
    if inserted_message_ids:
        background_tasks.add_task(analyze_whatsapp_message_ids, inserted_message_ids)
    return {"received": True, "duplicate": False, "messages": message_count}


@app.get("/api/v1/integrations/tiktok/callback")
def tiktok_callback(code: str | None = None) -> dict[str, str]:
    return {"status": "received", "code_present": str(bool(code)).lower()}


@app.get("/api/v1/integrations/meta/callback")
def meta_callback(code: str | None = None) -> dict[str, str]:
    return {"status": "received", "code_present": str(bool(code)).lower()}

