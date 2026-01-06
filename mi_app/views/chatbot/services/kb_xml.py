from __future__ import annotations

import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List
from django.conf import settings


@dataclass
class KBItem:
    id: str
    title: str
    body: str
    tags: str


def _kb_path() -> str:
    return os.path.join(settings.BASE_DIR, "mi_app", "views", "chatbot", "data", "kb.xml")


def load_kb() -> List[KBItem]:
    path = _kb_path()
    if not os.path.exists(path):
        return []

    tree = ET.parse(path)
    root = tree.getroot()

    items: List[KBItem] = []
    for node in root.findall(".//item"):
        item_id = (node.get("id") or "").strip()
        title = (node.findtext("title") or "").strip()
        body = (node.findtext("body") or "").strip()
        tags = (node.findtext("tags") or "").strip()
        if title or body:
            items.append(KBItem(id=item_id, title=title, body=body, tags=tags))
    return items


# --------- Normalización y tokens ----------
def _norm(text: str) -> str:
    text = (text or "").lower().strip()
    # quitar acentos
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    # espacios limpios
    text = re.sub(r"\s+", " ", text)
    return text


def _tokenize(text: str) -> List[str]:
    t = _norm(text)
    # tokens 3+ chars (evita ruido)
    return re.findall(r"[a-z0-9]{3,}", t)


# --------- Sinónimos básicos (ajusta a tu negocio) ----------
SYNONYMS = {
    "ipa": ["automatizacion", "procesos"],
    "automation": ["automatizacion"],
    "automatizar": ["automatizacion"],
    "workflow": ["workflows", "proceso", "procesos"],
    "roadmap": ["transformacion", "plan"],
    "metodologia": ["flow"],
    "metodo": ["metodologia"],
    "eve": ["eve360"],
    "evecumplimiento": ["cumplimiento", "trazabilidad", "gobierno"],
    "talento": ["staff", "augmentation", "equipo"],
    "desarrollo": ["aplicaciones", "portales", "soluciones"],
}


def _expand_tokens(tokens: List[str]) -> List[str]:
    expanded = list(tokens)
    for t in tokens:
        for syn in SYNONYMS.get(t, []):
            expanded.append(syn)
    # únicos conservando orden
    seen = set()
    out = []
    for x in expanded:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def search_kb(query: str, limit: int = 3) -> List[KBItem]:
    q = _norm(query)
    q_tokens = _expand_tokens(_tokenize(q))
    if not q_tokens:
        return []

    kb = load_kb()
    scored: List[tuple[int, KBItem]] = []

    for it in kb:
        title = _norm(it.title)
        body = _norm(it.body)
        tags = _norm(it.tags)

        # pesos
        score = 0

        # frase exacta (muy fuerte)
        if q and q in body:
            score += 25
        if q and q in title:
            score += 35
        if q and q in tags:
            score += 20

        # tokens ponderados por campo
        for t in q_tokens:
            if not t:
                continue
            if t in title:
                score += 10
            if t in tags:
                score += 6
            if t in body:
                score += 3

        # boost por “intención” (si pregunta por servicios)
        if "servicio" in q or "servicios" in q:
            if it.id.startswith("services-"):
                score += 12

        if score > 0:
            scored.append((score, it))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scored[:limit]]

def get_item_by_id(item_id: str) -> KBItem | None:
    item_id = (item_id or "").strip()
    if not item_id:
        return None
    for it in load_kb():
        if it.id == item_id:
            return it
    return None
