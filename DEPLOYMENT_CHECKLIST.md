# Checklist antes de subir al repo / deployment

## 1. No subir secretos
- [ ] **`.env`** está en `.gitignore` (ya lo está). No quitar.
- [ ] Confirmar que **nunca** haces `git add .env` ni commiteas claves (OpenAI, email, DB).

## 2. Configuración en el servidor (producción)
En el panel de tu hosting (Render, Railway, etc.) define estas variables de entorno:

| Variable | Producción | Ejemplo |
|----------|------------|---------|
| `SECRET_KEY` | **Obligatorio** una clave distinta y aleatoria | `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_DEBUG` | **0** o **False** | `0` |
| `ALLOWED_HOSTS` | Tu dominio (y el del host si aplica) | `starpathai.mx,www.starpathai.mx,tu-app.onrender.com` |
| `DATABASE_URL` o `DB_*` | Según tu proveedor (Render suele dar `DATABASE_URL`) | — |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Mismo correo que en local si quieres enviar emails | — |
| `OPENAI_API_KEY` | Si usas análisis de CV con IA | — |

Si el front se sirve en otro dominio (ej. `https://tu-app.onrender.com`), añade en el servidor:
- `CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com`

## 3. Antes del primer deploy
- [ ] `python manage.py migrate` (en el servidor o en el build).
- [ ] `python manage.py collectstatic --noinput` (el proyecto ya usa WhiteNoise; el host debe ejecutar collectstatic si no lo hace el build).
- [ ] Crear un superusuario en producción si necesitas entrar al admin: `python manage.py createsuperuser`.

## 4. Repo
- [ ] Revisar que no haya archivos con contraseñas o API keys: `git status` y no añadir `.env`.
- [ ] Hacer push; en el servidor, el deploy usará las variables de entorno que configures ahí.

## 5. Después del deploy
- [ ] Probar login ATS, envío de formulario público y (si aplica) análisis de CV.
- [ ] Revisar que los estáticos (CSS/JS) carguen (WhiteNoise).
- [ ] Revisar logs por errores 500 o de base de datos.
