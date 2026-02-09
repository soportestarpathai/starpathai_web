# Auditoría ATS — Cliente y Admin

Revisión de todos los elementos del proyecto ATS (cliente + administración) y lo que falta.

---

## ✅ Lo que está implementado

### Cliente ATS

| Área | Elemento | Estado |
|------|----------|--------|
| **Acceso** | Página producto (`/ats/`) | ✅ |
| **Acceso** | Login (`/ats/plataforma/`) | ✅ |
| **Acceso** | Registro | ✅ |
| **Acceso** | Logout | ✅ |
| **Dashboard** | Secciones: Candidatos, Reclutamiento, Mi cuenta | ✅ |
| **Dashboard** | KPIs (totales, aptos/revisión/no aptos, CVs usados/límite) | ✅ |
| **Dashboard** | Gráfica de estado (doughnut) | ✅ |
| **Dashboard** | Filtros (nombre/email, estado, vacante) | ✅ |
| **Dashboard** | Tabla de candidatos con enlace a detalle | ✅ |
| **Candidatos** | Detalle de candidato (datos, criterios, evaluación manual) | ✅ |
| **Reclutamiento** | Listado de vacantes, nueva vacante, eliminar | ✅ |
| **Reclutamiento** | Crear candidatos desde envíos de formularios | ✅ |
| **Formularios** | Lista, crear, editar, eliminar | ✅ |
| **Formularios** | Campos, criterios, opción solicitar CV/correo, layout (columnas) | ✅ |
| **Formularios** | Envíos por formulario (lista, archivos) | ✅ |
| **Formulario público** | GET/POST por UUID, thank you tras envío | ✅ |
| **Formulario público** | Subida de archivos (CV y campos tipo file) | ✅ |
| **Mi cuenta** | Plan actual, uso CVs, “Tu plan incluye” (pills) | ✅ |
| **Mi cuenta** | Cambio de plan (solicitud a soporte) + SweetAlert confirmación | ✅ |
| **Notificaciones** | Panel (lista izquierda, detalle derecha, scroll 5, “Ir al enlace”) | ✅ |
| **Notificaciones** | Campana en header + dropdown “Ver todas” | ✅ |
| **Notificaciones** | Marcar todas como leídas | ✅ |
| **Config. correo** | Configuración de correo (notificaciones, remitente) | ✅ |
| **Configurar cuenta** | Perfil: avatar, nombre contacto, empresa, teléfono | ✅ |
| **Base** | Sidebar, topbar (foto, nombre, rol), menú por rol | ✅ |
| **Base** | Context processor notificaciones cliente | ✅ |
| **Planes** | FREE (3), PRO (500), ENTERPRISE (2000) | ✅ |
| **Planes** | Lógica `subscription_can`, `apply_plan_to_subscription` | ✅ |
| **Email** | Notificaciones in-app + email al cliente (si config) | ✅ |
| **Email** | Correo a soporte en solicitud cambio de plan (HTML, teléfono) | ✅ |

### Admin ATS

| Área | Elemento | Estado |
|------|----------|--------|
| **Acceso** | Solo `is_staff`; redirect a administración tras login | ✅ |
| **Panel** | Listado clientes (empresa, contacto, email, plan, CVs) | ✅ |
| **Panel** | Aplicar plan (Gratuito/Pro/Enterprise) por cliente | ✅ |
| **Panel** | Notificación al cliente al aplicar plan | ✅ |
| **Panel** | Marcar solicitudes de cambio de plan como atendidas | ✅ |
| **Mi cuenta** | Página “Mi cuenta” (email, nombre, enlace cambiar contraseña) | ✅ |
| **Mi cuenta** | Cambio de contraseña (vista propia, mismo layout) | ✅ |
| **Notificaciones** | Campana con solicitudes de cambio de plan pendientes | ✅ |
| **Notificaciones** | Dropdown “Ver todas” → panel administración | ✅ |
| **Menú** | Solo administración + Mi cuenta + Cerrar sesión (sin menú cliente) | ✅ |
| **Header** | Mismo header (avatar placeholder, email, rol “Administrador”) | ✅ |
| **Modelo** | `PlanChangeRequest` (cliente, from_plan, to_plan, estado) | ✅ |
| **Django Admin** | Registro de modelos ATS + PlanChangeRequest | ✅ |

### Infra y datos

| Área | Estado |
|------|--------|
| Migraciones (incl. `0013_planchangerequest`) | ✅ |
| Context processor (cliente + admin) | ✅ |
| URLs y nombres de rutas | ✅ |
| Uso de `ats_client` / `_get_client_or_403` en vistas cliente | ✅ |
| Carpeta `static/` creada (evitar W004) | ✅ |

---

## ❌ Lo que falta o está incompleto

### 1. Recuperar contraseña (cliente y admin)

- **Falta:** Flujo “¿Olvidaste tu contraseña?” en `/ats/plataforma/`.
- **Idea:** Enlace en la pestaña de login que lleve a una vista de “Introduce tu email” y uso de `PasswordResetView` / `PasswordResetConfirmView` de Django (con email desde `settings`).
- **Prioridad:** Alta para producción.

### 2. Escaneo de CV con IA (consumo de cuota)

- **Estado:** El límite por plan (`cvs_limit`, `cvs_used`) y `subscription_can(subscription, "cvs_scan")` están implementados; el dashboard muestra “CVs usados / límite”.
- **Falta:** Ninguna acción en la app llama a `subscription.increment_cvs_used()` (no hay botón “Analizar con IA” ni integración con un servicio de análisis de CV).
- **Idea:** En detalle de candidato (o en envíos) un botón “Analizar CV con IA” que:
  - Compruebe `subscription_can(subscription, "cvs_scan")`.
  - Llame al servicio de IA, guarde resultado y llame a `increment_cvs_used()`.
- **Prioridad:** Alta si el producto debe ofrecer análisis de CV con IA.

### 3. Paginación en panel de administración

- **Estado:** Listado de clientes sin paginación.
- **Riesgo:** Con muchos clientes la tabla puede ser muy larga.
- **Idea:** Añadir `Paginator` en `ATSAdminDashboardView` (p. ej. 25 por página) y controles en `admin/dashboard.html`.
- **Prioridad:** Media.

### 4. Búsqueda / filtro en panel admin

- **Falta:** No hay búsqueda por empresa o email en el listado de clientes.
- **Idea:** Campo de búsqueda (GET) y filtrar `ATSClient` por `company_name` o `user__email`.
- **Prioridad:** Media.

### 5. Bloque “Solicitudes pendientes” en panel admin

- **Estado:** Las solicitudes de cambio de plan se ven en la campana y al “Ver todas” se va al panel, pero en el panel no hay un bloque tipo “Tienes X solicitudes pendientes” arriba de la tabla.
- **Idea:** En `admin/dashboard.html` mostrar un aviso o mini-tabla con las `PlanChangeRequest` con `status=pending` y enlace a la fila correspondiente.
- **Prioridad:** Baja (mejora de UX).

### 6. Validación de subida de archivos (formulario público)

- **Estado:** Se aceptan archivos en formulario público y en “solicitar CV” sin validación explícita de tipo o tamaño.
- **Riesgo:** Archivos muy grandes o tipos no deseados (PDF/DOC).
- **Idea:** En la vista del formulario público (o en el formulario): validar extensión/tipo de contenido y tamaño máximo (p. ej. con `settings.FILE_UPLOAD_MAX_MEMORY_SIZE` o un límite propio, p. ej. 10 MB).
- **Prioridad:** Media.

### 7. Rate limiting / anti-spam (formulario público)

- **Falta:** No hay límite de envíos por IP o por tiempo para el formulario público.
- **Riesgo:** Spam o abuso.
- **Idea:** Middleware o decorador que limite envíos por IP (p. ej. 5 por hora) o usar Django REST Framework throttling si se expone como API.
- **Prioridad:** Media para formularios públicos.

### 8. Página “Gracias” con URL fija (opcional)

- **Estado:** Tras enviar el formulario público se renderiza `form_public_thankyou.html` en la misma petición POST (no hay redirect).
- **Efecto:** Si el usuario recarga, puede reenviar (aunque el envío ya esté guardado) o ver de nuevo la misma página.
- **Idea:** Hacer `redirect` a una URL tipo `/ats/f/<uuid>/gracias/?submission=...` y mostrar el thank you por GET (y opcionalmente mensaje de “Ya has enviado el formulario” si se intenta reenviar).
- **Prioridad:** Baja.

### 9. Restricción de vistas por plan (opcional)

- **Estado:** Todas las vistas de cliente (formularios, config. correo, candidatos, etc.) están abiertas para cualquier plan; solo se usa `subscription_can` para “puede procesar CV” en el dashboard.
- **Idea:** Si en el futuro se restringe algo por plan (p. ej. solo PRO+ puede usar X), usar `subscription_can(subscription, "capability")` y devolver 403 o redirigir con mensaje.
- **Prioridad:** Baja hasta que se definan restricciones.

### 10. Tests automatizados ATS

- **Falta:** No hay tests para flujos ATS (registro, login, dashboard, formularios, notificaciones, admin, cambio de plan).
- **Idea:** Tests de vistas (cliente y staff), permisos, creación de `PlanChangeRequest` y notificaciones, y (opcional) formulario público.
- **Prioridad:** Alta para mantener el proyecto a largo plazo.

### 11. Documentación para despliegue

- **Falta:** No hay documento que liste variables de entorno (p. ej. `DATABASE_URL`, `EMAIL_*`, `ATS_SUPPORT_EMAIL`, `SECRET_KEY`), pasos de migración y creación de superuser/admin ATS.
- **Idea:** Un `docs/DEPLOY_ATS.md` o sección en README con checklist de despliegue.
- **Prioridad:** Media.

### 12. Baja de cuenta / eliminación de datos (opcional)

- **Falta:** No hay flujo para que el cliente solicite la baja o eliminación de sus datos (GDPR/LOPD).
- **Idea:** En “Mi cuenta” o “Configurar cuenta” un botón “Solicitar baja” (email a soporte) o “Eliminar mi cuenta” (con confirmación y borrado/anonymización en backend).
- **Prioridad:** Depende de requisitos legales.

---

## Resumen rápido

| Categoría | Cantidad |
|-----------|----------|
| Implementado (cliente) | ~35 ítems |
| Implementado (admin) | ~15 ítems |
| Falta (recomendado) | 12 ítems |
| Crítico / alta prioridad | Recuperar contraseña, escaneo IA (si aplica), tests |
| Mejoras media prioridad | Paginación admin, búsqueda admin, validación archivos, rate limit, docs despliegue |
| Mejoras baja prioridad | Bloque solicitudes pendientes en admin, thank you por URL, restricción por plan, baja de cuenta |

Si indicas por qué ítem quieres empezar (por ejemplo “recuperar contraseña” o “paginación admin”), puedo proponerte los cambios concretos en código (vistas, URLs, templates y settings).
