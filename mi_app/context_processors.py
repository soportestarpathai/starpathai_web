"""Context processors para el proyecto."""


def ats_notifications(request):
    """Añade notificaciones (clientes o admin) y contadores al contexto en páginas ATS."""
    if not request.user.is_authenticated:
        return {}
    if not request.path.startswith("/ats/plataforma/"):
        return {}
    ats_client = getattr(request.user, "ats_client", None)
    if ats_client:
        from mi_app.models import ATSNotification
        notifications = list(ATSNotification.objects.filter(client=ats_client)[:10])
        unread_count = ATSNotification.objects.filter(client=ats_client, read=False).count()
        return {
            "ats_notifications": notifications,
            "ats_unread_count": unread_count,
        }
    if request.user.is_staff:
        from mi_app.models import PlanChangeRequest
        plan_requests = list(
            PlanChangeRequest.objects.filter(status=PlanChangeRequest.STATUS_PENDING)
            .select_related("client")
            .order_by("-created_at")[:10]
        )
        admin_count = PlanChangeRequest.objects.filter(status=PlanChangeRequest.STATUS_PENDING).count()
        return {
            "ats_admin_notifications": plan_requests,
            "ats_admin_unread_count": admin_count,
        }
    return {}
