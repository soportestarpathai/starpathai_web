"""
Tests para vistas ATS: acceso, permisos, flujos cliente y admin.
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from mi_app.models import ATSClient, ATSForm, ATSFormField, ATSFormSubmission, Candidate, Subscription, Vacancy
from mi_app.views.orbita.forms import ATSVacancyForm

User = get_user_model()


class ATSPlataformaAccessTests(TestCase):
    """Login, registro, recuperar contraseña y redirect según rol."""

    def setUp(self):
        self.client = Client()

    def test_plataforma_returns_200(self):
        response = self.client.get(reverse("orbita_plataforma"))
        self.assertEqual(response.status_code, 200)

    def test_login_redirects_staff_to_admin_dashboard(self):
        user = User.objects.create_user(username="soporte@test.com", email="soporte@test.com", password="testpass123", is_staff=True)
        response = self.client.post(reverse("orbita_login"), {"username": "soporte@test.com", "password": "testpass123"}, follow=True)
        self.assertRedirects(response, reverse("orbita_admin_dashboard"))

    def test_login_redirects_client_to_dashboard(self):
        user = User.objects.create_user(username="cliente@test.com", email="cliente@test.com", password="testpass123", is_staff=False)
        ATSClient.objects.create(user=user, company_name="Test SA", contact_name="Juan")
        response = self.client.post(reverse("orbita_login"), {"username": "cliente@test.com", "password": "testpass123"}, follow=True)
        self.assertRedirects(response, reverse("orbita_dashboard"))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("orbita_dashboard"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.redirect_chain) >= 1)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_admin_dashboard_returns_403_for_non_staff(self):
        user = User.objects.create_user(username="user@test.com", email="user@test.com", password="testpass123", is_staff=False)
        self.client.force_login(user)
        response = self.client.get(reverse("orbita_admin_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_returns_200_for_staff(self):
        user = User.objects.create_user(username="admin@test.com", email="admin@test.com", password="testpass123", is_staff=True)
        self.client.force_login(user)
        response = self.client.get(reverse("orbita_admin_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_form_returns_200(self):
        response = self.client.get(reverse("orbita_password_reset"))
        self.assertEqual(response.status_code, 200)


class ATSFormPublicTests(TestCase):
    """Formulario público: GET y thanks."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="c@test.com", email="c@test.com", password="x")
        self.ats_client = ATSClient.objects.create(user=self.user, company_name="Test", contact_name="C")
        self.ats_form = ATSForm.objects.create(client=self.ats_client, name="Form Test", is_active=True)

    def test_form_public_get_returns_200_for_active_form(self):
        url = reverse("orbita_form_public", args=[self.ats_form.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_form_public_thanks_returns_200(self):
        url = reverse("orbita_form_public_thanks", args=[self.ats_form.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_form_public_returns_404_for_inactive_form(self):
        self.ats_form.is_active = False
        self.ats_form.save()
        url = reverse("orbita_form_public", args=[self.ats_form.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ATSNotificationPanelTests(TestCase):
    """Panel de notificaciones requiere cliente ATS."""

    def setUp(self):
        self.client = Client()

    def test_notification_panel_requires_login(self):
        response = self.client.get(reverse("orbita_notification_panel"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.redirect_chain) > 0 or not response.context.get("notifications") is None)


class ATSVacancyFormTests(TestCase):
    """Validaciones de vacantes visibles para usuarios en español."""

    def test_required_title_error_is_spanish(self):
        form = ATSVacancyForm(data={"title": ""})

        self.assertFalse(form.is_valid())
        self.assertIn("El título del puesto es obligatorio.", form.errors["title"])


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ATSFormBuilderTests(TestCase):
    """Validaciones y renderizado del constructor de formularios."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="forms@test.com", email="forms@test.com", password="testpass123")
        self.ats_client = ATSClient.objects.create(user=self.user, company_name="Cliente Forms")
        Subscription.objects.create(user=self.user)
        self.client.force_login(self.user)

    def test_create_form_required_name_error_is_spanish(self):
        response = self.client.post(reverse("orbita_form_create"), {"name": "", "layout": "single"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El nombre del formulario es obligatorio.")
        self.assertNotContains(response, "This field is required")

    def test_edit_form_does_not_render_default_blank_field_row(self):
        orbita_form = ATSForm.objects.create(client=self.ats_client, name="Formulario")
        response = self.client.get(reverse("orbita_form_edit", args=[orbita_form.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["formset"].total_form_count(), 0)

    def test_public_form_uses_layout_and_order_starting_at_zero(self):
        orbita_form = ATSForm.objects.create(client=self.ats_client, name="Formulario", layout=ATSForm.LAYOUT_TWO)
        second = ATSFormField.objects.create(form=orbita_form, label="Segundo", order=1)
        first = ATSFormField.objects.create(form=orbita_form, label="Primero", order=0)

        response = self.client.get(reverse("orbita_form_public", args=[orbita_form.uuid]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form-fields-grid layout-two_columns")
        content = response.content.decode("utf-8")
        self.assertLess(content.index(first.label), content.index(second.label))

    def test_submissions_display_payload_in_field_order_without_file_labels(self):
        orbita_form = ATSForm.objects.create(client=self.ats_client, name="Formulario")
        ATSFormField.objects.create(form=orbita_form, label="Nombre", order=0)
        ATSFormField.objects.create(form=orbita_form, label="Sube tu CV", field_type=ATSFormField.FIELD_FILE, order=1)
        ATSFormField.objects.create(form=orbita_form, label="Correo electrónico", field_type=ATSFormField.FIELD_EMAIL, order=2)
        ATSFormSubmission.objects.create(
            form=orbita_form,
            submitter_email="correo@test.com",
            payload={
                "CV": "cv.pdf",
                "Correo electrónico": "correo@test.com",
                "Sube tu CV": "cv.pdf",
                "Nombre": "Ana",
            },
        )

        response = self.client.get(reverse("orbita_form_submissions", args=[orbita_form.pk]))

        self.assertEqual(response.status_code, 200)
        submission = response.context["submissions"][0]
        self.assertEqual(
            submission.display_payload_items,
            [
                {"label": "Nombre", "value": "Ana"},
                {"label": "Correo electrónico", "value": "correo@test.com"},
            ],
        )
        self.assertNotContains(response, "<label>CV</label>", html=True)
        self.assertNotContains(response, "<label>Sube tu CV</label>", html=True)

    def test_account_front_hides_plan_change_ui(self):
        response = self.client.get(reverse("orbita_dashboard") + "?section=cuenta")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Cambiar de plan")
        self.assertNotContains(response, "Plan actual")
        self.assertNotContains(response, "Elegir este plan")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ATSDashboardFilterAccessTests(TestCase):
    """El dashboard no debe exponer IDs internos ni romperse con parámetros manipulados."""

    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username="dash-a@test.com", email="dash-a@test.com", password="testpass123")
        self.user_b = User.objects.create_user(username="dash-b@test.com", email="dash-b@test.com", password="testpass123")
        self.ats_a = ATSClient.objects.create(user=self.user_a, company_name="Cliente A")
        self.ats_b = ATSClient.objects.create(user=self.user_b, company_name="Cliente B")
        Subscription.objects.create(user=self.user_a)
        Subscription.objects.create(user=self.user_b)
        self.vacancy_a = Vacancy.objects.create(client=self.ats_a, title="Vacante A")
        self.vacancy_b = Vacancy.objects.create(client=self.ats_b, title="Vacante B")
        self.candidate_a = Candidate.objects.create(client=self.ats_a, vacancy=self.vacancy_a, name="Candidato A")

    def test_invalid_dashboard_section_redirects_to_candidates(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("orbita_dashboard") + "?section=admin&vacancy=10")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("orbita_dashboard") + "?section=candidatos")

    def test_numeric_vacancy_filter_is_removed_from_url(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("orbita_dashboard") + "?section=candidatos&q=&status=&vacancy=11")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("orbita_dashboard") + "?section=candidatos&q=&status=")

    def test_vacancy_filter_uses_public_uuid(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("orbita_dashboard") + f"?section=candidatos&vacancy={self.vacancy_a.public_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_vacancy"], self.vacancy_a)
        self.assertEqual(response.context["filter_vacancy"], str(self.vacancy_a.public_id))

    def test_other_client_vacancy_uuid_is_ignored(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("orbita_dashboard") + f"?section=candidatos&vacancy={self.vacancy_b.public_id}")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["selected_vacancy"])
        self.assertEqual(response.context["filter_vacancy"], "")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class ATSCandidateAccessTests(TestCase):
    """Los candidatos no deben ser enumerables ni accesibles entre clientes."""

    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username="a@test.com", email="a@test.com", password="testpass123")
        self.user_b = User.objects.create_user(username="b@test.com", email="b@test.com", password="testpass123")
        self.ats_a = ATSClient.objects.create(user=self.user_a, company_name="Cliente A")
        self.ats_b = ATSClient.objects.create(user=self.user_b, company_name="Cliente B")
        Subscription.objects.create(user=self.user_a)
        Subscription.objects.create(user=self.user_b)
        self.candidate_a = Candidate.objects.create(client=self.ats_a, name="Candidato A")
        self.candidate_b = Candidate.objects.create(client=self.ats_b, name="Candidato B")

    def test_candidate_url_uses_public_uuid(self):
        self.client.force_login(self.user_a)
        url = reverse("orbita_candidate_detail", args=[self.candidate_a.public_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_client_cannot_access_other_client_candidate_uuid(self):
        self.client.force_login(self.user_a)
        url = reverse("orbita_candidate_detail", args=[self.candidate_b.public_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("orbita_dashboard"), response["Location"])

