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
from django.views.generic.base import RedirectView
from mi_app.views.landing_page.landing_page_views import LandingPage
from mi_app.views.chatbot.chatbot_api import ChatAPIView
from mi_app.views.documents.document_extract_api import DocumentExtractAPIView
from mi_app.views.chatbot.services.kb_api import KBItemAPIView
from mi_app.views.orbita.form_chat_views import (
    FormChatPageView,
    FormChatStartAPI,
    FormChatAnswerAPI,
    FormChatFileUploadAPI,
    FormChatSessionsView,
    FormChatSessionsListAPI,
    FormChatSessionDeleteAPI,
    FormChatSessionDetailAPI,
    CandidateChatSessionAPI,
)
from mi_app.views.orbita.orbita_views import (
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
    ATSCandidateDeleteView,
    ATSFormListView,
    ATSFormCreateView,
    ATSFormEditView,
    ATSFormDeleteView,
    ATSFormSubmissionsView,
    ATSFormSubmissionDeleteView,
    ATSFormSubmissionDeleteAllView,
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
    ATSAdminSetLangSmithView,
    ATSAdminDeleteClientView,
    ATSAdminSendNotificationView,
    ATSAdminNotificationsView,
    ATSAdminMarkRequestDoneView,
    ATSStaffAccountView,
    ATSPasswordChangeView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "img/favicon.png", permanent=False)),
    path("", LandingPage.as_view(), name="home"),
    path("orbita/", ATSProductoView.as_view(), name="orbita_producto"),
    path("orbita/plataforma/", ATSPlataformaView.as_view(), name="orbita_plataforma"),
    path("orbita/plataforma/register/", ATSRegisterView.as_view(), name="orbita_register"),
    path("orbita/plataforma/login/", ATSLoginView.as_view(), name="orbita_login"),
    path("orbita/plataforma/recuperar-password/", ATSPasswordResetView.as_view(), name="orbita_password_reset"),
    path("orbita/plataforma/recuperar-password/enviado/", ATSPasswordResetDoneView.as_view(), name="orbita_password_reset_done"),
    path("orbita/plataforma/recuperar-password/restablecer/<uidb64>/<token>/", ATSPasswordResetConfirmView.as_view(), name="orbita_password_reset_confirm"),
    path("orbita/plataforma/recuperar-password/listo/", ATSPasswordResetCompleteView.as_view(), name="orbita_password_reset_complete"),
    path("orbita/plataforma/logout/", ATSLogoutView.as_view(), name="orbita_logout"),
    path("orbita/plataforma/dashboard/", ATSDashboardView.as_view(), name="orbita_dashboard"),
    path("orbita/plataforma/dashboard/candidato/<int:pk>/", ATSCandidateDetailView.as_view(), name="orbita_candidate_detail"),
    path("orbita/plataforma/dashboard/candidato/<int:pk>/subir-cv/", ATSCandidateUploadCVView.as_view(), name="orbita_candidate_upload_cv"),
    path("orbita/plataforma/dashboard/candidato/<int:pk>/analizar-cv/", ATSCandidateAnalyzeCVView.as_view(), name="orbita_candidate_analyze_cv"),
    path("orbita/plataforma/dashboard/candidato/<int:pk>/enviar-correo/", ATSCandidateSendEmailView.as_view(), name="orbita_candidate_send_email"),
    path("orbita/plataforma/dashboard/candidato/<int:pk>/eliminar/", ATSCandidateDeleteView.as_view(), name="orbita_candidate_delete"),
    path("orbita/plataforma/dashboard/candidatos/exportar/", ATSCandidateExportView.as_view(), name="orbita_candidate_export"),
    path("orbita/plataforma/dashboard/formularios/", ATSFormListView.as_view(), name="orbita_form_list"),
    path("orbita/plataforma/dashboard/formularios/nuevo/", ATSFormCreateView.as_view(), name="orbita_form_create"),
    path("orbita/plataforma/dashboard/formularios/<int:pk>/editar/", ATSFormEditView.as_view(), name="orbita_form_edit"),
    path("orbita/plataforma/dashboard/formularios/<int:pk>/eliminar/", ATSFormDeleteView.as_view(), name="orbita_form_delete"),
    path("orbita/plataforma/dashboard/formularios/<int:pk>/envios/", ATSFormSubmissionsView.as_view(), name="orbita_form_submissions"),
    path("orbita/plataforma/dashboard/formularios/<int:pk>/envios/<int:sub_pk>/eliminar/", ATSFormSubmissionDeleteView.as_view(), name="orbita_form_submission_delete"),
    path("orbita/plataforma/dashboard/formularios/<int:pk>/envios/eliminar-todos/", ATSFormSubmissionDeleteAllView.as_view(), name="orbita_form_submission_delete_all"),
    path("orbita/f/<uuid:uuid>/", ATSFormPublicView.as_view(), name="orbita_form_public"),
    path("orbita/f/<uuid:uuid>/gracias/", ATSFormPublicThanksView.as_view(), name="orbita_form_public_thanks"),
    path("orbita/chat/<uuid:uuid>/", FormChatPageView.as_view(), name="orbita_form_chat"),
    path("orbita/chat/<uuid:uuid>/api/start/", FormChatStartAPI.as_view(), name="orbita_form_chat_start"),
    path("orbita/chat/<uuid:uuid>/api/answer/", FormChatAnswerAPI.as_view(), name="orbita_form_chat_answer"),
    path("orbita/chat/<uuid:uuid>/api/upload/", FormChatFileUploadAPI.as_view(), name="orbita_form_chat_upload"),
    path("orbita/plataforma/dashboard/formularios/<int:pk>/chat-sessions/", FormChatSessionsView.as_view(), name="orbita_form_chat_sessions"),
    path("orbita/plataforma/dashboard/formularios/<int:pk>/chat-sessions/api/list/", FormChatSessionsListAPI.as_view(), name="orbita_form_chat_sessions_list_api"),
    path("orbita/plataforma/dashboard/formularios/<int:pk>/chat-sessions/<uuid:session_uuid>/api/", FormChatSessionDetailAPI.as_view(), name="orbita_form_chat_session_detail"),
    path("orbita/plataforma/dashboard/formularios/<int:pk>/chat-sessions/<uuid:session_uuid>/delete/", FormChatSessionDeleteAPI.as_view(), name="orbita_form_chat_session_delete"),
    path("orbita/plataforma/dashboard/chat-session/<uuid:session_uuid>/api/", CandidateChatSessionAPI.as_view(), name="orbita_candidate_chat_session_api"),
    path("orbita/plataforma/dashboard/configuracion/correo/", ATSEmailConfigView.as_view(), name="orbita_email_config"),
    path("orbita/plataforma/dashboard/cambiar-plan/", ATSChangePlanView.as_view(), name="orbita_change_plan"),
    path("orbita/plataforma/dashboard/solicitar-baja/", ATSRequestAccountDeletionView.as_view(), name="orbita_request_account_deletion"),
    path("orbita/plataforma/dashboard/configuracion/cuenta/", ATSProfileConfigView.as_view(), name="orbita_profile_config"),
    path("orbita/plataforma/dashboard/configuracion/analisis-cv/", ATSCVAnalysisConfigView.as_view(), name="orbita_cv_analysis_config"),
    path("orbita/plataforma/dashboard/reclutamiento/vacante/nueva/", ATSVacancyCreateView.as_view(), name="orbita_vacancy_create"),
    path("orbita/plataforma/dashboard/reclutamiento/vacante/<int:pk>/editar/", ATSVacancyEditView.as_view(), name="orbita_vacancy_edit"),
    path("orbita/plataforma/dashboard/reclutamiento/vacante/<int:pk>/eliminar/", ATSVacancyDeleteView.as_view(), name="orbita_vacancy_delete"),
    path("orbita/plataforma/dashboard/reclutamiento/crear-candidatos-desde-envios/", ATSBackfillCandidatesFromSubmissionsView.as_view(), name="orbita_backfill_candidates_from_submissions"),
    path("orbita/plataforma/dashboard/notificaciones/", ATSNotificationPanelView.as_view(), name="orbita_notification_panel"),
    path("orbita/plataforma/dashboard/notificaciones/<int:pk>/ir/", ATSNotificationGoView.as_view(), name="orbita_notification_go"),
    path("orbita/plataforma/dashboard/notificaciones/marcar-todas-leidas/", ATSNotificationMarkAllReadView.as_view(), name="orbita_notification_mark_all_read"),
    path("orbita/plataforma/administracion/", ATSAdminDashboardView.as_view(), name="orbita_admin_dashboard"),
    path("orbita/plataforma/administracion/cambiar-plan/", ATSAdminChangePlanView.as_view(), name="orbita_admin_change_plan"),
    path("orbita/plataforma/administracion/langsmith-cliente/", ATSAdminSetLangSmithView.as_view(), name="orbita_admin_set_langsmith"),
    path("orbita/plataforma/administracion/eliminar-cliente/", ATSAdminDeleteClientView.as_view(), name="orbita_admin_delete_client"),
    path("orbita/plataforma/administracion/enviar-notificacion/", ATSAdminSendNotificationView.as_view(), name="orbita_admin_send_notification"),
    path("orbita/plataforma/administracion/notificaciones/", ATSAdminNotificationsView.as_view(), name="orbita_admin_notifications"),
    path("orbita/plataforma/administracion/solicitud-atendida/", ATSAdminMarkRequestDoneView.as_view(), name="orbita_admin_mark_request_done"),
    path("orbita/plataforma/administracion/mi-cuenta/", ATSStaffAccountView.as_view(), name="orbita_staff_account"),
    path("orbita/plataforma/administracion/cambiar-password/", ATSPasswordChangeView.as_view(), name="orbita_password_change"),
    path("api/chat/", ChatAPIView.as_view(), name="api_chat"),
    path("api/kb/item/<str:item_id>/", KBItemAPIView.as_view(), name="api_kb_item"),
    path("api/documents/extract/", DocumentExtractAPIView.as_view(), name="api_documents_extract"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



