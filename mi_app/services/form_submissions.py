from mi_app.models import ATSFormSubmission


DUPLICATE_SUBMISSION_MESSAGE = "Ya registramos una respuesta con este correo para este formulario."


def normalize_submitter_email(email):
    return (email or "").strip().lower()


def has_existing_submission_for_email(orbita_form, email):
    normalized_email = normalize_submitter_email(email)
    if not normalized_email:
        return False
    return ATSFormSubmission.objects.filter(
        form=orbita_form,
        submitter_email__iexact=normalized_email,
    ).exists()


def create_submission_once(orbita_form, payload, submitter_email):
    normalized_email = normalize_submitter_email(submitter_email)
    if has_existing_submission_for_email(orbita_form, normalized_email):
        return None, True
    submission = ATSFormSubmission.objects.create(
        form=orbita_form,
        payload=payload,
        submitter_email=normalized_email,
    )
    return submission, False
