"""
Formularios para registro e inicio de sesión de clientes ATS.
"""
import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


def validate_password_strength(value):
    """Mínimo 8 caracteres, al menos una letra y un número."""
    if len(value) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
    if not re.search(r"[a-zA-Z]", value):
        raise ValidationError("La contraseña debe incluir al menos una letra.")
    if not re.search(r"\d", value):
        raise ValidationError("La contraseña debe incluir al menos un número.")


class ATSRegisterForm(UserCreationForm):
    """Registro de nuevo cliente ATS: email como usuario, empresa, contacto."""
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "tu@empresa.com",
            "autocomplete": "email",
        }),
    )
    company_name = forms.CharField(
        label="Nombre de la empresa",
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Mi Empresa S.A. de C.V.",
        }),
    )
    contact_name = forms.CharField(
        label="Nombre del contacto",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Juan Pérez",
        }),
    )
    contact_phone = forms.CharField(
        label="Teléfono",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "+52 55 1234 5678",
        }),
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Mín. 8 caracteres, con letra y número",
            "autocomplete": "new-password",
        }),
        validators=[validate_password_strength],
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Repite tu contraseña",
            "autocomplete": "new-password",
        }),
    )

    class Meta:
        model = User
        fields = ("email", "company_name", "contact_name", "contact_phone", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].help_text = "Mínimo 8 caracteres, al menos una letra y un número."
        if "username" in self.fields:
            del self.fields["username"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden.")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            raise forms.ValidationError("El correo es obligatorio.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo.")
        return email

    def save(self, commit=True):
        email = self.cleaned_data["email"]
        # Usamos el email como username (Django requiere username único)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data.get("contact_name", "")[:150],
        )
        if commit:
            from mi_app.models import ATSClient, Subscription
            ATSClient.objects.create(
                user=user,
                company_name=self.cleaned_data["company_name"],
                contact_name=self.cleaned_data.get("contact_name", ""),
                contact_phone=self.cleaned_data.get("contact_phone", ""),
            )
            Subscription.objects.get_or_create(
                user=user,
                defaults={
                    "plan": Subscription.PLAN_FREE,
                    "cvs_limit": 3,
                    "active": True,
                },
            )
        return user


class ATSLoginForm(AuthenticationForm):
    """Login con correo y contraseña."""
    username = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "tu@empresa.com",
            "autocomplete": "email",
        }),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Tu contraseña",
            "autocomplete": "current-password",
        }),
    )

    def clean(self):
        username = self.cleaned_data.get("username", "").strip().lower()
        if username:
            # Buscar usuario por email (guardamos email en User.username)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(email=username).exists():
                user = User.objects.get(email=username)
                self.cleaned_data["username"] = user.username
            elif User.objects.filter(username=username).exists():
                pass
            else:
                raise forms.ValidationError("Correo o contraseña incorrectos.")
        return super().clean()


# --- Formularios ATS (crear formularios para candidatos) y configuración de correo ---

from mi_app.models import ATSForm, ATSFormField, ATSFormCriterion, ATSClientEmailConfig, ATSClient, Vacancy, CVAnalysisConfig


class ATSFormCreateEditForm(forms.ModelForm):
    """Crear o editar un formulario ATS (nombre, descripción, vacante, vista/grilla, solicitar CV, solicitar correo)."""
    class Meta:
        model = ATSForm
        fields = ("name", "description", "vacancy", "layout", "request_email", "request_cv")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Postulación Desarrollador"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Instrucciones para el candidato (opcional)"}),
            "vacancy": forms.Select(attrs={"class": "form-select"}),
            "layout": forms.Select(attrs={"class": "form-select"}),
            "request_email": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "request_cv": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ATSFormFieldForm(forms.ModelForm):
    """Un campo del formulario (para formset)."""
    class Meta:
        model = ATSFormField
        fields = ("label", "field_type", "required", "order", "placeholder")
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Etiqueta"}),
            "field_type": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "required": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "order": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": 0}),
            "placeholder": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Opcional"}),
        }


def get_ats_form_field_formset(extra=2, form_instance=None, data=None, files=None):
    """Devuelve formset de campos. Si data/files se pasan, formset enlazado para validar."""
    from django.forms import modelformset_factory
    FormSet = modelformset_factory(
        ATSFormField,
        form=ATSFormFieldForm,
        extra=extra,
        can_delete=True,
        min_num=0,
        validate_min=False,
    )
    queryset = form_instance.fields.all() if form_instance else ATSFormField.objects.none()
    if data is not None:
        return FormSet(data, files, queryset=queryset, prefix="fields")
    return FormSet(queryset=queryset, prefix="fields")


class ATSFormCriterionForm(forms.ModelForm):
    """Un criterio de evaluación manual del formulario (para formset)."""
    class Meta:
        model = ATSFormCriterion
        fields = ("label", "order")
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-control form-control-sm", "placeholder": "Ej. Experiencia en Python"}),
            "order": forms.NumberInput(attrs={"class": "form-control form-control-sm", "min": 0}),
        }


def get_ats_form_criterion_formset(extra=2, form_instance=None, data=None):
    """Devuelve formset de criterios de evaluación. Si data se pasa, formset enlazado."""
    from django.forms import modelformset_factory
    FormSet = modelformset_factory(
        ATSFormCriterion,
        form=ATSFormCriterionForm,
        extra=extra,
        can_delete=True,
        min_num=0,
        validate_min=False,
    )
    queryset = form_instance.criteria.all() if form_instance else ATSFormCriterion.objects.none()
    if data is not None:
        return FormSet(data, queryset=queryset, prefix="criteria")
    return FormSet(queryset=queryset, prefix="criteria")


class ATSEmailConfigForm(forms.ModelForm):
    """Configuración de correo: notificaciones y correo de la empresa (conexión propia)."""
    class Meta:
        model = ATSClientEmailConfig
        fields = (
            "notification_email",
            "company_from_email",
            "company_from_name",
            "smtp_host",
            "smtp_port",
            "smtp_user",
            "smtp_use_tls",
        )
        widgets = {
            "notification_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "notificaciones@tuempresa.com"}),
            "company_from_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "rrhh@tuempresa.com"}),
            "company_from_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Recursos Humanos - Mi Empresa"}),
            "smtp_host": forms.TextInput(attrs={"class": "form-control", "placeholder": "smtp.gmail.com"}),
            "smtp_port": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 65535}),
            "smtp_user": forms.TextInput(attrs={"class": "form-control", "placeholder": "correo@tuempresa.com", "autocomplete": "off"}),
            "smtp_use_tls": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        help_texts = {
            "notification_email": "Recibirás aquí avisos de nuevas postulaciones y respuestas.",
            "company_from_email": "Correo que verán los candidatos como remitente (puede ser el mismo de la empresa).",
            "smtp_host": "Opcional: conectar tu servidor de correo para enviar desde tu dominio.",
        }


class ATSProfileForm(forms.ModelForm):
    """Configurar cuenta: foto de perfil, nombre de contacto, teléfono."""
    class Meta:
        model = ATSClient
        fields = ("avatar", "contact_name", "contact_phone", "company_name")
        widgets = {
            "avatar": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "contact_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Tu nombre"}),
            "contact_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+52 55 1234 5678"}),
            "company_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de la empresa"}),
        }


def _parse_skills_text(value):
    """Convierte texto (una por línea o separado por comas) en lista de strings sin vacíos."""
    if not value or not value.strip():
        return []
    lines = [s.strip() for s in value.replace(",", "\n").splitlines() if s.strip()]
    return lines


class ATSVacancyForm(forms.ModelForm):
    """Crear o editar vacante (puesto de trabajo) con perfil para análisis con IA."""
    desired_skills_text = forms.CharField(
        label="Habilidades deseadas (una por línea)",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Python\nInglés B2\nTrabajo en equipo\nLiderazgo",
        }),
    )

    class Meta:
        model = Vacancy
        fields = ("title", "description", "profile_for_analysis")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Desarrollador Python"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Requisitos, responsabilidades, etc."}),
            "profile_for_analysis": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Perfil que debe evaluar la IA: años de experiencia, tecnologías, nivel de inglés, etc.",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.desired_skills:
            self.fields["desired_skills_text"].initial = "\n".join(self.instance.desired_skills)

    def clean_desired_skills_text(self):
        return _parse_skills_text(self.cleaned_data.get("desired_skills_text") or "")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.desired_skills = self.cleaned_data.get("desired_skills_text") or []
        if commit:
            obj.save()
        return obj


class CVAnalysisConfigForm(forms.ModelForm):
    """Configuración por defecto del análisis de CV (perfil e instrucciones para la IA)."""
    default_desired_skills_text = forms.CharField(
        label="Habilidades deseadas por defecto (una por línea)",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Comunicación\nExcel\nTrabajo en equipo",
        }),
    )

    class Meta:
        model = CVAnalysisConfig
        fields = ("default_profile", "analysis_instructions")
        widgets = {
            "default_profile": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Perfil general que buscas cuando no hay vacante: experiencia, nivel, tipo de puesto.",
            }),
            "analysis_instructions": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Instrucciones extra para la IA (opcional).",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.default_desired_skills:
            self.fields["default_desired_skills_text"].initial = "\n".join(self.instance.default_desired_skills)

    def clean_default_desired_skills_text(self):
        return _parse_skills_text(self.cleaned_data.get("default_desired_skills_text") or "")

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.default_desired_skills = self.cleaned_data.get("default_desired_skills_text") or []
        if commit:
            obj.save()
        return obj
