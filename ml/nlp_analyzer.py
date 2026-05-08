"""
NLP Analyzer.
Scans textual content to identify common phishing terminology and patterns.
"""
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

URGENCY_WORDS = frozenset({
    "urgent", "immediately", "alert", "warning", "attention",
    "action required", "act now", "expires", "suspended",
    "deactivated", "locked", "restricted", "compromised",
})
CREDENTIAL_WORDS = frozenset({
    "password", "username", "login", "sign in", "verify", "confirm",
    "authenticate", "credential", "credit card", "bank account", "pin", "cvv",
})
IMPERSONATION_WORDS = frozenset({
    "paypal", "amazon", "apple", "microsoft", "google", "facebook",
    "netflix", "bank of america", "chase", "irs", "customer service",
})
THREAT_WORDS = frozenset({
    "malware", "virus", "hacked", "stolen", "breach", "fraud",
    "phishing", "scam", "infected", "blocked", "disabled", "terminated",
})


@dataclass
class NLPResult:
    content_score: float = 0.0
    urgency_score: float = 0.0
    credential_score: float = 0.0
    impersonation_score: float = 0.0
    threat_score: float = 0.0
    keyword_hits: list = field(default_factory=list)


def _normalize(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).lower()


def _score(text: str, words: frozenset):
    hits = [w for w in words if w in text]
    return min(1.0, len(hits) / max(1, len(words) * 0.1)), hits


def analyze(html: str, url: str = "") -> NLPResult:
    r = NLPResult()
    if not html:
        return r
    text = _normalize(html[:50_000])
    r.urgency_score, uh = _score(text, URGENCY_WORDS)
    r.credential_score, ch = _score(text, CREDENTIAL_WORDS)
    r.impersonation_score, ih = _score(text, IMPERSONATION_WORDS)
    r.threat_score, th = _score(text, THREAT_WORDS)
    r.content_score = min(1.0, (
        r.urgency_score * 0.35 + r.credential_score * 0.30 +
        r.impersonation_score * 0.20 + r.threat_score * 0.15
    ))
    r.keyword_hits = (uh + ch + ih + th)[:10]
    return r
