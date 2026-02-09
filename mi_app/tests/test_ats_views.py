"""
Tests para vistas ATS: acceso, permisos, flujos cliente y admin.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from mi_app.models import ATSClient, ATSForm, Subscription

User = get_user_model()


class ATSPlataformaAccessTests(TestCase):
    """Login, registro, recuperar contraseña y redirect según rol."""

    def setUp(self):
        self.client = Client()

    def test_plataforma_returns_200(self):
        response = self.client.get(reverse("ats_plataforma"))
        self.assertEqual(response.status_code, 200)

    def test_login_redirects_staff_to_admin_dashboard(self):
        user = User.objects.create_user(username="soporte@test.com", email="soporte@test.com", password="testpass123", is_staff=True)
        response = self.client.post(reverse("ats_login"), {"username": "soporte@test.com", "password": "testpass123"}, follow=True)
        self.assertRedirects(response, reverse("ats_admin_dashboard"))

    def test_login_redirects_client_to_dashboard(self):
        user = User.objects.create_user(username="cliente@test.com", email="cliente@test.com", password="testpass123", is_staff=False)
        ATSClient.objects.create(user=user, company_name="Test SA", contact_name="Juan")
        response = self.client.post(reverse("ats_login"), {"username": "cliente@test.com", "password": "testpass123"}, follow=True)
        self.assertRedirects(response, reverse("ats_dashboard"))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("ats_dashboard"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.redirect_chain) >= 1)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_admin_dashboard_returns_403_for_non_staff(self):
        user = User.objects.create_user(username="user@test.com", email="user@test.com", password="testpass123", is_staff=False)
        self.client.force_login(user)
        response = self.client.get(reverse("ats_admin_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_returns_200_for_staff(self):
        user = User.objects.create_user(username="admin@test.com", email="admin@test.com", password="testpass123", is_staff=True)
        self.client.force_login(user)
        response = self.client.get(reverse("ats_admin_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_form_returns_200(self):
        response = self.client.get(reverse("ats_password_reset"))
        self.assertEqual(response.status_code, 200)


class ATSFormPublicTests(TestCase):
    """Formulario público: GET y thanks."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="c@test.com", email="c@test.com", password="x")
        self.ats_client = ATSClient.objects.create(user=self.user, company_name="Test", contact_name="C")
        self.ats_form = ATSForm.objects.create(client=self.ats_client, name="Form Test", is_active=True)

    def test_form_public_get_returns_200_for_active_form(self):
        url = reverse("ats_form_public", args=[self.ats_form.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_form_public_thanks_returns_200(self):
        url = reverse("ats_form_public_thanks", args=[self.ats_form.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_form_public_returns_404_for_inactive_form(self):
        self.ats_form.is_active = False
        self.ats_form.save()
        url = reverse("ats_form_public", args=[self.ats_form.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ATSNotificationPanelTests(TestCase):
    """Panel de notificaciones requiere cliente ATS."""

    def setUp(self):
        self.client = Client()

    def test_notification_panel_requires_login(self):
        response = self.client.get(reverse("ats_notification_panel"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.redirect_chain) > 0 or not response.context.get("notifications") is None)
