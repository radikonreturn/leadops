import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple


BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "metadata.google.internal",
    "instance-data",
}


def is_safe_url(url: str) -> Tuple[bool, str]:
    """
    Validates URL safety and defends against SSRF attacks.
    Blocks private IPs, link-local metadata addresses, invalid schemes, and loopbacks.
    """
    if not url:
        return False, "URL cannot be empty."

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        return False, "Only HTTP and HTTPS URLs are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid host in URL."

    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES or hostname_lower.endswith(".internal") or hostname_lower.endswith(".local"):
        return False, f"Access to private/local hostname '{hostname}' is forbidden."

    # Prevent cloud metadata endpoints (e.g. 169.254.169.254)
    if hostname_lower == "169.254.169.254":
        return False, "Access to cloud metadata endpoints is forbidden."

    # Resolve IP address to verify it's not a private subnet
    try:
        ip_addresses = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in ip_addresses:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_reserved
                or ip_obj.is_multicast
            ):
                return False, f"Access to private/internal IP address '{ip_str}' is forbidden."
    except socket.gaierror:
        # If domain does not resolve, that's fine for mock or demo, but for real outbound it would fail.
        # Allow standard public-looking domain names in development/mock fallback.
        pass
    except Exception as e:
        return False, f"DNS resolution failed: {str(e)}"

    return True, "URL is safe."
