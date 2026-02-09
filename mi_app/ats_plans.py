"""
Definición de planes ATS: límites de CVs, precios, descripción y diferencias por plan.
Usado en dashboard (cambiar plan), lógica de suscripción y comprobación de capacidades.

Diferencias por plan (vistas, procedimientos, actividades):
- FREE: 3 escaneos IA, formularios, correo, soporte por correo. Sin API ni reportes avanzados.
- PRO: 500 escaneos IA, lo anterior + soporte prioritario. Sin API.
- ENTERPRISE: 2000 escaneos IA, lo anterior + API y reportes (cuando se implementen).
"""
from decimal import Decimal
from datetime import date


def _next_month():
    """Primer día del mes siguiente (para próximo cobro)."""
    d = date.today()
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)


# Plan id debe coincidir con Subscription.PLAN_* del modelo
# candidates_limit y vacancies_limit: número o None (ilimitado). Gratuito: 10 candidatos, 2 vacantes.
PLANS = [
    {
        "id": "FREE",
        "name": "Gratuito",
        "cvs_limit": 3,
        "candidates_limit": 10,
        "vacancies_limit": 2,
        "amount_mxn": Decimal("0"),
        "description": "Prueba el ATS con 10 candidatos (proceso manual) y 2 vacantes. Hasta 3 CVs analizados con IA.",
        "features": ["10 candidatos", "2 vacantes", "3 escaneos IA/mes", "Formularios", "Config. correo", "Soporte por correo"],
    },
    {
        "id": "PRO",
        "name": "Pro",
        "cvs_limit": 500,
        "candidates_limit": None,
        "vacancies_limit": None,
        "amount_mxn": Decimal("999.00"),
        "description": "Candidatos y vacantes ilimitados (proceso manual). Hasta 500 CVs con IA por mes.",
        "features": ["Candidatos ilimitados", "Vacantes ilimitadas", "500 CVs IA/mes", "Evaluación con IA", "Formularios ilimitados", "Correo empresa", "Soporte prioritario"],
    },
    {
        "id": "ENTERPRISE",
        "name": "Enterprise",
        "cvs_limit": 2000,
        "candidates_limit": None,
        "vacancies_limit": None,
        "amount_mxn": Decimal("2499.00"),
        "description": "Para empresas con alto volumen. Candidatos y vacantes ilimitados, 2000 CVs IA/mes.",
        "features": ["Candidatos ilimitados", "Vacantes ilimitadas", "2000 CVs IA/mes", "Todo lo de Pro", "API y reportes", "Soporte dedicado"],
    },
]

# Capacidades por plan: qué puede hacer cada uno (vistas, procedimientos, actividades).
# Añadir aquí nuevas capacidades cuando se implementen (ej. "api", "reportes").
PLAN_CAPABILITIES = {
    "FREE": {
        "cvs_scan": True,
        "forms": True,
        "email_config": True,
        "candidates": True,
        "vacancies": True,
        "support_priority": False,
        "api": False,
        "reportes": False,
        "custom_email_message": False,   # Mensaje personalizado en correo apto/rechazo
        "export_candidates": False,      # Exportar candidatos CSV/Excel
    },
    "PRO": {
        "cvs_scan": True,
        "forms": True,
        "email_config": True,
        "candidates": True,
        "vacancies": True,
        "support_priority": True,
        "api": False,
        "reportes": False,
        "custom_email_message": True,
        "export_candidates": True,
    },
    "ENTERPRISE": {
        "cvs_scan": True,
        "forms": True,
        "email_config": True,
        "candidates": True,
        "vacancies": True,
        "support_priority": True,
        "api": True,
        "reportes": True,
        "custom_email_message": True,
        "export_candidates": True,
    },
}


def plan_can(plan_id, capability):
    """Indica si un plan tiene una capacidad. plan_id ej: 'FREE', 'PRO', 'ENTERPRISE'."""
    caps = PLAN_CAPABILITIES.get(plan_id, {})
    return caps.get(capability, False)


def subscription_can(subscription, capability):
    """
    Indica si la suscripción permite una capacidad.
    Para 'cvs_scan' además comprueba que no haya alcanzado el límite (cvs_used < cvs_limit).
    """
    if not subscription or not subscription.active:
        return False
    if capability == "cvs_scan":
        return plan_can(subscription.plan, "cvs_scan") and subscription.cvs_used < subscription.cvs_limit
    return plan_can(subscription.plan, capability)


def get_plan_capabilities_display(plan_id):
    """Lista de capacidades incluidas en el plan (para mostrar en UI)."""
    caps = PLAN_CAPABILITIES.get(plan_id, {})
    labels = {
        "cvs_scan": "Escaneo de CV con IA",
        "forms": "Formularios de postulación",
        "email_config": "Configuración de correo",
        "candidates": "Gestión de candidatos",
        "vacancies": "Vacantes",
        "support_priority": "Soporte prioritario",
        "api": "API",
        "reportes": "Reportes avanzados",
        "custom_email_message": "Mensaje personalizado en correos al candidato",
        "export_candidates": "Exportar candidatos (CSV/Excel)",
    }
    return [labels[k] for k, v in caps.items() if v and k in labels]


def get_plan_config(plan_id):
    """Devuelve el dict de configuración del plan o None."""
    for p in PLANS:
        if p["id"] == plan_id:
            return p.copy()
    return None


def get_plan_candidates_limit(plan_id):
    """Límite de candidatos del plan (None = ilimitado)."""
    config = get_plan_config(plan_id)
    return config.get("candidates_limit") if config else None


def get_plan_vacancies_limit(plan_id):
    """Límite de vacantes del plan (None = ilimitado)."""
    config = get_plan_config(plan_id)
    return config.get("vacancies_limit") if config else None


def subscription_can_add_candidate(subscription, current_count):
    """True si la suscripción permite añadir más candidatos."""
    if not subscription or not subscription.active:
        return False
    limit = get_plan_candidates_limit(subscription.plan)
    return limit is None or current_count < limit


def subscription_can_add_vacancy(subscription, current_count):
    """True si la suscripción permite añadir más vacantes."""
    if not subscription or not subscription.active:
        return False
    limit = get_plan_vacancies_limit(subscription.plan)
    return limit is None or current_count < limit


def get_all_plans():
    return list(PLANS)


def apply_plan_to_subscription(subscription, plan_id):
    """
    Actualiza la suscripción al cambiar de plan. Hace lo siguiente:

    - plan, cvs_limit, amount: se actualizan según el plan elegido.
    - cvs_used: se ajusta si hace falta. Si al bajar de plan (ej. Pro → Gratuito) el uso
      supera el nuevo límite, se capa a ese límite (ej. 50 usados con límite 3 → cvs_used=3)
      para que el contador sea coherente y no queden “scans extra” al bajar.
    - next_payment_date: en planes de pago se pone el primer día del mes siguiente;
      en Gratuito se pone None.
    - active: se deja en True (el admin puede desactivar aparte).
    - paypal_subscription_id: si se cambia a Gratuito, se limpia para no asociar cobro.
    """
    config = get_plan_config(plan_id)
    if not config:
        return False
    new_limit = config["cvs_limit"]
    subscription.plan = plan_id
    subscription.cvs_limit = new_limit
    subscription.amount = config["amount_mxn"]
    # Ajustar uso al nuevo límite (al bajar de plan, capar; al subir no hace falta)
    capped_usage = subscription.cvs_used > new_limit
    if capped_usage:
        subscription.cvs_used = new_limit
    if config["amount_mxn"] and config["amount_mxn"] > 0:
        subscription.next_payment_date = _next_month()
        subscription.active = True
    else:
        subscription.next_payment_date = None
        subscription.active = True
        subscription.paypal_subscription_id = ""  # Gratuito: sin suscripción PayPal
    update_fields = ["plan", "cvs_limit", "amount", "next_payment_date", "active", "updated_at"]
    if capped_usage:
        update_fields.append("cvs_used")
    if not (config["amount_mxn"] and config["amount_mxn"] > 0):
        update_fields.append("paypal_subscription_id")
    subscription.save(update_fields=update_fields)
    return True
