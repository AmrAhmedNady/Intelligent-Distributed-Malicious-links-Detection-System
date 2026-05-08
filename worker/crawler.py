"""
Asynchronous Web Crawler.
Safely fetches web pages while enforcing SSRF protection and timeouts.
"""
import asyncio
import ipaddress
import logging
import socket
import time
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# SSRF Protection: block private IP ranges.
PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _is_private_ip(hostname: str) -> bool:
    """Return True if hostname resolves to a private/loopback IP."""
    try:
        ip = ipaddress.ip_address(hostname)
        return any(ip in net for net in PRIVATE_RANGES)
    except ValueError:
        pass
    try:
        resolved = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(resolved)
        return any(ip in net for net in PRIVATE_RANGES)
    except Exception:
        return False


async def fetch_url(url: str, timeout: int = 10) -> Optional[dict]:
    """
    Fetch a URL and return crawl data dict, or None on failure.
    Result keys: url, html, status_code, redirect_chain, elapsed_ms, error
    """
    try:
        import aiohttp
    except ImportError:
        logger.warning("aiohttp not installed — returning empty crawl")
        return {"url": url, "html": "", "status_code": 0, "redirect_chain": [], "elapsed_ms": 0}

    hostname = urlparse(url).hostname or ""

    # SSRF check
    if _is_private_ip(hostname):
        logger.warning("SSRF blocked: %s resolves to private IP", hostname)
        return {"url": url, "html": "", "status_code": 403, "redirect_chain": [], "elapsed_ms": 0,
                "error": "SSRF blocked: private IP"}

    redirect_chain = []
    start = time.monotonic()

    try:
        timeout_obj = aiohttp.ClientTimeout(total=timeout, connect=5)
        connector = aiohttp.TCPConnector(ssl=False, limit=10)

        async with aiohttp.ClientSession(
            headers=HEADERS,
            connector=connector,
            timeout=timeout_obj,
        ) as session:
            async with session.get(url, allow_redirects=True, max_redirects=5) as resp:
                # Track redirect chain
                for hist in resp.history:
                    redirect_chain.append(str(hist.url))
                redirect_chain.append(str(resp.url))

                # Read HTML (cap at 500KB)
                raw = await resp.read()
                html = raw[:512_000].decode("utf-8", errors="replace")
                elapsed = int((time.monotonic() - start) * 1000)

                return {
                    "url": str(resp.url),
                    "html": html,
                    "status_code": resp.status,
                    "redirect_chain": redirect_chain,
                    "elapsed_ms": elapsed,
                }

    except asyncio.TimeoutError:
        logger.warning("Timeout fetching %s", url)
        return {"url": url, "html": "", "status_code": 0, "redirect_chain": [], "elapsed_ms": timeout * 1000,
                "error": "Timeout"}
    except Exception as exc:
        logger.warning("Crawl error for %s: %s", url, exc)
        return {"url": url, "html": "", "status_code": 0, "redirect_chain": [], "elapsed_ms": 0,
                "error": str(exc)}
