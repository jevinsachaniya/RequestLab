"""Server-Side Request Forgery (SSRF) Protection and URL Safety Validator."""

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Set

# Cloud provider metadata IP addresses and hostnames
METADATA_IPS: Set[str] = {
    "169.254.169.254",  # AWS EC2, GCP, Azure, OpenStack instance metadata
    "100.100.100.200",  # Alibaba Cloud metadata
    "fd00:ec2::254",     # AWS IPv6 metadata
}

BLOCKED_HOSTNAMES: Set[str] = {
    "localhost",
    "metadata.google.internal",
    "instance-data",
}


class SSRFSecurityException(Exception):
    """Raised when an outbound HTTP request targets a blocked or unsafe destination."""
    pass


def is_ip_allowed(ip_str: str) -> bool:
    """Validate whether an IP address is safe for outbound server requests.

    Blocks:
    - Loopback (127.0.0.0/8, ::1)
    - Private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7)
    - Link-local (169.254.0.0/16, fe80::/10)
    - Cloud metadata IPs (169.254.169.254, etc.)
    - Multicast (224.0.0.0/4, ff00::/8)
    - Unspecified / 0.0.0.0 / ::
    - Reserved addresses
    """
    if ip_str in METADATA_IPS:
        return False

    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False

    if (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return False

    # Block 0.0.0.0/8 network
    if isinstance(ip, ipaddress.IPv4Address) and ip.is_reserved:
        return False

    return True


def validate_outbound_url(url: str) -> str:
    """Validate an outbound destination URL against SSRF and protocol vulnerabilities.

    Returns the normalized URL if safe, or raises SSRFSecurityException if blocked.
    """
    if not url or not isinstance(url, str):
        raise SSRFSecurityException("Request URL is required and must be a string.")

    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise SSRFSecurityException(f"Invalid URL structure: {exc}")

    # 1. Enforce HTTP/HTTPS protocols only
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFSecurityException(
            f"Unsupported scheme '{parsed.scheme}'. Only 'http' and 'https' are allowed."
        )

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityException("URL must contain a valid host destination.")

    hostname_lower = hostname.lower()

    # 2. Block well-known dangerous hostnames
    if hostname_lower in BLOCKED_HOSTNAMES:
        raise SSRFSecurityException(
            f"Access to destination '{hostname}' is blocked for security reasons."
        )

    # 3. Resolve DNS and inspect all destination IP addresses
    try:
        # Determine port
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        addr_info = socket.getaddrinfo(
            hostname,
            port,
            socket.AF_UNSPEC,
            socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise SSRFSecurityException(
            f"Unable to resolve hostname '{hostname}': {exc}"
        )

    if not addr_info:
        raise SSRFSecurityException(f"No IP addresses resolved for '{hostname}'.")

    # 4. Check each resolved IP
    for family, _, _, _, sockaddr in addr_info:
        resolved_ip = sockaddr[0]
        if not is_ip_allowed(resolved_ip):
            raise SSRFSecurityException(
                f"Destination '{hostname}' resolves to blocked/internal IP '{resolved_ip}'."
            )

    return url

