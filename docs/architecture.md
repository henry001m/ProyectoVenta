# Arquitectura

La aplicación sigue una arquitectura feature-first. El backend es la fuente de contratos OpenAPI; Angular y Flutter mantienen DTOs tipados alineados con esos contratos.

## Flujo de análisis

`importación → observación → extracción IA → señales → métricas → recomendación`

Las observaciones conservan el contenido original y la salida estructurada de IA. La confianza baja fuerza una revisión manual.

El adaptador remoto usa la Responses API de OpenAI cuando `OPENAI_API_KEY` está configurada y solicita salida JSON estructurada. Sin esa clave se usa el analizador determinista local para mantener el entorno ejecutable.

## Privacidad

Los tokens se almacenan solamente en backend y deben cifrarse en producción. Los reportes anonimizan teléfonos y nombres personales. El contenido importado debe contar con autorización del usuario y base legal aplicable.

