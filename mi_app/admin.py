from django.contrib import admin
from .models import (
    ATSClient,
    ATSClientEmailConfig,
    ATSNotification,
    PlanChangeRequest,
    Subscription,
    Vacancy,
    CVAnalysisConfig,
    Candidate,
    SkillEvaluation,
    LLMUsageLog,
    ATSForm,
    ATSFormField,
    ATSFormSubmission,
    ATSFormSubmissionFile,
)


@admin.register(ATSClient)
class ATSClientAdmin(admin.ModelAdmin):
    list_display = ("company_name", "user", "subscription_plan", "subscription_usage", "contact_name", "contact_phone", "created_at")
    search_fields = ("company_name", "contact_name", "user__email")
    list_filter = ("created_at",)

    @admin.display(description="Plan")
    def subscription_plan(self, obj):
        sub = getattr(obj.user, "ats_subscription", None)
        if not sub:
            return "—"
        return f"{sub.get_plan_display()}"

    @admin.display(description="CVs")
    def subscription_usage(self, obj):
        sub = getattr(obj.user, "ats_subscription", None)
        if not sub:
            return "—"
        return f"{sub.cvs_used} / {sub.cvs_limit}"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "client_company", "plan", "cvs_used", "cvs_limit", "active", "next_payment_date", "amount")
    list_filter = ("plan", "active")
    search_fields = ("user__email",)

    @admin.display(description="Empresa")
    def client_company(self, obj):
        client = getattr(obj.user, "ats_client", None)
        return client.company_name if client else "—"


class SkillEvaluationInline(admin.TabularInline):
    model = SkillEvaluation
    extra = 0
    fields = ("skill", "level", "match_percentage")


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "vacancy", "score", "status", "match_percentage", "analysis_date")
    list_filter = ("status", "client")
    search_fields = ("name", "email")
    inlines = [SkillEvaluationInline]
    readonly_fields = ("analysis_date",)


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "created_at")
    search_fields = ("title", "client__company_name")


@admin.register(CVAnalysisConfig)
class CVAnalysisConfigAdmin(admin.ModelAdmin):
    list_display = ("client", "updated_at")
    search_fields = ("client__company_name",)


@admin.register(SkillEvaluation)
class SkillEvaluationAdmin(admin.ModelAdmin):
    list_display = ("candidate", "skill", "level", "match_percentage")
    list_filter = ("candidate__client",)


@admin.register(LLMUsageLog)
class LLMUsageLogAdmin(admin.ModelAdmin):
    list_display = ("client", "candidate", "total_tokens", "prompt_tokens", "completion_tokens", "model", "created_at")
    list_filter = ("client", "model", "created_at")
    search_fields = ("client__company_name",)
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


@admin.register(ATSClientEmailConfig)
class ATSClientEmailConfigAdmin(admin.ModelAdmin):
    list_display = ("client", "notification_email", "company_from_email", "company_from_name")
    search_fields = ("client__company_name", "notification_email", "company_from_email")


class ATSFormFieldInline(admin.TabularInline):
    model = ATSFormField
    extra = 0
    fields = ("label", "field_type", "required", "order", "placeholder")


@admin.register(ATSForm)
class ATSFormAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "vacancy", "is_active", "created_at")
    list_filter = ("client", "is_active")
    search_fields = ("name", "client__company_name")
    inlines = [ATSFormFieldInline]


@admin.register(ATSFormField)
class ATSFormFieldAdmin(admin.ModelAdmin):
    list_display = ("form", "label", "field_type", "required", "order")
    list_filter = ("form__client", "field_type")


@admin.register(ATSFormSubmission)
class ATSFormSubmissionAdmin(admin.ModelAdmin):
    list_display = ("form", "submitter_email", "submitted_at")
    list_filter = ("form__client",)
    search_fields = ("submitter_email",)
    readonly_fields = ("form", "payload", "submitter_email", "submitted_at")


@admin.register(ATSFormSubmissionFile)
class ATSFormSubmissionFileAdmin(admin.ModelAdmin):
    list_display = ("submission", "form_field", "original_name")


@admin.register(ATSNotification)
class ATSNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "type", "read", "created_at")
    list_filter = ("type", "read", "client")
    search_fields = ("title", "message", "client__company_name")
    readonly_fields = ("created_at",)
    list_editable = ("read",)


@admin.register(PlanChangeRequest)
class PlanChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("client", "from_plan", "to_plan", "status", "created_at")
    list_filter = ("status", "to_plan")
    search_fields = ("client__company_name", "client__user__email")
    readonly_fields = ("created_at",)
    list_editable = ("status",)
