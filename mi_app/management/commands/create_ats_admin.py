"""
Crea el usuario administrador ATS (soporte). Solo staff puede entrar a /ats/plataforma/administracion/.

Uso:
  python manage.py create_ats_admin
  python manage.py create_ats_admin --username soporte --email soporte@starpathai.mx

El usuario se crea con is_staff=True (acceso al panel Administración ATS).
Se pedirá contraseña por consola. Si el usuario ya existe, solo se asegura is_staff=True.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea o actualiza el usuario administrador ATS (is_staff=True) para el panel de administración."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="soporte", help="Nombre de usuario (default: soporte)")
        parser.add_argument("--email", default="soporte@starpathai.mx", help="Email del admin ATS")
        parser.add_argument("--no-input", action="store_true", help="No pedir contraseña; solo marcar staff si el usuario existe")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        email = (options["email"] or "").strip()
        no_input = options["no_input"]

        user = User.objects.filter(username=username).first()
        if user:
            if not user.is_staff:
                user.is_staff = True
                user.save(update_fields=["is_staff"])
                self.stdout.write(self.style.SUCCESS(f"Usuario '{username}' actualizado: is_staff=True."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Usuario '{username}' ya es staff. Accede a /ats/plataforma/administracion/"))
            return

        if no_input:
            self.stdout.write(self.style.WARNING("Usuario no existe. Crea uno con: python manage.py create_ats_admin (sin --no-input)"))
            return

        password = None
        while not password or len(password) < 8:
            password = self.get_pass("Contraseña (mín. 8 caracteres): ")
            if len(password) < 8:
                self.stdout.write(self.style.WARNING("Mínimo 8 caracteres."))

        user = User.objects.create_user(
            username=username,
            email=email or f"{username}@starpathai.mx",
            password=password,
            is_staff=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Usuario administrador ATS creado: {username}"))
        self.stdout.write("  Accede a la plataforma ATS, inicia sesión con este usuario y serás redirigido al panel de Administración ATS.")

    def get_pass(self, prompt):
        import getpass
        try:
            return getpass.getpass(prompt=prompt)
        except Exception:
            return input(prompt)
