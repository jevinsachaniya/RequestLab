"""Pydantic schemas for executing HTTP requests and execution history."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


class RequestExecute(BaseModel):
    """Payload to execute an ad-hoc or temporary HTTP request."""

    method: str = Field("GET", description="HTTP method")
    url: str = Field(..., min_length=1, max_length=2000, description="Target URL")
    headers: Optional[Dict[str, Any]] = Field(default_factory=dict, description="HTTP headers")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Query parameters")
    body: Optional[str] = Field(None, description="Request body")
    follow_redirects: bool = Field(False, description="Follow redirects safely (default False)")
    assertions: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="Automated assertions to test against response"
    )

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in VALID_METHODS:
            raise ValueError(f"Method must be one of {sorted(VALID_METHODS)}")
        return v_upper


class ExecutionResponse(BaseModel):
    """Result returned immediately after executing an outbound HTTP request."""

    execution_id: Optional[int] = Field(None, description="Persisted history record ID")
    status_code: Optional[int] = Field(None, description="HTTP status code received")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    response_headers: Dict[str, str] = Field(default_factory=dict, description="Response headers")
    response_body: Optional[str] = Field(None, description="Response payload as string")
    assertion_results: List[Dict[str, Any]] = Field(
        default_factory=list, description="Results of automated response assertions"
    )
    error_message: Optional[str] = Field(None, description="Error message if request failed")


class ExecutionHistoryResponse(BaseModel):
    """Full detail of a logged execution history record."""

    id: int
    user_id: int
    saved_request_id: Optional[int] = None
    method: str
    url: str
    request_headers: Optional[Dict[str, Any]] = None
    request_body: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    response_headers: Optional[Dict[str, Any]] = None
    response_body: Optional[str] = None
    assertion_results: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionHistoryPagination(BaseModel):
    """Paginated list of execution history logs."""

    items: List[ExecutionHistoryResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)
