"""RequestExecution Database Repository."""

import math
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.request_execution import RequestExecution

SENSITIVE_HEADER_KEYS = {
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "cookie",
    "set-cookie",
}


def mask_sensitive_headers(headers: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Mask sensitive tokens, passwords, and cookies to prevent storing secrets in logs."""
    if not headers:
        return {}
    sanitized: Dict[str, str] = {}
    for k, v in headers.items():
        k_str = str(k)
        if k_str.lower() in SENSITIVE_HEADER_KEYS:
            sanitized[k_str] = "[REDACTED]"
        else:
            sanitized[k_str] = str(v)
    return sanitized


class ExecutionRepository:
    """Repository handling database operations for request execution history."""

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        method: str,
        url: str,
        saved_request_id: Optional[int] = None,
        request_headers: Optional[Dict[str, Any]] = None,
        request_body: Optional[str] = None,
        status_code: Optional[int] = None,
        response_time_ms: Optional[float] = None,
        response_headers: Optional[Dict[str, Any]] = None,
        response_body: Optional[str] = None,
        assertion_results: Optional[List[Dict[str, Any]]] = None,
        error_message: Optional[str] = None,
    ) -> RequestExecution:
        """Create and persist an execution history log, masking sensitive headers."""
        # Sanitize headers to prevent credential leakage
        safe_req_headers = mask_sensitive_headers(request_headers)

        # Cap stored body in DB to 250KB to keep database agile
        stored_body = response_body
        if stored_body and len(stored_body) > 250_000:
            stored_body = stored_body[:250_000] + "\n... [truncated for storage]"

        db_obj = RequestExecution(
            user_id=user_id,
            saved_request_id=saved_request_id,
            method=method,
            url=url,
            request_headers=safe_req_headers,
            request_body=request_body,
            status_code=status_code,
            response_time_ms=response_time_ms,
            response_headers=response_headers,
            response_body=stored_body,
            assertion_results=assertion_results,
            error_message=error_message,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_by_id_and_user(
        db: Session, execution_id: int, user_id: int
    ) -> Optional[RequestExecution]:
        """Fetch a specific execution log, ensuring user ownership."""
        return (
            db.query(RequestExecution)
            .filter(
                RequestExecution.id == execution_id,
                RequestExecution.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def get_multi_by_user(
        db: Session,
        user_id: int,
        saved_request_id: Optional[int] = None,
        status_code: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[RequestExecution], int, int]:
        """Fetch paginated execution history with optional filtering."""
        query = db.query(RequestExecution).filter(RequestExecution.user_id == user_id)

        if saved_request_id is not None:
            query = query.filter(RequestExecution.saved_request_id == saved_request_id)
        if status_code is not None:
            query = query.filter(RequestExecution.status_code == status_code)

        total = query.with_entities(func.count(RequestExecution.id)).scalar() or 0

        offset = (page - 1) * page_size
        items = (
            query.order_by(RequestExecution.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return items, total, total_pages

    @staticmethod
    def delete(db: Session, db_obj: RequestExecution) -> None:
        """Delete an execution log record."""
        db.delete(db_obj)
        db.commit()


execution_repository = ExecutionRepository()

