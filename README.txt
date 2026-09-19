ELEVENTA MÓVIL V9 — BASE PROVISIONAL 17/09/2026

Incluye:
- Catálogo web responsive.
- SQLite compartido con catálogo provisional.
- API de búsqueda.
- Endpoint /api/sync idempotente: cada venta usa event_key único y no se descuenta dos veces.
- WhatsApp personal: permanece en silencio salvo que escriban MENU/MENÚ/INICIO; ignora grupos.
- Herramienta PC para enviar ventas pendientes cuando vuelva a encenderse.

IMPORTANTE:
1) Este paquete usa el catálogo de ayer. Mañana se puede reemplazar sin rehacer la web.
2) Las fotos quedan preparadas mediante image_url. No se asignan fotos dudosas automáticamente.
3) Para funcionar con la PC apagada, server.py debe alojarse en un servicio/servidor que permanezca encendido. El teléfono no puede ejecutarlo si también está apagado.
4) El conector exacto del monitor Eleventa actual debe copiar cada venta detectada a ventas_pendientes.jsonl con:
   {"event_key":"folio:codigo:linea","codigo":"4556","delta":-1,"source":"eleventa"}
   Al reconectar, pc_sync/enviar_pendientes.py las aplica una sola vez.
5) WhatsApp usa una conexión vinculada no oficial (Baileys). En un número personal puede existir riesgo de desconexión/restricción; no se incluye automatización masiva.
