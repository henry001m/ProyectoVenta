from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .ai import AiAnalyzer
from .core.config import get_settings
from .core.database import Base, engine, get_db
from .core.security import create_token, decode_token, hash_password, verify_password
from .models import Observation, ObservationStatus, Signal, Source, User
from .schemas import (
    LoginRequest, MarketSummary, ObservationCreate, ObservationOut, OAuthLoginRequest, RefreshRequest, RegisterRequest,
    SignalOut, SourceCreate, SourceOut, TokenPair, UserOut,
)

settings = get_settings()
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Kicks Insight API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
analyzer = AiAnalyzer(settings)


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


@app.get("/api/v1/integrations/whatsapp/webhook")
def verify_whatsapp(mode: str | None = None, token: str | None = None, challenge: str | None = None) -> str:
    if mode == "subscribe" and token == settings.whatsapp_verify_token and challenge:
        return challenge
    raise HTTPException(status_code=403, detail="Verificación inválida")


@app.post("/api/v1/integrations/whatsapp/webhook")
def whatsapp_webhook(payload: dict) -> dict[str, bool]:
    return {"received": True}


@app.get("/api/v1/integrations/tiktok/callback")
def tiktok_callback(code: str | None = None) -> dict[str, str]:
    return {"status": "received", "code_present": str(bool(code)).lower()}


@app.get("/api/v1/integrations/meta/callback")
def meta_callback(code: str | None = None) -> dict[str, str]:
    return {"status": "received", "code_present": str(bool(code)).lower()}

