"""
Servicio de análisis de CV con IA.
- Extrae texto de PDF (pdfplumber) y DOCX (python-docx).
- Obtiene la configuración de perfil (vacante o CVAnalysisConfig del cliente).
- Analiza el CV con IA según esa configuración; el score es referente al perfil/vacante buscado.
- Guarda en BD: Candidate (score, status, explanation_text, raw_text, analysis_date, match_percentage)
  y SkillEvaluation por cada habilidad identificada.
"""
import logging
import os
from typing import Optional

from django.utils import timezone

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extrae texto de un PDF usando pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        logger.warning("pdfplumber no instalado; no se puede extraer texto de PDF.")
        return ""
    text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
    except Exception as e:
        logger.exception("Error extrayendo texto del PDF %s: %s", file_path, e)
        return ""
    return "\n\n".join(text_parts)


def extract_text_from_docx(file_path: str) -> str:
    """Extrae texto de un DOCX usando python-docx."""
    try:
        from docx import Document
    except ImportError:
        logger.warning("python-docx no instalado; no se puede extraer texto de DOCX.")
        return ""
    try:
        doc = Document(file_path)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.exception("Error extrayendo texto del DOCX %s: %s", file_path, e)
        return ""


def extract_text_from_cv(file_path: str, filename: Optional[str] = None) -> str:
    """
    Extrae texto de un archivo de CV (PDF o DOCX).
    file_path: ruta absoluta al archivo.
    filename: nombre del archivo (opcional) para decidir por extensión si no se puede por file_path.
    """
    if not file_path or not os.path.isfile(file_path):
        return ""
    name = (filename or os.path.basename(file_path)).lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    if name.endswith(".docx") or name.endswith(".doc"):
        # python-docx solo abre .docx; .doc sería otro formato
        if name.endswith(".doc") and not name.endswith(".docx"):
            logger.warning("Formato .doc no soportado para extracción de texto; use .docx o .pdf.")
            return ""
        return extract_text_from_docx(file_path)
    # Por defecto intentar como PDF (algunos sin extensión)
    return extract_text_from_pdf(file_path)


def get_profile_config_for_candidate(candidate) -> dict:
    """
    Devuelve la configuración de perfil para analizar el CV de un candidato.
    La configuración de la IA es por vacante: si tiene vacante con perfil/habilidades definidos,
    se usan; si tiene vacante pero sin perfil, se usa la config por defecto del cliente pero
    manteniendo el título de la vacante. Sin vacante, solo config por defecto.
    """
    vacancy = getattr(candidate, "vacancy", None)
    client = candidate.client
    config = getattr(client, "cv_analysis_config", None)
    default_profile = (config.default_profile or "").strip() if config else ""
    default_skills = list(config.default_desired_skills) if config and config.default_desired_skills else []
    default_instructions = (config.analysis_instructions or "").strip() if config else ""
    vacancy_title = vacancy.title if vacancy else None

    # Candidato con vacante: usar perfil de la vacante si está definido; si no, rellenar con defaults
    if vacancy:
        profile = (getattr(vacancy, "profile_for_analysis", None) or "").strip() or default_profile or vacancy.title
        skills = list(vacancy.desired_skills) if getattr(vacancy, "desired_skills", None) else default_skills
        return {
            "profile_summary": profile,
            "desired_skills": skills,
            "instructions": default_instructions,
            "vacancy_title": vacancy_title,
        }
    # Sin vacante: solo config por defecto
    return {
        "profile_summary": default_profile or "Evaluar experiencia y habilidades relevantes del candidato.",
        "desired_skills": default_skills,
        "instructions": default_instructions,
        "vacancy_title": None,
    }


def _analyze_with_openai(raw_text: str, profile_config: dict) -> tuple[dict | None, dict | None]:
    """
    Llama a la API de OpenAI para analizar el CV.
    Retorna (dict de resultado, dict de uso con prompt_tokens, completion_tokens, total_tokens, model) o (None, None) si falla.
    """
    from django.conf import settings as django_settings
    api_key = getattr(django_settings, "OPENAI_API_KEY", None) or os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None, None
    model = getattr(django_settings, "OPENAI_MODEL", "gpt-4o-mini")
    profile = profile_config.get("profile_summary") or "Perfil general"
    desired = profile_config.get("desired_skills") or []
    instructions = profile_config.get("instructions") or ""
    vacancy_title = profile_config.get("vacancy_title") or "la vacante"
    cv_snippet = (raw_text or "")[:12000].strip()
    if not cv_snippet:
        return None
    skills_list = ", ".join(desired) if desired else "las que consideres relevantes"
    system_prompt = (
        "Eres un evaluador de CVs para reclutamiento. Analiza el texto del CV y evalúa al candidato "
        "respecto al perfil y vacante indicados. Responde ÚNICAMENTE con un JSON válido, sin markdown ni texto extra."
    )
    user_prompt = f"""Perfil/vacante buscado: {vacancy_title}.
Descripción del perfil: {profile}
Habilidades deseadas: {skills_list}
{f'Instrucciones adicionales: {instructions}' if instructions else ''}

TEXTO DEL CV (extraído):
{cv_snippet}

Responde con un JSON que tenga exactamente estas claves:
- "score": número entre 0 y 100 (qué tan bien encaja con el perfil)
- "status": una de "APTO", "REVISION", "NO_APTO"
- "explanation": texto corto en español explicando por qué ese score y estado
- "match_percentage": número 0-100 (coincidencia global con la vacante)
- "skills": array de objetos con "skill" (nombre), "level" (0-100), "match_percentage" (número o null). Máximo 12."""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        content = (response.choices[0].message.content or "").strip()
        if not content:
            return None, None
        if "```" in content:
            for part in content.split("```"):
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    content = part
                    break
        import json
        data = json.loads(content)
        score = max(0.0, min(100.0, float(data.get("score", 0))))
        status = str(data.get("status", "REVISION")).strip().upper()
        if status not in ("APTO", "REVISION", "NO_APTO"):
            status = "REVISION"
        explanation = (data.get("explanation") or "")[:10000]
        match_percentage = data.get("match_percentage")
        if match_percentage is not None:
            match_percentage = max(0.0, min(100.0, float(match_percentage)))
        skills = []
        for s in (data.get("skills") or [])[:12]:
            if not isinstance(s, dict):
                continue
            skill_name = (s.get("skill") or "").strip()[:100]
            if not skill_name:
                continue
            level = max(0, min(100, int(s.get("level") or 0)))
            mp = s.get("match_percentage")
            if mp is not None:
                mp = max(0.0, min(100.0, float(mp)))
            skills.append({"skill": skill_name, "level": level, "match_percentage": mp})
        result = {
            "score": round(score, 1),
            "status": status,
            "explanation": explanation or f"Evaluación respecto a {vacancy_title}: {profile[:80]}...",
            "skills": skills,
            "match_percentage": round(score, 1) if match_percentage is None else match_percentage,
        }
        usage = None
        if getattr(response, "usage", None):
            u = response.usage
            usage = {
                "prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(u, "completion_tokens", 0) or 0,
                "total_tokens": getattr(u, "total_tokens", 0) or 0,
                "model": model,
            }
        return result, usage
    except Exception as e:
        logger.warning("OpenAI CV analysis failed: %s", e)
        return None, None


def _analyze_cv_stub(raw_text: str, profile_config: dict) -> dict:
    """Evaluación stub cuando no hay API key o falla OpenAI."""
    profile = profile_config.get("profile_summary") or "Perfil general"
    desired = profile_config.get("desired_skills") or []
    vacancy_title = profile_config.get("vacancy_title") or "la vacante"
    skills = []
    for i, skill in enumerate(desired[:8]):
        level = min(70 + (i * 5), 95)
        skills.append({"skill": skill, "level": level, "match_percentage": min(100.0, 75.0 + (i * 3))})
    if not skills and raw_text:
        skills = [
            {"skill": "Experiencia general", "level": 65, "match_percentage": None},
            {"skill": "Formación", "level": 70, "match_percentage": None},
        ]
    num_desired = len(desired)
    score = min(95.0, 50.0 + num_desired * 5 + (sum(s["level"] for s in skills) / max(len(skills), 1)) * 0.3) if (desired or skills) else 72.0
    status = "APTO" if score >= 75 else ("REVISION" if score >= 50 else "NO_APTO")
    explanation = (
        f"Análisis respecto al perfil de {vacancy_title}: {profile[:80]}... "
        "Sin clave OpenAI configurada o error de API; usando evaluación automática básica."
    )
    return {
        "score": round(score, 1),
        "status": status,
        "explanation": explanation,
        "skills": skills,
        "match_percentage": round(score, 1),
    }


def analyze_cv_with_ai(raw_text: str, profile_config: dict) -> tuple[dict, dict | None]:
    """
    Analiza el texto del CV con IA según el perfil/vacante buscado.
    Retorna (resultado, uso de tokens o None si stub/error).
    Si OPENAI_API_KEY está configurada, usa OpenAI; si no, usa evaluación stub.
    """
    if not raw_text or not raw_text.strip():
        return {
            "score": 0.0,
            "status": "NO_APTO",
            "explanation": "No se pudo extraer texto del CV. Asegúrate de que el archivo sea PDF o DOCX legible.",
            "skills": [],
            "match_percentage": None,
        }, None
    result, usage = _analyze_with_openai(raw_text, profile_config)
    if result is not None:
        return result, usage
    return _analyze_cv_stub(raw_text, profile_config), None


def _send_langsmith_trace_if_enabled(profile_config: dict, raw_text_len: int, result: dict, usage: dict, candidate) -> None:
    """
    Si LANGSMITH_API_KEY está configurada, envía una traza del análisis a LangSmith
    para poder orquestar y ver consumo desde el dashboard de LangSmith.
    """
    api_key = os.environ.get("LANGSMITH_API_KEY", "").strip()
    if not api_key:
        return
    try:
        from langsmith.run_trees import RunTree
        run = RunTree(
            name="cv_analysis",
            run_type="chain",
            project_name=os.environ.get("LANGSMITH_PROJECT", "ats-cv"),
            inputs={
                "profile_summary": (profile_config.get("profile_summary") or "")[:300],
                "vacancy_title": (profile_config.get("vacancy_title") or "")[:100],
                "text_length": raw_text_len,
                "client_id": candidate.client_id,
                "candidate_id": candidate.pk,
            },
            extra={
                "usage": usage,
                "client": getattr(candidate.client, "company_name", ""),
            },
        )
        run.end(outputs={
            "score": result.get("score"),
            "status": result.get("status"),
            "total_tokens": usage.get("total_tokens"),
        })
        run.post()
    except Exception as e:
        logger.warning("LangSmith trace failed (non-blocking): %s", e)


def run_cv_analysis_and_save(candidate) -> dict:
    """
    Ejecuta el análisis del CV del candidato según el perfil de la vacante (o config por defecto),
    guarda en la base de datos el score (referente a lo que se busca para ese tipo de vacante),
    la explicación, el texto extraído y las habilidades evaluadas.

    - candidate: instancia de Candidate con cv_file asignado.
    - Usa get_profile_config_for_candidate() para obtener perfil/habilidades deseadas.
    - Extrae texto del CV, llama a analyze_cv_with_ai(), persiste en Candidate y SkillEvaluation.

    Retorna: {"ok": True, "candidate": candidate} o {"ok": False, "error": str}.
    """
    from mi_app.models import Candidate, SkillEvaluation

    if not candidate.cv_file:
        return {"ok": False, "error": "El candidato no tiene archivo de CV."}

    file_path = getattr(candidate.cv_file, "path", None)
    if not file_path or not os.path.isfile(file_path):
        return {"ok": False, "error": "No se encontró el archivo del CV en el servidor."}

    profile_config = get_profile_config_for_candidate(candidate)
    raw_text = extract_text_from_cv(file_path, os.path.basename(candidate.cv_file.name))
    result, usage = analyze_cv_with_ai(raw_text, profile_config)

    # Actualizar candidato: score referente al perfil/vacante, estado, explicación, texto crudo, fecha
    candidate.raw_text = raw_text[:65535] if raw_text else ""  # por si el campo tiene límite
    candidate.score = max(0.0, min(100.0, float(result["score"])))
    candidate.status = result["status"] if result["status"] in ("APTO", "REVISION", "NO_APTO") else "REVISION"
    candidate.explanation_text = (result.get("explanation") or "")[:10000]
    candidate.analysis_date = timezone.now()
    mp = result.get("match_percentage")
    candidate.match_percentage = max(0.0, min(100.0, float(mp))) if mp is not None else None
    candidate.save(update_fields=[
        "raw_text", "score", "status", "explanation_text", "analysis_date", "match_percentage"
    ])

    # Eliminar evaluaciones de habilidades anteriores y crear las nuevas identificadas por la IA
    SkillEvaluation.objects.filter(candidate=candidate).delete()
    for s in result.get("skills") or []:
        skill_name = (s.get("skill") or "").strip()[:100]
        if not skill_name:
            continue
        level = max(0, min(100, int(s.get("level") or 0)))
        match_pct = s.get("match_percentage")
        if match_pct is not None:
            match_pct = max(0.0, min(100.0, float(match_pct)))
        SkillEvaluation.objects.create(
            candidate=candidate,
            skill=skill_name,
            level=level,
            match_percentage=match_pct,
        )

    # Registrar uso de tokens (para admin y LangSmith)
    if usage:
        from mi_app.models import LLMUsageLog
        LLMUsageLog.objects.create(
            client=candidate.client,
            candidate=candidate,
            prompt_tokens=usage.get("prompt_tokens", 0) or 0,
            completion_tokens=usage.get("completion_tokens", 0) or 0,
            total_tokens=usage.get("total_tokens", 0) or 0,
            model=(usage.get("model") or "")[:64],
        )
        _send_langsmith_trace_if_enabled(
            profile_config=profile_config,
            raw_text_len=len(raw_text),
            result=result,
            usage=usage,
            candidate=candidate,
        )

    return {"ok": True, "candidate": candidate}
