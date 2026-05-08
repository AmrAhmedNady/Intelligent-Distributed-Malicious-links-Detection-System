"""
Shared post-model risk adjustment rules.
Adds extra weight for high-risk lexical URL patterns that the ML model can
underestimate on modern phishing URLs, especially when the hostname is crafted
to impersonate trusted brands.
"""
import re
from urllib.parse import urlparse

from ml.classifier import PredictionResult
from ml.feature_extractor import IP_PATTERN, PHISHING_PATTERNS, SUSPICIOUS_TLDS, _extract_tld

IMPERSONATED_BRANDS = frozenset({
    "adobe",
    "amazon",
    "apple",
    "bank",
    "chase",
    "dropbox",
    "facebook",
    "github",
    "gmail",
    "google",
    "hotmail",
    "instagram",
    "linkedin",
    "microsoft",
    "netflix",
    "office",
    "openai",
    "outlook",
    "paypal",
    "slack",
    "spotify",
    "stripe",
    "telegram",
    "whatsapp",
    "yahoo",
    "youtube",
    "zoom",
})


def _hostname_tokens(hostname: str) -> list[str]:
    return [token for token in re.split(r"[.\-]", hostname.lower()) if token]


def _registrable_label(hostname: str) -> str:
    parts = hostname.lower().split(".")
    if len(parts) >= 2:
        return parts[-2]
    return hostname.lower()


def _has_brand_impersonation(hostname: str) -> bool:
    registrable_label = _registrable_label(hostname)
    tokens = set(_hostname_tokens(hostname))
    return any(
        brand in tokens and brand != registrable_label
        for brand in IMPERSONATED_BRANDS
    )


def apply_risk_rules(
    url: str,
    prediction: PredictionResult,
    *,
    nlp_score: float = 0.0,
    html: str = "",
) -> PredictionResult:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    scheme = (parsed.scheme or "").lower()
    url_lower = url.lower()

    keyword_hits = len(PHISHING_PATTERNS.findall(url_lower))
    dot_count = hostname.count(".")
    hyphen_count = hostname.count("-")
    has_ip = bool(IP_PATTERN.match(hostname))
    suspicious_tld = _extract_tld(hostname) in SUSPICIOUS_TLDS
    brand_impersonation = _has_brand_impersonation(hostname)
    js_redirect = "window.location" in html.lower() or "location.href" in html.lower()
    path_depth = len([p for p in parsed.path.split('/') if p])
    has_risky_ext = any(url_lower.endswith(ext) for ext in ['.exe', '.zip', '.apk', '.scr', '.jar', '.dmg'])
    digit_in_brand = any(char.isdigit() for char in hostname) and any(brand in hostname for brand in IMPERSONATED_BRANDS)

    adjusted_risk = float(prediction.risk_score)
    lexical_boost = 0.0

    if scheme != "https":
        lexical_boost += 0.18
    if keyword_hits:
        lexical_boost += min(0.18, 0.06 * keyword_hits)
    if dot_count >= 3:
        lexical_boost += 0.10
    elif dot_count == 2:
        lexical_boost += 0.04
    if hyphen_count >= 2:
        lexical_boost += 0.08
    elif hyphen_count == 1 and keyword_hits >= 2:
        lexical_boost += 0.04
    if brand_impersonation:
        lexical_boost += 0.18
    if js_redirect:
        lexical_boost += 0.08
    if path_depth >= 5:
        lexical_boost += 0.12
    if has_risky_ext:
        lexical_boost += 0.15
    if digit_in_brand:
        lexical_boost += 0.10
    if brand_impersonation and suspicious_tld:
        lexical_boost += 0.15

    if (suspicious_tld and keyword_hits >= 1) or has_ip:
        adjusted_risk = max(adjusted_risk, 0.72 if scheme == "https" else 0.82)
    if brand_impersonation and keyword_hits >= 2:
        adjusted_risk = max(adjusted_risk, 0.70 if scheme == "https" else 0.78)
    if keyword_hits >= 3 and dot_count >= 3 and (hyphen_count >= 1 or scheme != "https"):
        adjusted_risk = max(adjusted_risk, 0.68)

    adjusted_risk = min(1.0, adjusted_risk + lexical_boost)

    if nlp_score > 0.55 and adjusted_risk >= 0.30:
        adjusted_risk = min(1.0, adjusted_risk + nlp_score * 0.12)

    prediction.risk_score = round(adjusted_risk, 4)
    prediction.label = "malicious" if prediction.risk_score >= 0.5 else "benign"
    prediction.confidence = round(
        prediction.risk_score if prediction.label == "malicious" else (1.0 - prediction.risk_score),
        4,
    )
    return prediction
