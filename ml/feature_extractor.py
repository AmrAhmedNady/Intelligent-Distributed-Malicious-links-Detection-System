"""
Feature Extractor.
Analyzes raw HTML and URLs to generate the selected live-scan feature set.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from ml.dataset import MODEL_FEATURE_NAMES

try:
    import tldextract
    _HAS_TLDEXTRACT = True
except ImportError:
    _HAS_TLDEXTRACT = False

logger = logging.getLogger(__name__)

# Trusted domain whitelist.
# These domains are hard-coded as benign to protect against false positives.
TRUSTED_DOMAINS = frozenset({
    "google.com", "www.google.com", "youtube.com", "www.youtube.com",
    "facebook.com", "www.facebook.com", "twitter.com", "x.com",
    "instagram.com", "linkedin.com", "github.com", "microsoft.com",
    "apple.com", "amazon.com", "wikipedia.org", "reddit.com",
    "netflix.com", "python.org", "stackoverflow.com", "mozilla.org",
    "cloudflare.com", "openai.com", "anthropic.com", "stripe.com",
    "paypal.com", "noon.com", "yahoo.com", "bing.com", "adobe.com",
    "dropbox.com", "slack.com", "zoom.us", "office.com", "live.com",
    "outlook.com", "hotmail.com", "gmail.com", "twitch.tv", "spotify.com",
    "airbnb.com", "uber.com", "whatsapp.com", "telegram.org",
})

# URL Shortener hostnames.
URL_SHORTENERS = frozenset({
    "bit.ly", "tinyurl.com", "goo.gl", "ow.ly", "t.co",
    "is.gd", "buff.ly", "adf.ly", "bl.ink", "short.link",
    "cutt.ly", "rb.gy", "tiny.cc", "url.ie", "shorturl.at",
})

# Suspicious TLDs commonly used in phishing.
SUSPICIOUS_TLDS = frozenset({
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "click",
    "link", "work", "date", "loan", "download", "racing",
    "review", "stream", "gdn", "bid", "win", "accountant",
    "science", "trade", "webcam", "faith", "party",
})

SAFE_EXTERNAL_DOMAINS = frozenset({
    "adobedtm.com",
    "akamaihd.net",
    "bootstrapcdn.com",
    "cdnjs.com",
    "cloudflare.com",
    "cloudfront.net",
    "doubleclick.net",
    "google-analytics.com",
    "googletagmanager.com",
    "googleapis.com",
    "gstatic.com",
    "jsdelivr.net",
    "typekit.net",
    "unpkg.com",
})

# Phishing keyword patterns.
PHISHING_PATTERNS = re.compile(
    r"(payp[a4]l|secure|update|verify|account|login|signin|bank"
    r"|confirm|password|credential|wallet|invoice|billing"
    r"|suspend|unlock|alert|notice|claim|winner|prize|free)",
    re.IGNORECASE,
)

IP_PATTERN = re.compile(
    r"^(\d{1,3}\.){3}\d{1,3}$"
)


def _extract_tld(hostname: str) -> str:
    if _HAS_TLDEXTRACT:
        ext = tldextract.extract(hostname)
        return ext.suffix or ""
    parts = hostname.rsplit(".", 1)
    return parts[-1] if len(parts) > 1 else ""


def _registrable_domain(hostname: str) -> str:
    if not hostname:
        return ""
    if _HAS_TLDEXTRACT:
        ext = tldextract.extract(hostname)
        if ext.domain and ext.suffix:
            return f"{ext.domain}.{ext.suffix}".lower()
        if ext.domain:
            return ext.domain.lower()
    parts = hostname.lower().split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else hostname.lower()


def _domains_related(left: str, right: str) -> bool:
    if not left or not right:
        return False
    left_domain = _registrable_domain(left)
    right_domain = _registrable_domain(right)
    return bool(left_domain and left_domain == right_domain)


def _is_internal_or_safe(hostname: str, candidate: str) -> bool:
    if not candidate or not candidate.startswith(("http://", "https://")):
        return True

    target_host = urlparse(candidate).hostname or ""
    if not target_host:
        return True

    if _domains_related(hostname, target_host):
        return True

    return _registrable_domain(target_host) in SAFE_EXTERNAL_DOMAINS


@dataclass
class FeatureVector:
    """
    Selected live-scan features aligned with the training subset.
    All values: +1 = legit, -1 = phishing, 0 = uncertain
    """
    having_IP_Address: int = 0
    URL_Length: int = 0
    Shortining_Service: int = 0
    having_At_Symbol: int = 0
    Prefix_Suffix: int = 0
    having_Sub_Domain: int = 0
    SSLfinal_State: int = 0
    Favicon: int = 0
    port: int = 0
    HTTPS_token: int = 0
    Request_URL: int = 0
    URL_of_Anchor: int = 0
    Links_in_tags: int = 0
    SFH: int = 0
    Submitting_to_email: int = 0
    on_mouseover: int = 0
    popUpWidnow: int = 0

    FEATURE_ORDER = MODEL_FEATURE_NAMES

    def to_list(self) -> list:
        return [getattr(self, name) for name in self.FEATURE_ORDER]


class FeatureExtractor:
    """
    Extracts the feature subset we can compute reliably at runtime.
    """

    def extract_url_features(self, url: str) -> FeatureVector:
        """Extract features from URL string only (no HTTP request)."""
        fv = FeatureVector()
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            scheme = parsed.scheme.lower()
            tld = _extract_tld(hostname)

            fv.having_IP_Address = -1 if IP_PATTERN.match(hostname) else 1

            url_len = len(url)
            fv.URL_Length = 1 if url_len < 54 else (0 if url_len <= 75 else -1)

            is_short = any(s in hostname for s in URL_SHORTENERS)
            fv.Shortining_Service = -1 if is_short else 1

            fv.having_At_Symbol = -1 if "@" in url else 1

            fv.Prefix_Suffix = -1 if "-" in hostname else 1

            dot_count = hostname.count(".")
            fv.having_Sub_Domain = 1 if dot_count == 1 else (0 if dot_count == 2 else -1)

            if scheme == "https":
                fv.SSLfinal_State = 1 if tld not in SUSPICIOUS_TLDS else 0
            else:
                fv.SSLfinal_State = -1

            fv.Favicon = 0

            fv.port = -1 if parsed.port and parsed.port not in (80, 443, 8080, 8443) else 1

            fv.HTTPS_token = -1 if "https" in hostname else 1

            fv.Request_URL = 0
            fv.URL_of_Anchor = 0
            fv.Links_in_tags = 0
            fv.SFH = 0
            fv.Submitting_to_email = 0
            fv.on_mouseover = 1
            fv.popUpWidnow = 1

        except Exception as exc:
            logger.warning("Feature extraction error for %s: %s", url, exc)

        return fv

    def extract_html_features(self, url: str, html: str, fv: Optional[FeatureVector] = None) -> FeatureVector:
        """Enrich a FeatureVector with HTML content features."""
        if fv is None:
            fv = self.extract_url_features(url)
        if not html:
            return fv

        try:
            from bs4 import BeautifulSoup
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname or ""
            soup = BeautifulSoup(html, "html.parser")
            html_lower = html.lower()

            link_tags = soup.find_all("link", rel=re.compile("icon", re.I))
            if link_tags:
                favicon_href = link_tags[0].get("href", "")
                fv.Favicon = 1 if _is_internal_or_safe(hostname, favicon_href) else 0

            total_resources = 0
            external_resources = 0
            for tag in soup.find_all(["img", "script", "link"]):
                src = tag.get("src") or tag.get("href") or ""
                if src:
                    total_resources += 1
                    if not _is_internal_or_safe(hostname, src):
                        external_resources += 1
            if total_resources == 0:
                fv.Request_URL = 1
            else:
                ratio = external_resources / total_resources
                fv.Request_URL = 1 if ratio < 0.35 else (0 if ratio < 0.75 else -1)

            anchors = soup.find_all("a", href=True)
            suspicious_anchors = 0.0
            for a in anchors:
                href = (a["href"] or "").strip()
                if href in ("#", "", "javascript:;", "javascript:void(0)") or href.lower().startswith("javascript:"):
                    suspicious_anchors += 1.0
                    continue
                if href.startswith(("http://", "https://")) and not _is_internal_or_safe(hostname, href):
                    suspicious_anchors += 0.25
            if not anchors:
                fv.URL_of_Anchor = 1
            else:
                ratio = suspicious_anchors / len(anchors)
                fv.URL_of_Anchor = 1 if ratio < 0.20 else (0 if ratio < 0.50 else -1)

            meta_tags = soup.find_all(["meta", "link", "script"])
            ext_tags = sum(
                1 for t in meta_tags
                if not _is_internal_or_safe(hostname, t.get("href") or t.get("src") or "")
            )
            if not meta_tags:
                fv.Links_in_tags = 1
            else:
                ratio = ext_tags / len(meta_tags)
                fv.Links_in_tags = 1 if ratio < 0.40 else (0 if ratio < 0.80 else -1)

            forms = soup.find_all("form")
            if not forms:
                fv.SFH = 1
            else:
                fv.SFH = 1
                for form in forms:
                    action = (form.get("action", "") or "").strip()
                    if action in ("", "#", "about:blank"):
                        fv.SFH = -1
                        break
                    if action.startswith(("http://", "https://")) and not _is_internal_or_safe(hostname, action):
                        fv.SFH = 0

            if any("mailto:" in (f.get("action", "")) for f in soup.find_all("form")):
                fv.Submitting_to_email = -1
            else:
                fv.Submitting_to_email = 1

            fv.on_mouseover = -1 if "onmouseover" in html_lower and "window.status" in html_lower else 1

            fv.popUpWidnow = -1 if re.search(r"window\.open\s*\(", html_lower) else 1

        except Exception as exc:
            logger.warning("HTML feature extraction error: %s", exc)

        return fv


# Module-level singleton
_extractor = FeatureExtractor()


def extract(url: str, html: str = "") -> FeatureVector:
    """Convenience function: extract URL (+ optional HTML) features."""
    fv = _extractor.extract_url_features(url)
    if html:
        fv = _extractor.extract_html_features(url, html, fv)
    return fv


def is_trusted(url: str) -> bool:
    """Return True if the URL's hostname is in the trusted domain whitelist."""
    try:
        hostname = urlparse(url).hostname or ""
        # Check exact match and www variants
        return (
            hostname in TRUSTED_DOMAINS or
            hostname.lstrip("www.") in TRUSTED_DOMAINS or
            f"www.{hostname}" in TRUSTED_DOMAINS
        )
    except Exception:
        return False


if __name__ == "__main__":
    # Quick smoke test
    logging.basicConfig(level=logging.INFO)
    test_urls = [
        ("https://www.google.com", "LEGIT"),
        ("https://www.python.org", "LEGIT"),
        ("http://paypal-secure-verify.tk/login@192.168.1.1", "PHISH"),
        ("http://192.168.1.100/confirm-account?token=abc", "PHISH"),
        ("https://amazon-billing-update.xyz/verify", "PHISH"),
        ("https://github.com/openai", "LEGIT"),
    ]
    extractor = FeatureExtractor()
    for url, expected in test_urls:
        fv = extractor.extract_url_features(url)
        values = fv.to_list()
        phish_count = sum(1 for v in values if v == -1)
        legit_count = sum(1 for v in values if v == 1)
        print(f"[{expected}] {url[:60]}")
        print(f"  Phishing signals: {phish_count}/{len(values)}  Legit signals: {legit_count}/{len(values)}")
        print(f"  Trusted: {is_trusted(url)}\n")
