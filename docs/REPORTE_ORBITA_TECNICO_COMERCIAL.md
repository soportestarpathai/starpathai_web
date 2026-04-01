# Reporte Órbita ATS — Técnico y Comercial

Fecha de corte: 31 de marzo de 2026

## 1) Resumen ejecutivo

Órbita es una plataforma ATS multiempresa (SaaS) para gestionar reclutamiento de punta a punta: creación de vacantes, recepción de postulaciones por múltiples canales, análisis de CV con IA, evaluación manual, comunicación con candidatos y operación administrativa por cliente.

Estado actual: funcional y desplegable en producción, con separación de canales web + workers para automatizaciones (Telegram e IMAP).

---

## 2) Alcance funcional actual (producto)

### 2.1 Captura y operación de reclutamiento
- Gestión de vacantes (crear, editar, eliminar).
- Gestión de candidatos (detalle, estado, score, CV, acciones de comunicación).
- Formularios de postulación:
  - Constructor de campos dinámicos.
  - Enlace público por formulario.
  - Historial de envíos y administración.
- Evaluación manual por criterios (Cumple/No cumple) con pesos.

### 2.2 Canales de entrada de postulaciones
- Formulario web público.
- Chat conversacional web del formulario.
- Telegram bot (flujo conversacional vinculado a formularios).
- Correo entrante IMAP (procesado en background para convertir correos a postulaciones).

### 2.3 IA y analítica
- Análisis de CV con OpenAI (score, estatus, explicación, skills).
- Fallback automático (stub) cuando no hay API key de OpenAI.
- Configuración de análisis por cliente y por vacante.
- Registro de consumo de tokens (LLMUsageLog) para monitoreo administrativo.

### 2.4 Comunicación y notificaciones
- Notificaciones in-app.
- Envío de correos al candidato (apto/no seleccionado) vía SMTP por cliente.
- Plantillas HTML para correos de candidato.
- Configuración de correo saliente y entrante por cliente (SMTP/IMAP).

### 2.5 Administración
- Panel de administración ATS para usuarios staff.
- Solicitudes de cambio de plan y baja de cuenta.
- Gestión administrativa de clientes, planes y notificaciones.

---

## 3) Vista técnica

### 3.1 Stack y arquitectura
- Backend: Django 6 + Django REST Framework.
- Base de datos: MySQL o PostgreSQL (con fallback SQLite local).
- IA: OpenAI SDK.
- Bot: python-telegram-bot.
- Estáticos: WhiteNoise.
- Logging: consola + archivo (`logs/starpath.log`).

### 3.2 Módulos clave
- `mi_app/views/ats/ats_views.py`: flujo principal ATS (dashboard, candidatos, vacantes, formularios, correo, admin).
- `mi_app/views/ats/form_chat_views.py`: chat web de formularios y sesiones.
- `mi_app/services/cv_analysis.py`: extracción + análisis IA de CV.
- `mi_app/telegram_bot.py`: bot conversacional para postulaciones.
- `mi_app/management/commands/process_incoming_emails.py`: worker IMAP.
- `mi_app/ats_notifications.py`: notificaciones y correos.
- `starpath_web/urls.py`: mapa completo de rutas.

### 3.3 Requerimientos operativos
- Servicio web Django para UI/API.
- Worker de Telegram para escuchar mensajes:
  - `python manage.py run_telegram_bot`
- Worker de correo entrante IMAP (si se usa esta vía):
  - `python manage.py process_incoming_emails --loop --interval 60`

### 3.4 Variables críticas de entorno
- Seguridad y servidor: `SECRET_KEY`, `DJANGO_DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
- Base de datos: `USE_MYSQL` + `MYSQL_*` o `USE_POSTGRES`/`DATABASE_URL`.
- IA: `OPENAI_API_KEY` (y opcional `OPENAI_MODEL`).
- Telegram: `TELEGRAM_BOT_TOKEN`.
- Correo global/base: `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`.
- API documentos: `DOCUMENTS_API_KEY`.

---

## 4) Vista comercial

### 4.1 Propuesta de valor actual
- Reducir tiempo operativo de reclutamiento con automatización multicanal.
- Aumentar velocidad de filtro con scoring IA y criterios manuales.
- Unificar comunicación y seguimiento en una sola plataforma.

### 4.2 Segmentos objetivo
- PyME y mid-market con reclutamiento recurrente.
- Equipos de RH que reciben candidatos por formulario, correo y mensajería.

### 4.3 Empaquetado comercial (planes)
- FREE:
  - 10 candidatos, 2 vacantes, 3 análisis IA/mes.
- PRO:
  - candidatos y vacantes ilimitados, 500 análisis IA/mes.
  - habilita exportación y mensaje personalizado.
- ENTERPRISE:
  - candidatos y vacantes ilimitados, 2000 análisis IA/mes.
  - API, reportes y soporte dedicado (según capacidades configuradas).

### 4.4 Capacidades monetizables ya implementadas
- Límite por consumo IA.
- Upgrade por mayor volumen.
- Diferenciación por features (exportación, mensajes personalizados, API/reportes).

---

## 5) Estado de madurez y siguientes pasos

### 5.1 Estado actual
- Producto funcional en operación ATS.
- Automatizaciones principales disponibles vía workers.
- Lista para despliegue productivo con configuración adecuada.

### 5.2 Recomendaciones inmediatas
- Asegurar ejecución continua de workers (Telegram e IMAP) en producción.
- Mantener rotación de secretos y endurecer gestión de credenciales.
- Consolidar monitoreo de jobs y alertas de fallas de worker.

---

## 6) Roadmap por fases (alineado al mapa de procesos)

Objetivo: evolucionar de ATS (Talent Acquisition fuerte) a plataforma integral de ciclo de talento.

### Fase 1 (0-8 semanas) — Consolidación ATS y cierre de brechas inmediatas

Foco principal: cerrar huecos de Talent Acquisition y estabilidad operativa.

- Entregables:
  - Sourcing integrado (publicación y trazabilidad en bolsas/canales externos).
  - Agenda de entrevistas y recordatorios.
  - Pipeline de contratación (oferta, aceptación, checklist preingreso).
  - Tablero operativo de workers (Telegram/IMAP) con alertas básicas.
- Impacto comercial:
  - Mayor conversión de demo a pago por cubrir proceso end-to-end de reclutamiento.
  - Menor fricción de onboarding de nuevos clientes ATS.
- Dependencias técnicas:
  - Integraciones externas de publicación.
  - Jobs programados y observabilidad mínima (logs/health checks).

### Fase 2 (8-16 semanas) — Onboarding operativo

Foco principal: activar el bloque de Onboarding del mapa.

- Entregables:
  - Workflows de alta de colaborador por plantilla (por rol/área).
  - Checklists de accesos y provisión de herramientas.
  - Tareas automáticas por responsable con SLA.
  - Evidencia de cumplimiento por paso (auditable).
- Impacto comercial:
  - Incremento de ticket promedio por pasar de ATS a suite de talento.
  - Mayor retención por dependencia operativa del cliente.
- Dependencias técnicas:
  - Motor de tareas por estado.
  - Modelo de responsables y permisos por área.

### Fase 3 (16-24 semanas) — Performance & Execution

Foco principal: habilitar ejecución y evaluación continua.

- Entregables:
  - Objetivos por puesto/persona.
  - Seguimiento de avance con alertas de riesgo.
  - Evaluación de capacidades (capability assessment) por criterios.
  - Dashboard de cumplimiento de SLA y decisiones.
- Impacto comercial:
  - Venta consultiva a cuentas medianas y enterprise.
  - Caso de uso continuo post-contratación (no solo reclutamiento).
- Dependencias técnicas:
  - Modelo de métricas por colaborador/equipo.
  - Historial de eventos y trazabilidad por periodo.

### Fase 4 (24-36 semanas) — Workforce Planning y analítica predictiva

Foco principal: activar planeación de capacidad y demanda.

- Entregables:
  - Planeación de headcount por área y periodo.
  - Forecast de demanda y simulación de escenarios.
  - Alineación de capacidad vs presupuesto.
  - Recomendaciones de contratación/reasignación con IA.
- Impacto comercial:
  - Posicionamiento como plataforma estratégica de talento.
  - Mayor valor en renovación anual enterprise.
- Dependencias técnicas:
  - Data mart operativo (histórico de candidatos, contrataciones, desempeño).
  - Modelos de forecast y tableros ejecutivos.

### Prioridad de ejecución recomendada

1. Fase 1 (rápido retorno y cierre funcional ATS).
2. Fase 2 (expande valor a onboarding).
3. Fase 3 (retención y uso continuo).
4. Fase 4 (diferenciación estratégica y enterprise).
