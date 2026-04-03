from .create_orbita_admin import Command as OrbitaAdminCommand


class Command(OrbitaAdminCommand):
    """
    Comando legacy mantenido por compatibilidad.
    Usa `python manage.py create_orbita_admin`.
    """

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "create_ats_admin está deprecado. Usa create_orbita_admin."
            )
        )
        return super().handle(*args, **options)
