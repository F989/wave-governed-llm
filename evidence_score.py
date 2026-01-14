from __future__ import annotations

import re
from typing import List, Dict, Any, Tuple


# -----------------------------
# Source / citation heuristics
# -----------------------------

URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
PMID_RE = re.compile(r"\bPMID\s*:\s*\d+\b|\bPMID\s+\d+\b|\bpubmed\s*:\s*\d+\b", re.IGNORECASE)
ARXIV_RE = re.compile(r"\barxiv\s*:\s*\d{4}\.\d{4,5}\b|\b\d{4}\.\d{4,5}\s*\[", re.IGNORECASE)
ISBN_RE = re.compile(r"\bISBN(?:-13)?\s*:\s*[\d-]{10,17}\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")

SOURCE_PREFIX_RE = re.compile(r"^\s*(source|sources|ref|reference|citation)\s*:\s*", re.IGNORECASE)
BRACKET_CIT_RE = re.compile(r"\[\s*\d+\s*\]")
PAREN_CIT_RE = re.compile(r"\(\s*\d{4}\s*\)")

AUTHORITY_TOKENS = {
    "britannica", "nature", "science", "nejm", "jama", "thelancet", "lancet",
    "pubmed", "ncbi", "nih", "who", "cdc", "fda", "ema", "gov", "acm", "ieee",
    "springer", "elsevier", "oxford", "cambridge", "arxiv"
}

# ✅ expanded: internal HR / interview workflows + common phrasing
INTERNAL_SOURCE_RE = re.compile(
    r"\b("
    r"interview notes?|hiring notes?|scorecard|rubric|role requires|role need[s]?|job description|"
    r"\bjd\b|panel feedback|assessment|take[- ]home|case study|"
    r"stakeholder|product sense|tradeoffs?|candidate|sql tasks?"
    r")\b",
    re.IGNORECASE
)

# Intent detectors
INTENT_FEEDBACK_RE = re.compile(
    r"\b(rejection|reject|feedback|actionable|improve|strengths?|gaps?|areas to improve|"
    r"interview|candidate|hiring)\b",
    re.IGNORECASE
)

INTENT_FACTOID_RE = re.compile(
    r"\b(capital|population|date|who is|what is)\b",
    re.IGNORECASE
)


# -----------------------------
# Helpers
# -----------------------------

WORD_RE = re.compile(r"[A-Za-z0-9]+")

def _tokens(s: str) -> List[str]:
    return [t.lower() for t in WORD_RE.findall(s)]

def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

def _sigmoid_like(x: float, k: float = 6.0, x0: float = 0.5) -> float:
    import math
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))


def _source_signals(text: str) -> Dict[str, bool]:
    t = text.strip()
    t_low = t.lower()
    return {
        "has_url": bool(URL_RE.search(t)),
        "has_doi": bool(DOI_RE.search(t)),
        "has_pmid": bool(PMID_RE.search(t)),
        "has_arxiv": bool(ARXIV_RE.search(t)),
        "has_isbn": bool(ISBN_RE.search(t)),
        "has_year": bool(YEAR_RE.search(t)),
        "has_source_prefix": bool(SOURCE_PREFIX_RE.search(t)),
        "has_bracket_cit": bool(BRACKET_CIT_RE.search(t)),
        "has_paren_year": bool(PAREN_CIT_RE.search(t)),
        "has_authority_token": any(tok in t_low for tok in AUTHORITY_TOKENS),
        "has_internal_source": bool(INTERNAL_SOURCE_RE.search(t)),
    }


def _count_unique_sources(evidence: List[str]) -> int:
    seen = set()
    for e in evidence:
        e_low = e.lower()

        for m in URL_RE.findall(e):
            url = m[0] if isinstance(m, tuple) else m
            dom = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
            dom = dom.split("/")[0].strip().lower()
            if dom:
                seen.add(("url", dom))

        for m in DOI_RE.findall(e):
            seen.add(("doi", m.lower()))

        for m in PMID_RE.findall(e):
            digits = re.findall(r"\d+", m)
            if digits:
                seen.add(("pmid", digits[0]))

        for m in ARXIV_RE.findall(e):
            num = re.search(r"\d{4}\.\d{4,5}", m)
            if num:
                seen.add(("arxiv", num.group(0)))

        for m in ISBN_RE.findall(e):
            digits = re.sub(r"[^0-9]", "", m)
            if digits:
                seen.add(("isbn", digits))

        for tok in AUTHORITY_TOKENS:
            if tok in e_low:
                seen.add(("auth", tok))

        if INTERNAL_SOURCE_RE.search(e):
            seen.add(("internal", "hr_artifact"))

    return len(seen)


def _quantity_score(evidence: List[str]) -> float:
    if not evidence:
        return 0.0
    return _clamp01(len(evidence) / 3.0)

def _length_score(evidence: List[str]) -> float:
    if not evidence:
        return 0.0
    total = sum(len(e.strip()) for e in evidence)
    return _clamp01(total / 240.0)


def _relevance_score(user_text: str, evidence: List[str]) -> float:
    if not evidence:
        return 0.0

    u_low = user_text.lower()
    joined = " ".join(evidence).lower()

    # ✅ feedback intent: accept HR-like evidence even without token overlap
    if INTENT_FEEDBACK_RE.search(u_low):
        internal_like = bool(INTERNAL_SOURCE_RE.search(joined))
        if internal_like:
            return 0.90
        # fallback: if there are at least 2 evidence items, treat as moderately relevant
        if len(evidence) >= 2:
            return 0.70

    # factoid intent: keep strict overlap
    if INTENT_FACTOID_RE.search(u_low):
        u = set(_tokens(user_text))
        if not u:
            return 0.0
        e_tokens = set()
        for e in evidence:
            e_tokens.update(_tokens(e))
        overlap = len(u & e_tokens) / max(1, len(u))
        return _clamp01(_sigmoid_like(overlap, k=10.0, x0=0.15))

    # default overlap
    u = set(_tokens(user_text))
    if not u:
        return 0.0
    e_tokens = set()
    for e in evidence:
        e_tokens.update(_tokens(e))
    overlap = len(u & e_tokens) / max(1, len(u))
    return _clamp01(_sigmoid_like(overlap, k=10.0, x0=0.15))


def _concreteness_score(user_text: str, evidence: List[str]) -> Tuple[float, Dict[str, Any], List[str]]:
    if not evidence:
        return 0.0, {"subscores": {"concrete": 0.0}}, ["no_evidence"]

    agg = {
        "url": 0, "doi": 0, "pmid": 0, "arxiv": 0, "isbn": 0,
        "year": 0, "source_prefix": 0, "bracket_cit": 0, "paren_year": 0,
        "authority": 0,
        "internal": 0,
    }

    for e in evidence:
        s = _source_signals(e)
        agg["url"] += int(s["has_url"])
        agg["doi"] += int(s["has_doi"])
        agg["pmid"] += int(s["has_pmid"])
        agg["arxiv"] += int(s["has_arxiv"])
        agg["isbn"] += int(s["has_isbn"])
        agg["year"] += int(s["has_year"])
        agg["source_prefix"] += int(s["has_source_prefix"])
        agg["bracket_cit"] += int(s["has_bracket_cit"])
        agg["paren_year"] += int(s["has_paren_year"])
        agg["authority"] += int(s["has_authority_token"])
        agg["internal"] += int(s["has_internal_source"])

    unique_src = _count_unique_sources(evidence)

    strong = (
        0.35 * _clamp01(agg["doi"] > 0) +
        0.30 * _clamp01(agg["pmid"] > 0) +
        0.20 * _clamp01(agg["url"] > 0) +
        0.10 * _clamp01(agg["arxiv"] > 0) +
        0.05 * _clamp01(agg["isbn"] > 0)
    )

    # ✅ internal HR evidence counts as "strong-ish" when feedback intent
    u_low = user_text.lower()
    if INTENT_FEEDBACK_RE.search(u_low) and agg["internal"] > 0:
        strong = max(strong, 0.65)

    medium = (
        0.20 * _clamp01(agg["source_prefix"] > 0) +
        0.15 * _clamp01(agg["year"] > 0) +
        0.10 * _clamp01(agg["bracket_cit"] > 0) +
        0.10 * _clamp01(agg["paren_year"] > 0) +
        0.20 * _clamp01(agg["authority"] > 0) +
        0.25 * _clamp01(agg["internal"] > 0)
    )

    diversity = _clamp01(unique_src / 3.0)
    concrete = _clamp01(0.65 * strong + 0.25 * medium + 0.10 * diversity)

    reasons = []
    if concrete < 0.25:
        reasons.append("low_concreteness")

    signals = {
        "unique_sources": unique_src,
        "counts": agg,
        "subscores": {
            "concrete": concrete,
            "strong_id": _clamp01(strong),
            "medium_id": _clamp01(medium),
            "diversity": diversity,
        }
    }
    return concrete, signals, reasons


# -----------------------------
# Public API
# -----------------------------

def evidence_score(user_text: str, evidence: List[str]) -> Dict[str, Any]:
    reasons: List[str] = []

    if not evidence:
        return {
            "score": 0.0,
            "reasons": ["no_evidence"],
            "signals": {"subscores": {"qty": 0.0, "length": 0.0, "rel": 0.0, "concrete": 0.0}},
        }

    qty = _quantity_score(evidence)
    length = _length_score(evidence)
    rel = _relevance_score(user_text, evidence)

    concrete, concrete_signals, concrete_reasons = _concreteness_score(user_text, evidence)
    reasons.extend(concrete_reasons)

    if rel < 0.35:
        reasons.append("low_relevance")

    score = _clamp01(
        0.40 * rel +
        0.35 * concrete +
        0.15 * qty +
        0.10 * length
    )

    # ✅ feedback floor: 2+ evidence items should not collapse to "no evidence"
    if INTENT_FEEDBACK_RE.search(user_text.lower()) and len(evidence) >= 2:
        score = max(score, 0.50)  # pushes governor to DAMPEN instead of PROJECT

    has_any_source_marker = (
        concrete_signals["counts"]["url"] > 0 or
        concrete_signals["counts"]["doi"] > 0 or
        concrete_signals["counts"]["pmid"] > 0 or
        concrete_signals["counts"]["arxiv"] > 0 or
        concrete_signals["counts"]["isbn"] > 0 or
        concrete_signals["counts"]["source_prefix"] > 0 or
        concrete_signals["counts"]["authority"] > 0 or
        concrete_signals["counts"]["internal"] > 0
    )
    if not has_any_source_marker:
        reasons.append("no_source_markers")
        score = min(score, 0.60)

    signals = {
        "subscores": {
            "qty": qty,
            "length": length,
            "rel": rel,
            "concrete": concrete,
        },
        **concrete_signals,
    }

    return {
        "score": float(score),
        "reasons": reasons,
        "signals": signals,
    }


