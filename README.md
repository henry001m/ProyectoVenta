# Kicks Insight

Monorepo para analizar oferta, demanda y competencia de tenis deportivos y basqueteros.

## Componentes

- `apps/web`: Angular 21, NgModules, PrimeNG, NgRx y Cypress.
- `apps/mobile`: Flutter, Provider, GoRouter, Dio, Hive y EasyLocalization.
- `services/api`: FastAPI, SQLAlchemy, PostgreSQL, JWT y adaptadores de IA/integraciones.
- `infra`: servicios locales y configuración de despliegue.
- `docs`: arquitectura, API e integraciones.

## Inicio rápido

```bash
cp .env.example .env
python3 -m venv services/api/.venv
services/api/.venv/bin/pip install -r services/api/requirements.txt
cd services/api && python3 -m uvicorn app.main:app --reload
```

En otra terminal:

```bash
cd apps/web
npm install
npm start
```

La API queda en `http://localhost:8000` y Swagger en `/docs`.

## Fuentes externas

Las integraciones usan OAuth/webhooks y variables de entorno. Para grupos privados de WhatsApp y publicaciones que no expongan una API oficial se usa importación asistida de enlaces, capturas, imágenes, videos o textos. No se automatizan sesiones de WhatsApp Web ni se guardan contraseñas.

## Verificación

```bash
make typecheck
make test
```

