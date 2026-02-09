from django.db import models
from django.conf import settings


class ATSClient(models.Model):
    """
    Cliente del servicio ATS (Applicant Tracking System).
    Cada cliente que se registra tiene un User y datos de empresa/contacto.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ats_client",
    )
    company_name = models.CharField("Empresa", max_length=200)
    contact_name = models.CharField("Nombre del contacto", max_length=150, blank=True)
    contact_phone = models.CharField("Teléfono", max_length=30, blank=True)
    avatar = models.ImageField("Foto de perfil", upload_to="ats/avatars/%Y/%m/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente ATS"
        verbose_name_plural = "Clientes ATS"

    def __str__(self):
        return f"{self.company_name} ({self.user.email})"


class ATSClientEmailConfig(models.Model):
    """
    Configuración de correo del cliente: notificaciones y correo de la empresa
    (para enviar/recibir como la empresa y recibir respuestas de formularios).
    """
    client = models.OneToOneField(
        ATSClient,
        on_delete=models.CASCADE,
        related_name="email_config",
    )
    # Correo donde recibir notificaciones (formularios, candidatos, y cuando esté activo el análisis de CVs con IA)
    notification_email = models.EmailField(
        "Correo de notificaciones",
        blank=True,
        help_text="Recibirás avisos de formularios, candidatos y, cuando esté activo el análisis de CVs con IA, notificaciones de resultados.",
    )
    # Correo de la empresa (remitente visible; también para envíos cuando se analicen CVs con IA)
    company_from_email = models.EmailField(
        "Correo de envío (empresa)",
        blank=True,
        help_text="Correo con el que se enviarán mensajes a candidatos y, al analizar CVs con IA, comunicaciones desde tu empresa.",
    )
    company_from_name = models.CharField(
        "Nombre del remitente",
        max_length=150,
        blank=True,
        help_text="Nombre que verán los candidatos (ej. Recursos Humanos - Mi Empresa).",
    )
    # Opcional: conectar inbox propio (SMTP) para enviar desde tu servidor
    smtp_host = models.CharField("Servidor SMTP", max_length=255, blank=True)
    smtp_port = models.PositiveIntegerField("Puerto SMTP", null=True, blank=True, default=587)
    smtp_user = models.CharField("Usuario SMTP", max_length=255, blank=True)
    smtp_password_encrypted = models.CharField("Contraseña SMTP (encriptada)", max_length=255, blank=True)
    smtp_use_tls = models.BooleanField("Usar TLS", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de correo ATS"
        verbose_name_plural = "Configuraciones de correo ATS"

    def __str__(self):
        return f"Correo — {self.client.company_name}"


class ATSNotification(models.Model):
    """Notificación in-app para el cliente ATS (campana + opcional email)."""
    TYPE_SUBMISSION = "submission"
    TYPE_CANDIDATE = "candidate"
    TYPE_PLAN = "plan"
    TYPE_CVS_LIMIT = "cvs_limit"
    TYPE_CHOICES = [
        (TYPE_SUBMISSION, "Nuevo envío"),
        (TYPE_CANDIDATE, "Nuevo candidato"),
        (TYPE_PLAN, "Plan actualizado"),
        (TYPE_CVS_LIMIT, "Límite de CVs"),
    ]
    client = models.ForeignKey(
        ATSClient,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField("Tipo", max_length=30, choices=TYPE_CHOICES, default=TYPE_SUBMISSION)
    title = models.CharField("Título", max_length=200)
    message = models.TextField("Mensaje", blank=True)
    link = models.CharField("Enlace", max_length=500, blank=True, help_text="URL a la que lleva la notificación")
    read = models.BooleanField("Leída", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación ATS"
        verbose_name_plural = "Notificaciones ATS"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.client.company_name}"


# --- Planes y facturación ---

class Subscription(models.Model):
    """Suscripción del cliente: plan, límite de CVs, próximo cobro (billing)."""
    PLAN_FREE = "FREE"
    PLAN_PRO = "PRO"
    PLAN_ENTERPRISE = "ENTERPRISE"
    PLAN_CHOICES = [
        (PLAN_FREE, "Gratuito"),
        (PLAN_PRO, "Pro"),
        (PLAN_ENTERPRISE, "Enterprise"),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ats_subscription",
    )
    plan = models.CharField("Plan", max_length=50, choices=PLAN_CHOICES, default=PLAN_FREE)
    cvs_used = models.PositiveIntegerField("CVs usados", default=0)
    cvs_limit = models.PositiveIntegerField("Límite de CVs", default=3)  # FREE=3, PRO=500, etc.
    next_payment_date = models.DateField("Próximo pago", null=True, blank=True)
    amount = models.DecimalField("Monto (MXN)", max_digits=10, decimal_places=2, null=True, blank=True)
    active = models.BooleanField("Activa", default=True)
    paypal_subscription_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Suscripción ATS"
        verbose_name_plural = "Suscripciones ATS"

    def __str__(self):
        return f"{self.user.email} — {self.get_plan_display()}"

    @property
    def can_process_cv(self):
        return self.active and self.cvs_used < self.cvs_limit

    def increment_cvs_used(self):
        self.cvs_used += 1
        self.save(update_fields=["cvs_used", "updated_at"])


class PlanChangeRequest(models.Model):
    """Solicitud de cambio de plan para que el admin/soporte la vea y active el plan."""
    STATUS_PENDING = "pending"
    STATUS_DONE = "done"
    STATUS_CHOICES = [(STATUS_PENDING, "Pendiente"), (STATUS_DONE, "Atendida")]
    client = models.ForeignKey(
        ATSClient,
        on_delete=models.CASCADE,
        related_name="plan_change_requests",
    )
    from_plan = models.CharField("Plan anterior", max_length=50)
    to_plan = models.CharField("Plan solicitado", max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField("Estado", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        verbose_name = "Solicitud de cambio de plan"
        verbose_name_plural = "Solicitudes de cambio de plan"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client.company_name}: {self.from_plan} → {self.to_plan}"

    def get_from_plan_display(self):
        return dict(Subscription.PLAN_CHOICES).get(self.from_plan, self.from_plan)

    def get_to_plan_display(self):
        return dict(Subscription.PLAN_CHOICES).get(self.to_plan, self.to_plan)


# --- Vacantes (contra las que se evalúa) ---

class Vacancy(models.Model):
    """Vacante o puesto contra el que se evalúan candidatos."""
    client = models.ForeignKey(
        ATSClient,
        on_delete=models.CASCADE,
        related_name="vacancies",
    )
    title = models.CharField("Título", max_length=255)
    description = models.TextField("Descripción", blank=True)
    # Perfil e instrucciones para el análisis de CV con IA (qué buscar en el candidato)
    profile_for_analysis = models.TextField(
        "Perfil para análisis con IA",
        blank=True,
        help_text="Descripción del perfil buscado: requisitos, experiencia deseada, qué debe evaluar la IA en el CV.",
    )
    desired_skills = models.JSONField(
        "Habilidades deseadas",
        default=list,
        blank=True,
        help_text="Lista de habilidades o competencias a buscar (ej. Python, Inglés B2, liderazgo).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vacante"
        verbose_name_plural = "Vacantes"

    def __str__(self):
        return f"{self.title} ({self.client.company_name})"


class CVAnalysisConfig(models.Model):
    """
    Configuración por defecto del análisis de CV con IA para un cliente.
    Se usa cuando se analiza un candidato sin vacante asociada, o como complemento.
    """
    client = models.OneToOneField(
        ATSClient,
        on_delete=models.CASCADE,
        related_name="cv_analysis_config",
    )
    default_profile = models.TextField(
        "Perfil por defecto para análisis",
        blank=True,
        help_text="Qué perfil buscar en los CV cuando no hay vacante asociada (ej. experiencia general, habilidades clave).",
    )
    default_desired_skills = models.JSONField(
        "Habilidades deseadas por defecto",
        default=list,
        blank=True,
        help_text="Lista de habilidades a evaluar cuando no hay vacante (ej. Comunicación, Excel).",
    )
    analysis_instructions = models.TextField(
        "Instrucciones adicionales para la IA",
        blank=True,
        help_text="Criterios extra o cómo debe interpretar la IA el CV (opcional).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración análisis CV"
        verbose_name_plural = "Configuraciones análisis CV"

    def __str__(self):
        return f"Análisis CV — {self.client.company_name}"


# --- Candidatos y evaluación por IA ---

class Candidate(models.Model):
    """Candidato analizado por el ATS (score, estado, explicación LLM)."""
    STATUS_APTO = "APTO"
    STATUS_REVISION = "REVISION"
    STATUS_NO_APTO = "NO_APTO"
    STATUS_CHOICES = [
        (STATUS_APTO, "Apto"),
        (STATUS_REVISION, "En revisión"),
        (STATUS_NO_APTO, "No apto"),
    ]
    client = models.ForeignKey(
        ATSClient,
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidates",
    )
    name = models.CharField("Nombre", max_length=255)
    email = models.EmailField("Email", blank=True)
    score = models.FloatField("Score general (0-100)", default=0)
    status = models.CharField(
        "Estado",
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_REVISION,
    )
    match_percentage = models.FloatField("Coincidencia con vacante (%)", null=True, blank=True)
    analysis_date = models.DateTimeField("Fecha de análisis", auto_now_add=True)
    explanation_text = models.TextField(
        "Explicación (generada por LLM)",
        blank=True,
        help_text="Por qué es apto / no apto en lenguaje humano.",
    )
    cv_file = models.FileField("Archivo CV", upload_to="ats/cvs/%Y/%m/", blank=True, null=True)
    raw_text = models.TextField("Texto extraído del CV (OCR)", blank=True)

    class Meta:
        verbose_name = "Candidato"
        verbose_name_plural = "Candidatos"
        ordering = ["-analysis_date"]

    def __str__(self):
        return f"{self.name} — {self.get_status_display()} ({self.score}%)"


class SkillEvaluation(models.Model):
    """Habilidad evaluada por LLM para un candidato (nivel y coincidencia)."""
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="skill_evaluations",
    )
    skill = models.CharField("Habilidad", max_length=100)
    level = models.PositiveSmallIntegerField(
        "Nivel (0-100)",
        default=0,
        help_text="0-100, generado por LLM.",
    )
    match_percentage = models.FloatField(
        "Coincidencia con vacante (%)",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Evaluación de habilidad"
        verbose_name_plural = "Evaluaciones de habilidades"
        ordering = ["-level"]

    def __str__(self):
        return f"{self.candidate.name} — {self.skill} ({self.level}%)"


class LLMUsageLog(models.Model):
    """
    Registro de uso de IA por análisis de CV: tokens consumidos por cliente/candidato.
    Permite ver consumo desde el admin ATS y opcionalmente trazar en LangSmith.
    """
    client = models.ForeignKey(
        ATSClient,
        on_delete=models.CASCADE,
        related_name="llm_usage_logs",
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="llm_usage_logs",
    )
    prompt_tokens = models.PositiveIntegerField("Tokens entrada", default=0)
    completion_tokens = models.PositiveIntegerField("Tokens salida", default=0)
    total_tokens = models.PositiveIntegerField("Total tokens", default=0)
    model = models.CharField("Modelo", max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Uso IA (tokens)"
        verbose_name_plural = "Uso IA (tokens)"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client.company_name} — {self.total_tokens} tokens ({self.created_at.date()})"


# --- Formularios (crear, enviar, recibir respuestas) ---

class ATSForm(models.Model):
    """Formulario que el cliente crea para enviar a candidatos y recibir postulaciones."""
    client = models.ForeignKey(
        ATSClient,
        on_delete=models.CASCADE,
        related_name="ats_forms",
    )
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ats_forms",
        help_text="Vacante asociada (opcional).",
    )
    name = models.CharField("Nombre del formulario", max_length=200)
    slug = models.SlugField("Slug", max_length=100, blank=True)
    description = models.TextField("Descripción (instrucciones para el candidato)", blank=True)
    is_active = models.BooleanField("Activo", default=True)
    request_cv = models.BooleanField(
        "Solicitar CV",
        default=False,
        help_text="Si está activo, el formulario público incluirá un campo para subir CV (PDF/DOC).",
    )
    request_email = models.BooleanField(
        "Solicitar correo electrónico",
        default=True,
        help_text="Si está activo, el formulario incluirá un campo de correo (o usará el que ya tengas).",
    )
    LAYOUT_SINGLE = "single"
    LAYOUT_TWO = "two_columns"
    LAYOUT_THREE = "three_columns"
    LAYOUT_CHOICES = [
        (LAYOUT_SINGLE, "Una columna"),
        (LAYOUT_TWO, "Dos columnas"),
        (LAYOUT_THREE, "Tres columnas"),
    ]
    layout = models.CharField(
        "Vista del formulario (grilla)",
        max_length=20,
        choices=LAYOUT_CHOICES,
        default=LAYOUT_SINGLE,
        help_text="Cómo se muestran los campos en el formulario público.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # UUID para enlace público no adivinable
    uuid = models.UUIDField(unique=True, editable=False, null=True, blank=True)

    class Meta:
        verbose_name = "Formulario ATS"
        verbose_name_plural = "Formularios ATS"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["client", "slug"], name="unique_client_form_slug"),
        ]

    def __str__(self):
        return f"{self.name} ({self.client.company_name})"

    def save(self, *args, **kwargs):
        if not self.uuid:
            import uuid as uuid_lib
            self.uuid = uuid_lib.uuid4()
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.name) or "form"
            self.slug = base
            for i in range(100):
                if not ATSForm.objects.filter(client=self.client, slug=self.slug).exclude(pk=self.pk).exists():
                    break
                self.slug = f"{base}-{i+1}"
        super().save(*args, **kwargs)


class ATSFormField(models.Model):
    """Campo de un formulario ATS (nombre, email, teléfono, texto, archivo, etc.)."""
    FIELD_TEXT = "text"
    FIELD_EMAIL = "email"
    FIELD_PHONE = "phone"
    FIELD_TEXTAREA = "textarea"
    FIELD_FILE = "file"
    FIELD_CHOICES = [
        (FIELD_TEXT, "Texto corto"),
        (FIELD_EMAIL, "Correo electrónico"),
        (FIELD_PHONE, "Teléfono"),
        (FIELD_TEXTAREA, "Texto largo (párrafo)"),
        (FIELD_FILE, "Archivo (CV/PDF)"),
    ]
    form = models.ForeignKey(
        ATSForm,
        on_delete=models.CASCADE,
        related_name="fields",
    )
    label = models.CharField("Etiqueta", max_length=200)
    field_type = models.CharField("Tipo", max_length=20, choices=FIELD_CHOICES, default=FIELD_TEXT)
    required = models.BooleanField("Obligatorio", default=True)
    order = models.PositiveSmallIntegerField("Orden", default=0)
    placeholder = models.CharField("Placeholder", max_length=200, blank=True)

    class Meta:
        verbose_name = "Campo de formulario"
        verbose_name_plural = "Campos de formulario"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.form.name} — {self.label}"


class ATSFormSubmission(models.Model):
    """Respuesta enviada por un candidato a un formulario ATS."""
    form = models.ForeignKey(
        ATSForm,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_submissions",
    )
    # Datos enviados: {"field_label_or_id": "value", ...}; archivos por FieldFile ref o path
    payload = models.JSONField("Datos enviados", default=dict)
    submitter_email = models.EmailField("Correo del remitente", blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Envío de formulario"
        verbose_name_plural = "Envíos de formularios"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.form.name} — {self.submitter_email or 'Anónimo'} ({self.submitted_at.date()})"


class ATSFormSubmissionFile(models.Model):
    """Archivo adjunto en un envío de formulario (ej. CV subido por el candidato)."""
    submission = models.ForeignKey(
        ATSFormSubmission,
        on_delete=models.CASCADE,
        related_name="files",
    )
    form_field = models.ForeignKey(
        ATSFormField,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="submission_files",
    )
    file = models.FileField("Archivo", upload_to="ats/form_uploads/%Y/%m/")
    original_name = models.CharField("Nombre original", max_length=255, blank=True)

    class Meta:
        verbose_name = "Archivo de envío"
        verbose_name_plural = "Archivos de envíos"


class ATSFormCriterion(models.Model):
    """Criterio de evaluación manual del formulario (ej. 'Experiencia en Python', 'Inglés B2')."""
    form = models.ForeignKey(
        ATSForm,
        on_delete=models.CASCADE,
        related_name="criteria",
    )
    label = models.CharField("Etiqueta / Criterio", max_length=200)
    order = models.PositiveSmallIntegerField("Orden", default=0)

    class Meta:
        verbose_name = "Criterio de evaluación"
        verbose_name_plural = "Criterios de evaluación"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.form.name} — {self.label}"


class ATSCandidateCriterionResponse(models.Model):
    """Respuesta manual: si el candidato cumple o no cumple cada criterio (para calcular score)."""
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="criterion_responses",
    )
    criterion = models.ForeignKey(
        ATSFormCriterion,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    cumple = models.BooleanField("Cumple", default=False)

    class Meta:
        verbose_name = "Respuesta a criterio"
        verbose_name_plural = "Respuestas a criterios"
        unique_together = [["candidate", "criterion"]]

    def __str__(self):
        return f"{self.candidate.name} — {self.criterion.label}: {'Cumple' if self.cumple else 'No cumple'}"
