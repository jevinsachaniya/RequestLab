"""Secure HTTP Request Execution Engine.

Uses HTTPX with strict SSRF filtering, DNS verification, timeout enforcement,
and response size limits.
"""

import time
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import httpx

from app.core.config import settings
from app.core.ssrf import validate_outbound_url, SSRFSecurityException

ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


class ExecutionResult:
    """Encapsulates the outcome of an executed HTTP request."""

    def __init__(
        self,
        status_code: Optional[int] = None,
        response_time_ms: Optional[float] = None,
        response_headers: Optional[Dict[str, str]] = None,
        response_body: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        self.status_code = status_code
        self.response_time_ms = response_time_ms
        self.response_headers = response_headers or {}
        self.response_body = response_body
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "response_headers": self.response_headers,
            "response_body": self.response_body,
            "error_message": self.error_message,
        }


class HTTPExecutorService:
    """Executes outbound HTTP requests securely."""

    @staticmethod
    def _sanitize_headers(headers: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Validate and sanitize request headers, preventing CRLF injection."""
        if not headers:
            return {}

        sanitized: Dict[str, str] = {}
        for key, val in headers.items():
            k_str = str(key).strip()
            v_str = str(val).strip()

            # Prevent CRLF header injection
            if any(ch in k_str or ch in v_str for ch in ("\r", "\n")):
                raise ValueError(f"Header '{k_str}' contains forbidden newline characters.")

            # Filter out internal hop-by-hop headers
            if k_str.lower() in ("connection", "keep-alive", "proxy-authenticate"):
                continue

            sanitized[k_str] = v_str
        return sanitized

    @classmethod
    async def execute_request(
        cls,
        method: str,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[str] = None,
        follow_redirects: bool = False,
    ) -> ExecutionResult:
        """Execute an outbound HTTP request with SSRF protection and resource limits."""
        method_upper = method.strip().upper()
        if method_upper not in ALLOWED_METHODS:
            return ExecutionResult(
                error_message=f"HTTP method '{method}' is unsupported. Allowed: {sorted(ALLOWED_METHODS)}"
            )

        # 1. SSRF Protection: Validate target destination URL
        try:
            current_url = validate_outbound_url(url)
        except SSRFSecurityException as ssrf_err:
            return ExecutionResult(
                error_message=f"Security violation: {ssrf_err}"
            )

        # 2. Prepare headers
        try:
            req_headers = cls._sanitize_headers(headers)
        except ValueError as val_err:
            return ExecutionResult(error_message=str(val_err))

        redirect_count = 0
        max_redirects = settings.OUTBOUND_MAX_REDIRECTS if follow_redirects else 0
        timeout = httpx.Timeout(
            settings.OUTBOUND_REQUEST_TIMEOUT_SECONDS,
            connect=5.0,
        )

        start_time = time.perf_counter()

        # 3. Execution loop (manually manages redirects with per-hop SSRF validation)
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            verify=True,
        ) as client:
            while True:
                try:
                    response = await client.request(
                        method=method_upper,
                        url=current_url,
                        headers=req_headers,
                        params=params if redirect_count == 0 else None,
                        content=body.encode("utf-8") if (body and redirect_count == 0) else None,
                    )
                except httpx.TimeoutException:
                    elapsed = (time.perf_counter() - start_time) * 1000.0
                    return ExecutionResult(
                        response_time_ms=round(elapsed, 2),
                        error_message=f"Request timed out after {settings.OUTBOUND_REQUEST_TIMEOUT_SECONDS}s.",
                    )
                except (httpx.ConnectError, httpx.NetworkError) as net_err:
                    elapsed = (time.perf_counter() - start_time) * 1000.0
                    return ExecutionResult(
                        response_time_ms=round(elapsed, 2),
                        error_message=f"Connection failure: {net_err}",
                    )
                except Exception as exc:
                    elapsed = (time.perf_counter() - start_time) * 1000.0
                    return ExecutionResult(
                        response_time_ms=round(elapsed, 2),
                        error_message=f"Request failed: {exc}",
                    )

                # 4. Handle Redirects (if enabled and status is 3xx)
                if response.is_redirect and follow_redirects:
                    if redirect_count >= max_redirects:
                        elapsed = (time.perf_counter() - start_time) * 1000.0
                        return ExecutionResult(
                            status_code=response.status_code,
                            response_time_ms=round(elapsed, 2),
                            error_message=f"Exceeded maximum redirect limit of {max_redirects}.",
                        )

                    location = response.headers.get("location")
                    if not location:
                        break

                    next_url = urljoin(current_url, location)

                    # Re-validate redirect destination for SSRF
                    try:
                        current_url = validate_outbound_url(next_url)
                    except SSRFSecurityException as ssrf_err:
                        elapsed = (time.perf_counter() - start_time) * 1000.0
                        return ExecutionResult(
                            status_code=response.status_code,
                            response_time_ms=round(elapsed, 2),
                            error_message=f"Redirect blocked by SSRF protection: {ssrf_err}",
                        )

                    # Strip Authorization header if redirect crosses to a different host
                    orig_host = urlparse(url).hostname
                    dest_host = urlparse(current_url).hostname
                    if orig_host and dest_host and orig_host.lower() != dest_host.lower():
                        req_headers.pop("Authorization", None)
                        req_headers.pop("authorization", None)

                    redirect_count += 1
                    # Method handling on 303 or 302
                    if response.status_code in (302, 303):
                        method_upper = "GET"
                        body = None
                    continue

                break

            # 5. Read response body with size limit guard
            elapsed = (time.perf_counter() - start_time) * 1000.0
            resp_bytes = bytearray()
            max_bytes = settings.OUTBOUND_MAX_RESPONSE_BYTES

            async for chunk in response.aiter_bytes():
                resp_bytes.extend(chunk)
                if len(resp_bytes) > max_bytes:
                    return ExecutionResult(
                        status_code=response.status_code,
                        response_time_ms=round(elapsed, 2),
                        response_headers=dict(response.headers),
                        error_message=f"Response exceeded maximum allowed size ({max_bytes / (1024 * 1024):.1f} MB).",
                    )

            try:
                decoded_body = resp_bytes.decode("utf-8")
            except UnicodeDecodeError:
                decoded_body = resp_bytes.decode("latin-1", errors="replace")

            return ExecutionResult(
                status_code=response.status_code,
                response_time_ms=round(elapsed, 2),
                response_headers=dict(response.headers),
                response_body=decoded_body,
            )


http_executor = HTTPExecutorService()

