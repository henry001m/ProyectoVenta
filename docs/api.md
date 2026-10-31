# API

La especificación OpenAPI se sirve desde FastAPI en `/openapi.json`. Los endpoints iniciales se encuentran bajo `/api/v1` y cubren autenticación, fuentes, observaciones, señales, analítica y WhatsApp Business.

## WhatsApp Business

- `GET/POST /api/v1/integrations/whatsapp/webhook`: validación de Meta y recepción autenticada de eventos.
- `GET/POST /api/v1/whatsapp/accounts`: listar la cuenta activa o verificar y registrar las credenciales configuradas en el backend.
- `POST /api/v1/whatsapp/accounts/{id}/connect|disconnect`: revalidar o desactivar el uso local de la cuenta.
- `GET /api/v1/whatsapp/conversations`: bandeja paginada con `limit` y `offset`; admite `search` (nombre, teléfono o contenido de mensaje) y `unread_only`.
- Cada conversación incluye la vista previa, el tipo y la dirección del mensaje más reciente.
- `GET /api/v1/whatsapp/conversations/{id}/messages`: mensajes paginados hacia atrás con `before_id`.
- `POST /api/v1/whatsapp/conversations/{id}/messages`: enviar texto, plantilla, imagen, documento o audio.

Los endpoints de cuenta, conversación y envío requieren JWT. El webhook se autentica con `X-Hub-Signature-256` y el secreto de la aplicación Meta. Una cuenta solo puede enviar texto libre dentro de las 24 horas posteriores al último mensaje entrante; fuera de esa ventana se requiere una plantilla aprobada.

