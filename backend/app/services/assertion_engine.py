"""Automated Response Assertion Evaluation Engine.

Safely evaluates expected status codes, response times, headers, and JSON fields
without executing any arbitrary code or eval().
"""

import json
from typing import Dict, Any, List, Optional, Tuple


def extract_json_path(data: Any, path: str) -> Tuple[bool, Any]:
    """Safely traverse a nested JSON structure (dicts and lists) using dot notation.

    Example: "user.orders.0.total" -> traverses data["user"]["orders"][0]["total"]
    Returns: (found: bool, value: Any)
    """
    if not path or not isinstance(path, str):
        return False, None

    tokens = path.strip().split(".")
    current = data

    for token in tokens:
        if isinstance(current, dict):
            if token in current:
                current = current[token]
            else:
                return False, None
        elif isinstance(current, list):
            # Check if token is an integer list index
            try:
                idx = int(token)
                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return False, None
            except ValueError:
                return False, None
        else:
            return False, None

    return True, current


class AssertionEngine:
    """Evaluates a list of assertion rules against HTTP response data."""

    @classmethod
    def evaluate(
        cls,
        assertions: Optional[List[Dict[str, Any]]],
        status_code: Optional[int],
        response_time_ms: Optional[float],
        response_headers: Optional[Dict[str, str]],
        response_body: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Evaluate all assertions and return structured results."""
        if not assertions:
            return []

        results: List[Dict[str, Any]] = []

        # Parse JSON body once if possible
        parsed_json: Optional[Any] = None
        is_valid_json = False
        if response_body:
            try:
                parsed_json = json.loads(response_body)
                is_valid_json = True
            except Exception:
                pass

        for rule in assertions:
            if not isinstance(rule, dict):
                results.append({
                    "rule": rule,
                    "passed": False,
                    "actual": None,
                    "message": "Malformed assertion rule: must be a dictionary.",
                })
                continue

            rule_type = str(rule.get("type", "")).strip().lower()
            expected = rule.get("expected")
            operator = str(rule.get("operator", "equals")).strip().lower()
            target = rule.get("target")

            # 1. Status Code Assertion
            if rule_type == "status_code":
                actual = status_code
                passed = False
                message = ""

                try:
                    expected_code = int(expected)
                    if operator in ("equals", "=="):
                        passed = (actual == expected_code)
                        message = f"Expected status {expected_code}, got {actual}." if not passed else f"Status code is {actual}."
                    elif operator in ("not_equals", "!="):
                        passed = (actual != expected_code)
                        message = f"Expected status not {expected_code}, got {actual}."
                    else:
                        message = f"Unsupported operator '{operator}' for status_code assertion."
                except (ValueError, TypeError):
                    message = f"Expected status code must be an integer, got '{expected}'."

                results.append({
                    "rule": rule,
                    "passed": passed,
                    "actual": actual,
                    "message": message,
                })

            # 2. Response Time Assertion
            elif rule_type == "response_time":
                actual = response_time_ms
                passed = False
                message = ""

                try:
                    max_ms = float(expected)
                    if actual is None:
                        message = "No response time available."
                    elif operator in ("less_than", "<"):
                        passed = (actual < max_ms)
                        message = f"Response time {actual}ms {'<' if passed else '>='} threshold {max_ms}ms."
                    elif operator in ("less_than_or_equal", "<=", "equals"):
                        passed = (actual <= max_ms)
                        message = f"Response time {actual}ms {'<=' if passed else '>'} threshold {max_ms}ms."
                    else:
                        message = f"Unsupported operator '{operator}' for response_time."
                except (ValueError, TypeError):
                    message = f"Expected response time threshold must be numeric, got '{expected}'."

                results.append({
                    "rule": rule,
                    "passed": passed,
                    "actual": actual,
                    "message": message,
                })

            # 3. JSON Field Assertion
            elif rule_type == "json_field":
                path = str(target or rule.get("path", "")).strip()
                if not is_valid_json:
                    results.append({
                        "rule": rule,
                        "passed": False,
                        "actual": None,
                        "message": "Response body is not valid JSON.",
                    })
                    continue

                found, actual_val = extract_json_path(parsed_json, path)

                if operator == "exists":
                    passed = found
                    message = f"Field '{path}' {'exists' if passed else 'was not found'}."
                elif not found:
                    passed = False
                    message = f"Field '{path}' was not found in response JSON."
                elif operator in ("equals", "=="):
                    passed = (actual_val == expected)
                    message = f"Field '{path}': expected {expected!r}, got {actual_val!r}."
                elif operator in ("not_equals", "!="):
                    passed = (actual_val != expected)
                    message = f"Field '{path}': expected not {expected!r}, got {actual_val!r}."
                elif operator == "contains":
                    try:
                        passed = expected in actual_val
                        message = f"Field '{path}': {'contains' if passed else 'does not contain'} {expected!r}."
                    except TypeError:
                        passed = False
                        message = f"Field '{path}' value cannot be searched with 'contains'."
                elif operator == "is_null":
                    passed = (actual_val is None)
                    message = f"Field '{path}' {'is null' if passed else 'is not null'}."
                else:
                    passed = False
                    message = f"Unsupported operator '{operator}' for json_field."

                results.append({
                    "rule": rule,
                    "passed": passed,
                    "actual": actual_val if found else None,
                    "message": message,
                })

            # 4. Header Assertion
            elif rule_type == "header":
                header_name = str(target or rule.get("name", "")).strip().lower()
                headers_lower = {k.lower(): v for k, v in (response_headers or {}).items()}
                actual_val = headers_lower.get(header_name)

                passed = False
                message = ""

                if operator == "exists":
                    passed = (actual_val is not None)
                    message = f"Header '{header_name}' {'exists' if passed else 'was not present'}."
                elif actual_val is None:
                    passed = False
                    message = f"Header '{header_name}' was not found in response headers."
                elif operator in ("equals", "=="):
                    passed = (actual_val == str(expected))
                    message = f"Header '{header_name}': expected {expected!r}, got {actual_val!r}."
                elif operator == "contains":
                    passed = (str(expected).lower() in actual_val.lower())
                    message = f"Header '{header_name}': {'contains' if passed else 'does not contain'} {expected!r}."
                else:
                    message = f"Unsupported operator '{operator}' for header assertion."

                results.append({
                    "rule": rule,
                    "passed": passed,
                    "actual": actual_val,
                    "message": message,
                })

            else:
                results.append({
                    "rule": rule,
                    "passed": False,
                    "actual": None,
                    "message": f"Unknown assertion type '{rule_type}'. Supported: status_code, response_time, json_field, header.",
                })

        return results


assertion_engine = AssertionEngine()

