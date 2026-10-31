# Integraciones

## WhatsApp Business Cloud API

Kicks Insight se integra directamente con la Cloud API oficial de Meta usando HTTPS desde FastAPI. No se usa un BSP/intermediario. Flutter consume únicamente la API autenticada de Kicks Insight; el token de Meta nunca se entrega al cliente.

Configura `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_WABA_ID`, `WHATSAPP_PHONE_NUMBER_ID` y `WHATSAPP_API_VERSION` en el entorno del backend. La ruta de webhook es `GET/POST /api/v1/integrations/whatsapp/webhook`; debe publicarse con HTTPS y suscribirse al campo `messages`. Para coexistencia, configura también `smb_message_echoes` si Meta lo habilita para la incorporación.

La conexión por configuración directa valida el token consultando el Phone Number ID y asocia la cuenta al usuario autenticado. `POST /api/v1/whatsapp/accounts` registra esa conexión después de configurar las credenciales en el servidor. La incorporación de números mediante Embedded Signup depende de que Meta habilite ese flujo y los permisos correspondientes; la configuración manual no activa por sí sola la coexistencia.

Los mensajes y estados se guardan de forma idempotente. Los textos entrantes se convierten en observaciones y se analizan en una tarea posterior al acuse del webhook. La bandeja Flutter consulta la API periódicamente mientras está abierta.

La API oficial permite conversaciones individuales autorizadas con el negocio. No expone grupos privados como una bandeja general ni el historial completo como WhatsApp Web. El número actual solo debe conectarse por el flujo que Meta declare elegible. El envío fuera de la ventana de atención requiere una plantilla aprobada.

## TikTok

Se prepara OAuth y lectura de perfil/videos autorizados. El análisis de videos de terceros se realiza mediante enlace o archivo compartido hasta contar con los permisos de API correspondientes.

## Meta/Facebook

Se prepara un conector de Meta Business y un importador de Marketplace mediante URL, captura o imagen. No se asume acceso a perfiles personales o mensajes que no estén expuestos por una API autorizada.

