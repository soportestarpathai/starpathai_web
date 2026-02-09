"""
Comando: python manage.py list_superusers
Lista los usuarios con is_superuser=True para verificar que el admin existe.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Lista los superusuarios (usuarios admin)."

    def handle(self, *args, **options):
        User = get_user_model()
        supers = User.objects.filter(is_superuser=True).order_by("date_joined")
        if not supers.exists():
            self.stdout.write(self.style.WARNING("No hay ningún superusuario. Ejecuta: python manage.py createsuperuser"))
            return
        self.stdout.write(self.style.SUCCESS(f"Superusuarios ({supers.count()}):"))
        for u in supers:
            self.stdout.write(f"  - {u.username} | email: {getattr(u, 'email', '')} | activo: {u.is_active}")
