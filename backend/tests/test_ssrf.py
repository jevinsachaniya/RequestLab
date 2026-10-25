"""Unit tests for SSRF (Server-Side Request Forgery) protection."""

import pytest
from app.core.ssrf import validate_outbound_url, is_ip_allowed, SSRFSecurityException


@pytest.mark.parametrize(
    "blocked_ip",
    [
        "127.0.0.1",
        "127.0.0.2",
        "10.0.0.1",
        "10.254.0.1",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.0.1",
        "192.168.1.100",
        "169.254.169.254",  # Cloud metadata
        "100.100.100.200",  # Alibaba cloud metadata
        "0.0.0.0",
        "::1",              # IPv6 loopback
        "fe80::1",          # IPv6 link-local
        "fc00::1",          # IPv6 private
    ],
)
def test_is_ip_allowed_blocks_private_and_metadata_ips(blocked_ip: str):
    """Verify that private, loopback, link-local, and cloud metadata IPs are rejected."""
    assert is_ip_allowed(blocked_ip) is False


def test_is_ip_allowed_permits_public_ips():
    """Verify that legitimate public IPs are permitted."""
    assert is_ip_allowed("8.8.8.8") is True
    assert is_ip_allowed("1.1.1.1") is True
    assert is_ip_allowed("93.184.216.34") is True  # example.com


@pytest.mark.parametrize(
    "unsupported_scheme_url",
    [
        "ftp://example.com/file.txt",
        "file:///etc/passwd",
        "file:///C:/Windows/System32/drivers/etc/hosts",
        "gopher://example.com",
        "ssh://user@example.com",
        "data:text/plain;base64,SGVsbG8=",
    ],
)
def test_validate_outbound_url_rejects_unsupported_protocols(unsupported_scheme_url: str):
    """Verify that non-HTTP/HTTPS protocols are rejected."""
    with pytest.raises(SSRFSecurityException) as exc_info:
        validate_outbound_url(unsupported_scheme_url)
    assert "unsupported scheme" in str(exc_info.value).lower()


@pytest.mark.parametrize(
    "blocked_hostname_url",
    [
        "http://localhost",
        "http://localhost:8000",
        "http://metadata.google.internal",
        "http://instance-data/latest/meta-data/",
    ],
)
def test_validate_outbound_url_rejects_dangerous_hostnames(blocked_hostname_url: str):
    """Verify that well-known dangerous hostnames are rejected."""
    with pytest.raises(SSRFSecurityException) as exc_info:
        validate_outbound_url(blocked_hostname_url)
    assert "blocked for security reasons" in str(exc_info.value).lower()


def test_validate_outbound_url_blocks_loopback_ip():
    """Verify that direct loopback IP URLs are blocked."""
    with pytest.raises(SSRFSecurityException) as exc_info:
        validate_outbound_url("http://127.0.0.1:8080/admin")
    assert "blocked/internal ip" in str(exc_info.value).lower()


def test_validate_outbound_url_blocks_cloud_metadata():
    """Verify that cloud metadata IP 169.254.169.254 is blocked."""
    with pytest.raises(SSRFSecurityException) as exc_info:
        validate_outbound_url("http://169.254.169.254/latest/meta-data/")
    assert "blocked/internal ip" in str(exc_info.value).lower()

