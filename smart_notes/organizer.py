"""Core logic for Smart Notes Organizer.

Pipeline:  raw text -> parse_notes -> cluster (LLM or local) -> render_markdown
Both backends return the same structure:  [{"heading": str, "notes": [str, ...]}, ...]
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, List

Group = Dict[str, object]

DEFAULT_MODEL = os.getenv("SMART_NOTES_MODEL", "claude-sonnet-5-5")

PROMPT = """You are a note-organizing assistant.

Below are numbered notes collected from many sources. Group them by topic and
write a short, clear heading (2-5 words) for each group.

Rules:
- Every note index must appear in exactly one group.
- Prefer fewer, meaningful groups over many tiny ones (singletons only if truly unrelated).
- Do not rewrite or drop notes; only reference them by index.
- Respond with ONLY valid JSON, no prose, no code fences, in this shape:
{{"groups": [{{"heading": "Topic Heading", "notes": [0, 3, 5]}}]}}

NOTES:
{notes}
"""


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")


def parse_notes(text: str) -> List[str]:
    """Split pasted text into individual notes.

    Notes are separated by blank lines. If the text is a single block, each
    non-empty line is treated as its own note. Bullet markers are stripped.
    """
    text = text.strip()
    if not text:
        return []
    blocks = [b for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) == 1:
        blocks = [ln for ln in blocks[0].splitlines() if ln.strip()]
    notes = []
    for block in blocks:
        cleaned = " ".join(_BULLET.sub("", ln).strip() for ln in block.splitlines())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            notes.append(cleaned)
    return notes


# --------------------------------------------------------------------------
# LLM backend
# --------------------------------------------------------------------------
def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _cluster_llm(notes: List[str], model: str = DEFAULT_MODEL) -> List[Group]:
    numbered = "\n".join(f"[{i}] {n}" for i, n in enumerate(notes))
    prompt = PROMPT.format(notes=numbered)

    if os.getenv("GROQ_API_KEY"):
        from groq import Groq

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content
    else:
        import anthropic

        os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        resp = client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = "".join(b.text for b in resp.content if b.type == "text")

    data = _extract_json(raw)

    groups: List[Group] = []
    seen = set()
    for g in data.get("groups", []):
        idxs = [i for i in g.get("notes", []) if isinstance(i, int) and 0 <= i < len(notes) and i not in seen]
        seen.update(idxs)
        if idxs:
            groups.append({"heading": str(g.get("heading", "Untitled")).strip(), "notes": [notes[i] for i in idxs]})
    missing = [notes[i] for i in range(len(notes)) if i not in seen]
    if missing:
        groups.append({"heading": "Miscellaneous", "notes": missing})
    return groups


# --------------------------------------------------------------------------
# Local (offline) backend: TF-IDF + KMeans
# --------------------------------------------------------------------------
def _cluster_local(notes: List[str], max_groups: int = 8) -> List[Group]:
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics import silhouette_score

    if len(notes) < 3:
        return [{"heading": "Notes", "notes": notes}]

    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    X = vec.fit_transform(notes)
    terms = vec.get_feature_names_out()

    best_k, best_score = None, -1.0
    for k in range(2, min(max_groups, len(notes) - 1) + 1):
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(X, labels)
        if score > best_score:
            best_k, best_score = k, score
    if best_k is None:
        return [{"heading": "Notes", "notes": notes}]

    km = KMeans(n_clusters=best_k, n_init=10, random_state=42).fit(X)
    groups: List[Group] = []
    for c in range(best_k):
        members = [notes[i] for i, l in enumerate(km.labels_) if l == c]
        top = km.cluster_centers_[c].argsort()[::-1][:6]
        words: List[str] = []
        for t in top:
            term = terms[t]
            if not any(term in w or w in term for w in words):
                words.append(term)
            if len(words) == 2:
                break
        groups.append({"heading": " & ".join(w.title() for w in words) or "Notes", "notes": members})
    return sorted(groups, key=lambda g: -len(g["notes"]))


# --------------------------------------------------------------------------
# Rendering + public API
# --------------------------------------------------------------------------
def render_markdown(groups: List[Group], title: str = "Organized Notes") -> str:
    lines = [f"# {title}", ""]
    for g in groups:
        lines.append(f"## {g['heading']}")
        lines.extend(f"- {n}" for n in g["notes"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def organize_notes(text: str, backend: str = "auto", model: str = DEFAULT_MODEL) -> str:
    """Turn pasted notes into Markdown grouped under topic headings.

    backend: "llm", "local", or "auto" (LLM if ANTHROPIC_API_KEY is set, else local).
    """
    notes = parse_notes(text)
    if not notes:
        raise ValueError("No notes found. Paste some text first.")
    if backend == "auto":
        backend = "llm" if (os.getenv("ANTHROPIC_API_KEY") or os.getenv("GROQ_API_KEY")) else "local"
    if backend == "llm":
        groups = _cluster_llm(notes, model)
    elif backend == "local":
        groups = _cluster_local(notes)
    else:
        raise ValueError(f"Unknown backend: {backend}")
    return render_markdown(groups)
