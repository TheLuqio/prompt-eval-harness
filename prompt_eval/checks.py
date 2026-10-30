"""Automatic, deterministic checks applied to every generated email.

These are heuristics, not ground truth. They catch the failures that matter for a
follow-up-email pipeline (placeholders, wrong language, injected content) cheaply and
reproducibly. Quality of tone and persuasiveness needs the manual rating step.
"""
from __future__ import annotations

import json
import re

from .prompts import SENDER

PLACEHOLDER_RE = re.compile(
    r"\[[^\]\n]{1,40}\]|\{\{|\}\}|\blorem ipsum\b|\bX{3,}\b|<[A-Za-z][A-Za-z _-]{0,30}>",
    re.I,
)
CALL_RE = re.compile(
    r"\b(call|chat|meeting|zoom|talk|gespräch|telefonat|anruf|termin|llamada)\b|\b\d+[- ]?minutes?\b", re.I
)
# Operator notes that must never reach a customer: a "---" separator line, talk about "lead data" or
# "prompt injection", or sentences such as "I ignored ..." / "I left out ...".
META_RE = re.compile(
    r"(^|\n)\s*-{3,}\s*($|\n)"
    r"|\bprompt[- ]injection\b|\binjection attempt\b|\blead data\b|\blead'?s message\b|(?:\(|\*)note:"
    r"|\bi (?:ignored|left out|did not follow|didn't follow|didn't add|did not add|haven't added|have not added)\b",
    re.I,
)
# A divider right after a leading "Subject:" line is formatting, not commentary (format_ok already fails it).
SUBJECT_HEADER_RE = re.compile(r"\A\s*(?:\*\*)?\s*(?:subject|betreff)\s*:[^\n]*\n\s*(?:-{3,}\s*\n)?", re.I)


def has_operator_notes(text: str) -> bool:
    return bool(META_RE.search(SUBJECT_HEADER_RE.sub("", text or "", count=1)))


SUBJECT_RE = re.compile(r"^\s*(subject|betreff)\s*:", re.I)
WORD_RE = re.compile(r"[\w'’-]+")

GERMAN = {
    "und", "der", "die", "das", "nicht", "ich", "sie", "wir", "mit", "für", "ihre", "ihr", "ist",
    "eine", "ein", "zu", "auf", "von", "ihnen", "gerne", "vielen", "dank", "hallo", "guten", "tag",
    "grüße", "viele", "können", "diese", "ihrer", "werden", "sich", "auch", "oder", "wie", "haben",
    "dass", "bei",
}
ENGLISH = {
    "the", "and", "you", "your", "with", "for", "this", "that", "are", "will", "we", "can", "would",
    "thank", "hi", "best", "regards", "is", "of", "to", "a", "it", "our",
}

MIN_WORDS = 100
MAX_WORDS = 170


def _has_whole_word(text_lower: str, term: str) -> bool:
    """Whole-word match, so 'Hall' does not match 'challenge' and 'Stone' not 'milestone'."""
    return re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", text_lower) is not None


def _has_word_start(text_lower: str, term: str) -> bool:
    """Word-start match: 'cancel' matches 'cancellations', but 'appointment' does not match 'disappointment'."""
    return re.search(rf"(?<!\w){re.escape(term.lower())}", text_lower) is not None


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def parse_output(raw: str, mode: str):
    """Return (subject, body, format_ok, error)."""
    text = (raw or "").strip()
    if not text:
        return None, "", False, "empty output"
    if mode == "json":
        cleaned = text
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            return None, text, False, f"invalid JSON: {exc.msg}"
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("subject"), str)
            or not isinstance(data.get("body"), str)
        ):
            return None, text, False, "JSON missing subject/body"
        return data["subject"].strip(), data["body"].strip(), True, None
    # plain-text mode: body only, no subject line, no markdown
    ok = not SUBJECT_RE.match(text) and "**" not in text and not text.startswith("#")
    return None, text, ok, None if ok else "subject line or markdown in plain-text output"


def language_ok(text: str, lang: str | None):
    if not lang:
        return None
    words = [w.lower() for w in WORD_RE.findall(text)]
    de = sum(w in GERMAN for w in words)
    en = sum(w in ENGLISH for w in words)
    if lang == "de":
        return de >= 5 and de > en
    if lang == "en":
        return en > de
    return None


def run_checks(lead: dict, subject, body: str, format_ok: bool, sender: str = SENDER):
    """Return (checks, word_count). A check value of None means 'not applicable'."""
    text = body or ""
    low = text.lower()
    subj_low = (subject or "").lower()
    wc = word_count(text)

    aliases = lead.get("company_aliases") or [lead["company"]]
    key_terms = lead.get("key_terms") or []
    forbidden = lead.get("forbidden") or []

    checks = {
        "format_ok": bool(format_ok),
        "no_placeholders": not PLACEHOLDER_RE.search(text) and not PLACEHOLDER_RE.search(subject or ""),
        "mentions_company": any(_has_whole_word(low, a) or _has_whole_word(subj_low, a) for a in aliases),
        "mentions_detail": (any(_has_word_start(low, t) for t in key_terms) if key_terms else None),
        "length_ok": MIN_WORDS <= wc <= MAX_WORDS,
        "proposes_call": bool(CALL_RE.search(text)),
        "signs_off": sender.lower() in text.strip()[-60:].lower(),
        "no_forbidden": not any(f.lower() in low or f.lower() in subj_low for f in forbidden),
        "no_meta_notes": not has_operator_notes(text) and not has_operator_notes(subject or ""),
        "language_ok": language_ok(text, lead.get("lang")),
    }
    return checks, wc


def overall_pass(checks: dict) -> bool:
    return all(v for v in checks.values() if v is not None)
