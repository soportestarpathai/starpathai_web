# Despliegue ATS — Star Path

Checklist y variables de entorno para desplegar el proyecto con el módulo ATS.

---

## 1. Variables de entorno

Crea un archivo `.env` en la raíz del proyecto (o configura las variables en tu hosting).

### Base de datos (PostgreSQL en producción)

```env
DATABASE_URL=postgresql://usuario:contraseña@host:5432/nombre_bd
```

O por separado:

```env
DB_NAME=nombre_bd
DB_USER=usuario
DB_PASSWORD=contraseña
DB_HOST=tu-host.postgres.render.com
DB_PORT=5432
```

### Correo (para notificaciones ATS, recuperar contraseña, contacto)

```env
EMAIL_HOST_USER=tu-correo@gmail.com
EMAIL_HOST_PASSWORD=contraseña-de-aplicacion
DEFAULT_FROM_EMAIL=Star Path <tu-correo@gmail.com>
CONTACT_TO_EMAIL=soporte@starpathai.mx
```

### ATS (opcional; tienen valor por defecto)

```env
ATS_SUPPORT_EMAIL=soporte@starpathai.mx
ATS_FORM_PUBLIC_MAX_FILE_SIZE=10485760
ATS_FORM_PUBLIC_ALLOWED_EXTENSIONS=pdf,doc,docx
ATS_FORM_PUBLIC_RATE_LIMIT_COUNT=5
ATS_FORM_PUBLIC_RATE_LIMIT_SECONDS=3600
```

### Análisis de CV con IA (OpenAI)

Para que el botón «Analizar con IA» use el modelo de OpenAI en lugar de la evaluación básica (stub), añade tu clave en `.env`:

```env
OPENAI_API_KEY=sk-tu-clave-de-openai
```

Opcional (modelo por defecto es `gpt-4o-mini`):

```env
OPENAI_MODEL=gpt-4o-mini
```

**Importante:** no subas la clave a Git. En producción usa variables de entorno del hosting. Sin `OPENAI_API_KEY`, el análisis sigue funcionando con una evaluación automática básica.

### API de extracción de documentos (INE, comprobante)

El endpoint `POST /api/documents/extract/` requiere autenticación por API key:

```env
DOCUMENTS_API_KEY=tu-clave-secreta-para-documentos
```

El cliente debe enviar la clave en el header:
- `Authorization: Bearer tu-clave-secreta-para-documentos`
- o `X-API-Key: tu-clave-secreta-para-documentos`

Genera una clave segura con: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Seguridad (producción)

```env
SECRET_KEY=genera-una-clave-segura-y-no-la-subas-a-git
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
```

---

## 2. Migraciones

Con el entorno virtual activado:

```bash
python manage.py migrate
```

---

## 3. Usuario administrador Django (superusuario)

Para acceder a `/admin/` (Django admin):

```bash
python manage.py createsuperuser
```

Indica username, email y contraseña cuando se soliciten.

---

## 4. Usuario administrador ATS (soporte)

Para acceder al panel **Administración ATS** (`/ats/plataforma/administracion/`) hace falta un usuario con **staff**:

```bash
python manage.py create_ats_admin
```

Por defecto crea el usuario `soporte` con email `soporte@starpathai.mx`. Para otro usuario/correo:

```bash
python manage.py create_ats_admin --username adminats --email soporte@starpathai.mx
```

Ese usuario inicia sesión en `/ats/plataforma/` y será redirigido al panel de administración ATS.

---

## 5. Archivos estáticos (producción)

```bash
python manage.py collectstatic --noinput
```

Configura el servidor (Nginx, etc.) para servir los archivos en `staticfiles/` bajo `/static/` y los subidos en `media/` bajo `/media/`.

---

## 6. Comprobar que todo responde

- Página principal: `/`
- Producto ATS: `/ats/`
- Login/registro ATS: `/ats/plataforma/`
- Recuperar contraseña: `/ats/plataforma/recuperar-password/`
- Admin Django: `/admin/` (con superusuario)
- Panel admin ATS: `/ats/plataforma/administracion/` (con usuario staff)

---

## 7. Resumen de URLs ATS

| Ruta | Descripción |
|------|-------------|
| `/ats/` | Página producto ATS |
| `/ats/plataforma/` | Login / registro |
| `/ats/plataforma/recuperar-password/` | Recuperar contraseña |
| `/ats/plataforma/dashboard/` | Dashboard cliente (candidatos, reclutamiento, Mi cuenta) |
| `/ats/plataforma/administracion/` | Panel administración (solo staff) |
| `/ats/f/<uuid>/` | Formulario público de postulación |
| `/ats/f/<uuid>/gracias/` | Página de agradecimiento tras enviar formulario |
