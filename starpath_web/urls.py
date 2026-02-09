"""
URL configuration for starpath_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from mi_app.views.landing_page.landing_page_views import LandingPage
from mi_app.views.chatbot.chatbot_api import ChatAPIView
from mi_app.views.chatbot.services.kb_api import KBItemAPIView
from mi_app.views.ats.ats_views import (
    ATSProductoView,
    ATSPlataformaView,
    ATSRegisterView,
    ATSLoginView,
    ATSLogoutView,
    ATSPasswordResetView,
    ATSPasswordResetDoneView,
    ATSPasswordResetConfirmView,
    ATSPasswordResetCompleteView,
    ATSDashboardView,
    ATSCandidateDetailView,
    ATSCandidateUploadCVView,
    ATSCandidateAnalyzeCVView,
    ATSCandidateSendEmailView,
    ATSCandidateExportView,
    ATSFormListView,
    ATSFormCreateView,
    ATSFormEditView,
    ATSFormDeleteView,
    ATSFormSubmissionsView,
    ATSFormPublicView,
    ATSFormPublicThanksView,
    ATSEmailConfigView,
    ATSChangePlanView,
    ATSRequestAccountDeletionView,
    ATSProfileConfigView,
    ATSVacancyCreateView,
    ATSVacancyEditView,
    ATSVacancyDeleteView,
    ATSCVAnalysisConfigView,
    ATSBackfillCandidatesFromSubmissionsView,
    ATSNotificationGoView,
    ATSNotificationMarkAllReadView,
    ATSNotificationPanelView,
    ATSAdminDashboardView,
    ATSAdminChangePlanView,
    ATSStaffAccountView,
    ATSPasswordChangeView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", LandingPage.as_view(), name="home"),
    path("ats/", ATSProductoView.as_view(), name="ats_producto"),
    path("ats/plataforma/", ATSPlataformaView.as_view(), name="ats_plataforma"),
    path("ats/plataforma/register/", ATSRegisterView.as_view(), name="ats_register"),
    path("ats/plataforma/login/", ATSLoginView.as_view(), name="ats_login"),
    path("ats/plataforma/recuperar-password/", ATSPasswordResetView.as_view(), name="ats_password_reset"),
    path("ats/plataforma/recuperar-password/enviado/", ATSPasswordResetDoneView.as_view(), name="ats_password_reset_done"),
    path("ats/plataforma/recuperar-password/restablecer/<uidb64>/<token>/", ATSPasswordResetConfirmView.as_view(), name="ats_password_reset_confirm"),
    path("ats/plataforma/recuperar-password/listo/", ATSPasswordResetCompleteView.as_view(), name="ats_password_reset_complete"),
    path("ats/plataforma/logout/", ATSLogoutView.as_view(), name="ats_logout"),
    path("ats/plataforma/dashboard/", ATSDashboardView.as_view(), name="ats_dashboard"),
    path("ats/plataforma/dashboard/candidato/<int:pk>/", ATSCandidateDetailView.as_view(), name="ats_candidate_detail"),
    path("ats/plataforma/dashboard/candidato/<int:pk>/subir-cv/", ATSCandidateUploadCVView.as_view(), name="ats_candidate_upload_cv"),
    path("ats/plataforma/dashboard/candidato/<int:pk>/analizar-cv/", ATSCandidateAnalyzeCVView.as_view(), name="ats_candidate_analyze_cv"),
    path("ats/plataforma/dashboard/candidato/<int:pk>/enviar-correo/", ATSCandidateSendEmailView.as_view(), name="ats_candidate_send_email"),
    path("ats/plataforma/dashboard/candidatos/exportar/", ATSCandidateExportView.as_view(), name="ats_candidate_export"),
    path("ats/plataforma/dashboard/formularios/", ATSFormListView.as_view(), name="ats_form_list"),
    path("ats/plataforma/dashboard/formularios/nuevo/", ATSFormCreateView.as_view(), name="ats_form_create"),
    path("ats/plataforma/dashboard/formularios/<int:pk>/editar/", ATSFormEditView.as_view(), name="ats_form_edit"),
    path("ats/plataforma/dashboard/formularios/<int:pk>/eliminar/", ATSFormDeleteView.as_view(), name="ats_form_delete"),
    path("ats/plataforma/dashboard/formularios/<int:pk>/envios/", ATSFormSubmissionsView.as_view(), name="ats_form_submissions"),
    path("ats/f/<uuid:uuid>/", ATSFormPublicView.as_view(), name="ats_form_public"),
    path("ats/f/<uuid:uuid>/gracias/", ATSFormPublicThanksView.as_view(), name="ats_form_public_thanks"),
    path("ats/plataforma/dashboard/configuracion/correo/", ATSEmailConfigView.as_view(), name="ats_email_config"),
    path("ats/plataforma/dashboard/cambiar-plan/", ATSChangePlanView.as_view(), name="ats_change_plan"),
    path("ats/plataforma/dashboard/solicitar-baja/", ATSRequestAccountDeletionView.as_view(), name="ats_request_account_deletion"),
    path("ats/plataforma/dashboard/configuracion/cuenta/", ATSProfileConfigView.as_view(), name="ats_profile_config"),
    path("ats/plataforma/dashboard/configuracion/analisis-cv/", ATSCVAnalysisConfigView.as_view(), name="ats_cv_analysis_config"),
    path("ats/plataforma/dashboard/reclutamiento/vacante/nueva/", ATSVacancyCreateView.as_view(), name="ats_vacancy_create"),
    path("ats/plataforma/dashboard/reclutamiento/vacante/<int:pk>/editar/", ATSVacancyEditView.as_view(), name="ats_vacancy_edit"),
    path("ats/plataforma/dashboard/reclutamiento/vacante/<int:pk>/eliminar/", ATSVacancyDeleteView.as_view(), name="ats_vacancy_delete"),
    path("ats/plataforma/dashboard/reclutamiento/crear-candidatos-desde-envios/", ATSBackfillCandidatesFromSubmissionsView.as_view(), name="ats_backfill_candidates_from_submissions"),
    path("ats/plataforma/dashboard/notificaciones/", ATSNotificationPanelView.as_view(), name="ats_notification_panel"),
    path("ats/plataforma/dashboard/notificaciones/<int:pk>/ir/", ATSNotificationGoView.as_view(), name="ats_notification_go"),
    path("ats/plataforma/dashboard/notificaciones/marcar-todas-leidas/", ATSNotificationMarkAllReadView.as_view(), name="ats_notification_mark_all_read"),
    path("ats/plataforma/administracion/", ATSAdminDashboardView.as_view(), name="ats_admin_dashboard"),
    path("ats/plataforma/administracion/cambiar-plan/", ATSAdminChangePlanView.as_view(), name="ats_admin_change_plan"),
    path("ats/plataforma/administracion/mi-cuenta/", ATSStaffAccountView.as_view(), name="ats_staff_account"),
    path("ats/plataforma/administracion/cambiar-password/", ATSPasswordChangeView.as_view(), name="ats_password_change"),
    path("api/chat/", ChatAPIView.as_view(), name="api_chat"),
    path("api/kb/item/<str:item_id>/", KBItemAPIView.as_view(), name="api_kb_item"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
