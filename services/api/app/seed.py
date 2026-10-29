from .core.database import Base, SessionLocal, engine
from .models import Source


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if not db.query(Source).count():
        db.add_all([Source(kind="manual", name="Importación manual", status="manual"), Source(kind="whatsapp", name="WhatsApp Business", status="disconnected")])
        db.commit()
    db.close()


if __name__ == "__main__":
    main()

