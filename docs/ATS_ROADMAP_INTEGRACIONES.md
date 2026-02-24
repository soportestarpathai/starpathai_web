# Qué integrar o construir para estar a la altura de la competencia (y ser mejor)

Lista priorizada de lo que haría falta para **entrar** en el mismo nivel que los ATS de la tabla (Bizneo, Zoho, Personio, etc.) y, luego, para **ser mejor** o diferenciarte.

---

## 1. Para “entrar” (table stakes: parecer un ATS completo)

Lo que casi todos tienen y tú aún no, o lo tienes a medias. Sin esto, en ventas te preguntan “¿y esto?” y no puedes decir que sí.

| # | Integración / funcionalidad | Qué es | Esfuerzo aprox. | Prioridad |
|---|-----------------------------|--------|------------------|------------|
| 1 | **Estados de vacante (Open / Closed)** | Que cada vacante tenga estado: Abierta, Cerrada, Borrador. Ocultar o marcar “no acepta candidatos” cuando está cerrada. | Bajo (campo + filtros + lógica en formulario) | Alta |
| 2 | **Pipeline de candidato (etapas)** | Sustituir o ampliar “Apto / Revisión / No apto” por etapas: Aplicado → Screening → Entrevista → Oferta → Contratado / Rechazado. Vista lista o Kanban. | Medio (modelo, vistas, opcional Kanban) | Alta |
| 3 | **Historial de cambios de estado** | Log por candidato: quién/cuándo cambió el estado (auditoría y reportes). | Bajo (tabla + guardar en cada cambio) | Alta |
| 4 | **Dashboard / reportes básicos** | Gráficas o KPIs: candidatos por vacante, por etapa, tiempo en etapa, origen (formulario X). No hace falta Power BI; con lo que ya tienes + export puedes hacer una vista “Resumen” en el dashboard. | Medio | Media |
| 5 | **Preguntas knockout (filtro en formulario)** | Preguntas tipo “¿Tienes disponibilidad inmediata?” Sí/No; si No → no dejar enviar o marcar como “no cumple mínimo”. | Medio (campos condicionales o reglas en el formulario) | Media |
| 6 | **Detección de candidatos duplicados** | Al aplicar o al subir CV, avisar si ya existe un candidato con mismo email (o mismo teléfono si lo capturas). | Bajo–medio | Media |

Resumen “para entrar”: **estados de vacante + pipeline + historial** son los tres que más te piden cuando te comparan con otro ATS. Luego, **reportes básicos** y **knockout/duplicados** redondean.

---

## 2. Para “ser mejor” (diferenciarte o igualar ventajas de ellos)

Cosas que te ponen al nivel de los más fuertes de la tabla o por encima en algo concreto.

| # | Integración / funcionalidad | Qué es | Esfuerzo aprox. | Prioridad |
|---|-----------------------------|--------|------------------|------------|
| 7 | **Publicación en 1–2 portales (multiposting)** | Integración con LinkedIn Jobs y/o Indeed (o una bolsa local) para publicar la vacante desde tu ATS y que los CVs lleguen a tu funnel. | Alto (APIs, OAuth, mapeo de campos) | Media–alta si tu mercado lo pide |
| 8 | **API pública (Enterprise)** | API REST para que el cliente integre su web, su HRIS o sus herramientas. CRUD de candidatos, vacantes, obtener lista por vacante/estado. | Medio–alto (diseño, auth, documentación) | Media (ya en plan Enterprise) |
| 9 | **Vista Kanban por etapa** | Arrastrar candidatos entre columnas (etapas) en una vista tipo tablero. | Medio (front-end + actualizar estado) | Media |
| 10 | **Correos automáticos por trigger** | Ej.: “Si el candidato pasa a etapa Entrevista → enviar email con plantilla X”. Configurable por vacante o global. | Medio (modelo de reglas + cola o envío inmediato) | Media |
| 11 | **Portal de carrera / employer branding** | Página “Trabaja con nosotros” con listado de vacantes abiertas y enlace a tu formulario. Aunque sea una página estática por cliente con su marca. | Medio (subdominio o path por cliente, plantilla) | Media–baja |
| 12 | **Métricas por etapa (Time to Hire, embudo)** | Tiempo medio por etapa, abandono por etapa, conversión Aplicado → Contratado. Aunque sea una pantalla con números y un gráfico. | Medio (consultas + vista) | Media |
| 13 | **Reclutador asignado** | Campo “asignado a” en vacante y/o candidato (útil cuando haya varios usuarios por cliente). | Bajo | Baja hasta que tengas multi-usuario |
| 14 | **App móvil (web responsive ya lo tienes)** | App nativa o PWA para que reclutadores revisen candidatos y muevan etapas desde el móvil. | Alto | Baja (primero consolidar web) |

Resumen “ser mejor”: **multiposting (aunque sea 1–2 portales)** y **API** son los que más te acercan a Personio/Zoho. **Kanban + triggers + métricas** te dan el “flujo moderno” que piden en ventas.

---

## 3. Opcional / enterprise (cuando el producto y el cliente lo pidan)

No necesarios para “entrar” ni para “ser mejor” en la primera versión; típicos de ATS enterprise o de mercados muy regulados.

| # | Integración / funcionalidad | Qué es | Prioridad |
|---|-----------------------------|--------|-----------|
| 15 | **Requisición con flujo de aprobación** | Área pide vacante → aprobador aprueba → se crea/abre vacante. | Baja (hasta tener clientes con muchos departamentos) |
| 16 | **Entrevistas (agenda + scorecards)** | Calendario, invitación por correo, scorecard por entrevista (por etapa o por tipo). | Media–baja (módulo grande) |
| 17 | **Ofertas y firma digital** | Carta oferta, estados (enviada/aceptada/rechazada), firma electrónica. | Baja |
| 18 | **Integración HRIS / nómina** | Al marcar “Contratado”, export o API a sistema de nómina o HRIS del cliente. | Baja (muy dependiente del cliente) |
| 19 | **Tests psicométricos o de habilidades** | Integración con proveedor externo (ej. test técnico o psicométrico) y guardar resultado en el candidato. | Baja (como Krowdy) |
| 20 | **Video preguntas / videollamada** | Que el candidato grabe respuestas en video o que la entrevista se agende por videollamada desde el ATS. | Baja |
| 21 | **Cumplimiento normativo (GDPR, etc.)** | Documentación, opciones de consentimiento, exportación de datos personales, baja. | Media si vendes en EU; baja si solo México |
| 22 | **Multi-idioma en la interfaz** | Que el cliente pueda ver el ATS en inglés u otro idioma. | Baja si tu foco es México |

---

## 4. Orden sugerido (roadmap mínimo para “entrar” y “ser mejor”)

**Fase 1 – Entrar (3–6 meses)**  
1. Estados de vacante (Open/Closed/Draft).  
2. Pipeline de candidato (etapas configurables) + historial de estado.  
3. Vista Kanban (opcional pero muy visible).  
4. Reportes básicos (dashboard con KPIs por vacante/etapa).  
5. Detección de duplicados (por email).  
6. Preguntas knockout en formulario (aunque sea 1–2 reglas simples).

**Fase 2 – Ser mejor (6–12 meses)**  
7. Multiposting a 1 portal (LinkedIn o Indeed o bolsa local).  
8. API pública documentada (plan Enterprise).  
9. Triggers de correo (ej. “al pasar a Entrevista enviar X”).  
10. Métricas por etapa (Time to Hire, embudo).  
11. Portal de carrera / “Trabaja con nosotros” por cliente (opcional).

**Fase 3 – Enterprise / diferenciación**  
12. Módulo de entrevistas (agenda + scorecards).  
13. Ofertas y firma digital.  
14. Integración HRIS/nómina (bajo demanda).  
15. Tests externos (psicométricos/técnicos).  
16. GDPR / cumplimiento (si vendes en EU).

---

## 5. Resumen en una lista (checklist)

**Para entrar al nivel de la competencia:**  
- [ ] Estados de vacante (Open / Closed / Draft)  
- [ ] Pipeline de etapas (Aplicado → Screening → … → Contratado/Rechazado)  
- [ ] Historial de cambios de estado del candidato  
- [ ] Dashboard / reportes básicos (KPIs, gráficas)  
- [ ] Preguntas knockout en formulario  
- [ ] Detección de candidatos duplicados (email)  

**Para ser mejor:**  
- [ ] Publicación en 1–2 portales (multiposting)  
- [ ] API pública (Enterprise)  
- [ ] Vista Kanban por etapa  
- [ ] Correos automáticos por trigger (cambio de etapa)  
- [ ] Métricas por etapa (Time to Hire, embudo)  
- [ ] Portal de carrera / employer branding (opcional)  
- [ ] Reclutador asignado (cuando haya multi-usuario)  

**Opcional / más adelante:**  
- [ ] Requisición con aprobación  
- [ ] Módulo entrevistas (agenda + scorecards)  
- [ ] Ofertas y firma digital  
- [ ] Integración HRIS / nómina  
- [ ] Tests psicométricos o técnicos externos  
- [ ] Video / videollamada  
- [ ] GDPR y cumplimiento  
- [ ] Multi-idioma UI  

Con la **Fase 1** completada ya puedes decir que tienes un ATS con flujo completo (vacante abierta/cerrada, pipeline, historial, reportes básicos). Con la **Fase 2** te pones al nivel de productos como Sesame o Kenjo en integraciones y automatización, manteniendo tu ventaja en IA en el CV.
