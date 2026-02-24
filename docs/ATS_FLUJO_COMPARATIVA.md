# Comparativa: Flujo ATS típico vs Star Path ATS actual

## Flujo estándar vs lo que tenemos

| Fase típica | Qué implica | ¿Lo tenemos? | Notas |
|-------------|-------------|---------------|--------|
| **1. Requisición** | Área pide vacante → aprobación → ID vacante → reclutador asignado. Estados: Pending Approval → Approved | **Parcial** | Tenemos **Vacante** (título, descripción, perfil IA). No tenemos: flujo de aprobación, ID de requisición, reclutador asignado por vacante. |
| **2. Publicación** | Publicar en bolsa, LinkedIn, Indeed, web. Estado: Open. ATS centraliza CVs. | **Parcial** | Vacantes existen pero **sin estado** (Open/Closed). No hay integración con portales ni “publicación” explícita; el flujo es formulario propio + enlace. |
| **3. Aplicación** | Candidato llena formulario, adjunta CV, knockout questions. Parseo CV, score preliminar, duplicados. | **Sí** | Formularios dinámicos, CV obligatorio/opcional, enlace público. **Parseo CV con IA** (score, match, habilidades). No hay detección de duplicados ni preguntas knockout explícitas. |
| **4. Screening** | Reclutador revisa CV, valida requisitos, llamada corta. Estados: Screening, Phone Interview, Rejected, On Hold. Kanban. | **Parcial** | **Score + estado** (Apto / En revisión / No apto) = resultado de screening. No hay **pipeline por etapas** (Screening → Entrevista → Oferta). No Kanban. |
| **5. Entrevistas** | Etapas configurables (RH, Técnica, Manager, Panel). Agendar, correo automático, scorecards. | **No** | No hay etapas de entrevista ni agendamiento. |
| **6. Evaluaciones** | Pruebas técnicas, psicométricos, assessment. APIs externas. | **Parcial** | Criterios de evaluación manual (Cumple/No cumple) y score por criterios. No integración con tests externos. |
| **7. Oferta** | Carta oferta, aprobación, firma digital. Estados: Offer Extended / Accepted / Declined. | **No** | No módulo de ofertas. |
| **8. Contratación** | Candidato → empleado, handoff a nómina/HRIS, onboarding. Estado: Hired. | **No** | No HRIS ni onboarding. |

---

## Modelo actual (resumido)

- **Candidato:** `id`, `vacancy`, `name`, `email`, `score`, `status` (APTO/REVISION/NO_APTO), `match_percentage`, `explanation_text`, CV, habilidades evaluadas.
- **Vacante:** `id`, `title`, `description`, `profile_for_analysis`, `desired_skills`. Sin estado ni reclutador asignado.
- **Sin:** historial de estados, pipeline configurable, reclutador asignado, etapas de entrevista, ofertas, HRIS.

---

## Qué falta (y si es recomendable)

### Recomendable a corto/medio plazo

1. **Estados de vacante (Open / Closed)**  
   - Añadir en `Vacancy` un campo `status` (Open, Closed, Draft).  
   - Evita que sigan llegando candidatos a vacantes ya cerradas. Poco esfuerzo, mucho orden.

2. **Historial de estado del candidato**  
   - Tabla `CandidateStatusLog`: candidato, estado_anterior, estado_nuevo, fecha, usuario (opcional).  
   - Permite ver “cuándo pasó a Apto” o “cuándo se rechazó”. Útil para auditoría y reportes.

3. **Pipeline simple por vacante (etapas configurables)**  
   - En lugar de solo Apto/Revisión/No apto, tener etapas tipo: Aplicado → Screening → Entrevista → Oferta → Contratado / Rechazado.  
   - Opcional: que cada vacante tenga su propia lista de etapas (o usar una lista global por cliente).  
   - Permite vista tipo Kanban y métricas por etapa (donde se atoran).

4. **Reclutador asignado**  
   - Si en el futuro hay varios usuarios por cliente (varios reclutadores), tener `assigned_to` (User) en Vacante y/o en Candidato.  
   - Si hoy solo hay un usuario por cliente, se puede posponer.

### Recomendable solo si el producto crece

5. **Requisición con aprobación**  
   - Flujo: “Área pide vacante” → “Aprobador aprueba” → se crea/abre vacante.  
   - Útil en empresas con muchos departamentos; para pymes puede ser overkill al inicio.

6. **Publicación en portales (LinkedIn, Indeed)**  
   - Integraciones con APIs de portales.  
   - Coste y complejidad altos; suele ser fase Enterprise o integración con herramientas ya usadas.

7. **Entrevistas (agenda + scorecards)**  
   - Calendario, envío de correos, scorecard por entrevista.  
   - Muy valioso pero implica bastante desarrollo; se puede plantear como siguiente gran módulo después del pipeline.

8. **Ofertas y firma digital**  
   - Carta oferta, estados Offer Extended/Accepted/Declined, firma.  
   - Típico de ATS enterprise; se puede dejar para una fase posterior.

9. **Handoff a HRIS / nómina**  
   - Exportación o API hacia sistema de nómina/HRIS cuando el candidato pasa a “Contratado”.  
   - Muy dependiente del cliente; conviene cuando ya haya demanda clara.

---

## Enfoque técnico sugerido (sin implementar aún)

Para alinearte al flujo típico sin reescribir todo:

- **Candidato:** ya tienes `id`, `vacancy`, `score`. Añadirías:
  - `status` actual como etapa de pipeline (no solo Apto/Revisión/No apto).
  - Opcional: `assigned_recruiter_id` (FK User, nullable).
- **Historial:** tabla `CandidateStatusLog` (candidato_id, from_status, to_status, created_at, user_id opcional).
- **Vacante:** `status` (Open/Closed/Draft), opcional `assigned_recruiter_id`.
- **Pipeline:** tabla `PipelineStage` (cliente, nombre, orden) y `Candidate.status` o FK a etapa actual; transiciones según reglas de negocio.

Así mantienes el modelo actual y lo vas extendiendo hacia el flujo Requisition → Open → Applied → Screening → Interview → Assessment → Offer → Hired/Rejected, priorizando lo que tus clientes pidan primero (por ejemplo: estados de vacante + pipeline + historial).

---

## Resumen

- **Tenemos cubierto:** aplicación (formulario + CV), parseo/score con IA, screening básico (Apto/Revisión/No apto), evaluación manual por criterios, correos al candidato (apto/rechazo), export CSV/Excel, LangSmith.
- **Falta y es muy recomendable:** estados de vacante (Open/Closed), historial de cambios de estado del candidato, pipeline de etapas (aunque sea simple) y vista tipo Kanban.
- **Falta y es más “enterprise”:** requisición con aprobación, publicación en portales, entrevistas con agenda/scorecards, ofertas y firma, integración HRIS.

Si quieres, el siguiente paso puede ser: (1) diseño de modelo (PostgreSQL) para estados de vacante + historial de candidato + pipeline, o (2) diagrama BPMN del flujo que quieres soportar en 6–12 meses, para decidir en qué orden implementar.
