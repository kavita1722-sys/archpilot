"""Tests for URL security, SSRF blocking, and safe fetching."""

import pytest
from app.tools.url_fetch import UrlFetchTool, is_safe_ip, validate_url_safety


def test_reject_non_http_schemes():
    """Verify validate_url_safety rejects non-http/https protocols."""
    safe, reason = validate_url_safety("file:///etc/passwd")
    assert safe is False
    assert "forbidden" in reason.lower()

    safe, reason = validate_url_safety("ftp://example.com/file.txt")
    assert safe is False
    assert "forbidden" in reason.lower()

    safe, reason = validate_url_safety("gopher://internal.service")
    assert safe is False
    assert "forbidden" in reason.lower()


def test_reject_localhost_and_loopback():
    """Verify SSRF protection rejects localhost and loopback interfaces."""
    safe, reason = validate_url_safety("http://localhost:8000/api")
    assert safe is False
    assert "rejected" in reason.lower() or "forbidden" in reason.lower()

    safe, reason = validate_url_safety("http://127.0.0.1:8000/admin")
    assert safe is False
    assert "forbidden" in reason.lower()

    safe, reason = validate_url_safety("http://127.0.0.5:8080")
    assert safe is False
    assert "forbidden" in reason.lower()


def test_is_safe_ip_loopback():
    """Verify is_safe_ip blocks loopback IPs."""
    safe, reason = is_safe_ip("127.0.0.1")
    assert safe is False
    assert "loopback" in reason.lower()


def test_is_safe_ip_private_ranges():
    """Verify is_safe_ip blocks RFC 1918 private IP ranges."""
    # 10.0.0.0/8
    safe, reason = is_safe_ip("10.0.1.5")
    assert safe is False
    assert "private" in reason.lower()

    # 192.168.0.0/16
    safe, reason = is_safe_ip("192.168.1.100")
    assert safe is False
    assert "private" in reason.lower()

    # 172.16.0.0/12
    safe, reason = is_safe_ip("172.20.0.5")
    assert safe is False
    assert "private" in reason.lower()


def test_is_safe_ip_link_local_and_zero():
    """Verify is_safe_ip blocks link-local metadata service (169.254.169.254) and 0.0.0.0."""
    safe, reason = is_safe_ip("169.254.169.254")
    assert safe is False
    assert "link-local" in reason.lower()

    safe, reason = is_safe_ip("0.0.0.0")
    assert safe is False
    assert "forbidden" in reason.lower()


def test_url_fetch_tool_rejects_ssrf_via_execute():
    """Verify UrlFetchTool rejects SSRF attacks and returns an error without raising."""
    tool = UrlFetchTool()
    result = tool.execute({"url": "http://127.0.0.1:8000/internal"})

    assert result.status == "error"
    assert "forbidden" in result.error.lower() or "rejected" in result.error.lower() or "blocked" in result.error.lower()


def test_url_fetch_tool_mock_domain_success():
    """Verify UrlFetchTool successfully handles known benchmark documentation URLs."""
    tool = UrlFetchTool()
    result = tool.execute({"url": "https://qdrant.tech/documentation/guides/quantization/"})

    assert result.status == "success"
    assert "quantization" in result.output["content"].lower()
    assert result.output["content_length"] > 0
