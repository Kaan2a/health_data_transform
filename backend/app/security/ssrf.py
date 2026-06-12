import socket
import ipaddress
from urllib.parse import urlparse
from app.core.config import settings

class SSRFError(Exception):
    pass

def validate_url_for_ssrf(url: str) -> None:
    """
    Validates a URL to prevent Server-Side Request Forgery (SSRF).
    Blocks requests to private IPs (e.g. 10.x.x.x, 192.168.x.x, 127.0.0.1)
    and loopback addresses, unless explicitly allowed in development.
    """
    try:
        parsed_url = urlparse(url)
    except Exception as e:
        raise SSRFError(f"Invalid URL format: {str(e)}")

    if parsed_url.scheme not in ["http", "https"]:
        raise SSRFError(f"Unsupported scheme: {parsed_url.scheme}")

    hostname = parsed_url.hostname
    if not hostname:
        raise SSRFError("No hostname provided in URL")

    # In development, check the explicit allowlist (e.g. "mock-api:5000")
    if settings.ENVIRONMENT == "development":
        host_port = f"{hostname}:{parsed_url.port}" if parsed_url.port else hostname
        if host_port in settings.SSRF_DEV_ALLOWLIST:
            return # Explicitly allowed in dev

    try:
        # Resolve hostname to IPs
        ip_addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise SSRFError(f"Could not resolve hostname: {hostname}")

    for addr_info in ip_addresses:
        ip_str = addr_info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
            raise SSRFError(
                f"URL resolves to a private or restricted IP address: {ip_str}. "
                "This request is blocked due to SSRF protection policies."
            )
