"""
Crea el usuario administrador Órbita (soporte).
Solo staff puede entrar a /orbita/plataforma/administracion/.

Uso:
  python manage.py create_orbita_admin
  python manage.py create_orbita_admin --username soporte --email hola@starpathai.mx

El usuario se crea con is_staff=True.
Si el usuario ya existe, solo se asegura is_staff=True.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea o actualiza el usuario administrador Órbita (is_staff=True)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="soporte", help="Nombre de usuario (default: soporte)")
        parser.add_argument("--email", default="hola@starpathai.mx", help="Email del admin Órbita")
        parser.add_argument("--no-input", action="store_true", help="No pedir contraseña; solo marcar staff si el usuario existe")

    def handle(self, *args, **options):
        user_model = get_user_model()
        username = options["username"]
        email = (options["email"] or "").strip()
        no_input = options["no_input"]

        user = user_model.objects.filter(username=username).first()
        if user:
            if not user.is_staff:
                user.is_staff = True
                user.save(update_fields=["is_staff"])
                self.stdout.write(self.style.SUCCESS(f"Usuario '{username}' actualizado: is_staff=True."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Usuario '{username}' ya es staff."))
            self.stdout.write("Accede a /orbita/plataforma/administracion/.")
            return

        if no_input:
            self.stdout.write(
                self.style.WARNING(
                    "Usuario no existe. Crea uno con: python manage.py create_orbita_admin (sin --no-input)"
                )
            )
            return

        password = None
        while not password or len(password) < 8:
            password = self._get_pass("Contraseña (mín. 8 caracteres): ")
            if len(password) < 8:
                self.stdout.write(self.style.WARNING("Mínimo 8 caracteres."))

        user_model.objects.create_user(
            username=username,
            email=email or f"{username}@starpathai.mx",
            password=password,
            is_staff=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Usuario administrador Órbita creado: {username}"))
        self.stdout.write("Inicia sesión en la plataforma y se redirigirá al panel de Administración.")

    def _get_pass(self, prompt):
        import getpass

        try:
            return getpass.getpass(prompt=prompt)
        except Exception:
            return input(prompt)
