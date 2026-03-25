"""
Core calculator logic for SCRUM-6.
Input:  {"op": "+", "a": 5, "b": 3}
Output: {"result": 8}  or  {"error": "..."}
"""

import logging

SUPPORTED_OPS = {"+", "-", "*", "/"}

# Module-level logger — real-life analogy: like a security camera above the
# bank teller's counter that records every transaction and every rejected cheque.
logger = logging.getLogger(__name__)


def _validate(payload: dict) -> tuple[bool, str]:
    """Return (is_valid, error_message). Empty string means no error."""
    if not isinstance(payload, dict):
        logger.warning("Validation failed: payload is not a dict — received %r", type(payload).__name__)
        return False, "Request body must be a JSON object."

    missing = [k for k in ("op", "a", "b") if k not in payload]
    if missing:
        logger.warning("Validation failed: missing field(s) %s in payload: %r", missing, payload)
        return False, f"Missing required field(s): {', '.join(missing)}."

    op = payload["op"]
    if op not in SUPPORTED_OPS:
        logger.warning("Validation failed: unsupported operator %r in payload: %r", op, payload)
        return False, f"Invalid operator '{op}'. Supported: {sorted(SUPPORTED_OPS)}."

    for field in ("a", "b"):
        val = payload[field]
        if not isinstance(val, (int, float)):
            logger.warning(
                "Validation failed: field '%s' is not numeric (got %r) in payload: %r",
                field, type(val).__name__, payload,
            )
            return False, f"Field '{field}' must be a number, got {type(val).__name__}."

    if op == "/" and payload["b"] == 0:
        logger.warning("Validation failed: division by zero attempted — payload: %r", payload)
        return False, "Division by zero is not allowed."

    return True, ""


def calculate(payload: dict) -> dict:
    """
    Perform the requested arithmetic operation.

    Real-life analogy: like a bank teller who validates your cheque (inputs)
    before processing the transaction (operation). Every validation failure
    and every completed transaction is logged for audit purposes.

    Args:
        payload: dict with keys 'op', 'a', 'b'
            op  – one of '+', '-', '*', '/'
            a   – left operand  (int or float)
            b   – right operand (int or float)

    Returns:
        {"result": <value>}  on success
        {"error":  <message>} on failure
    """
    try:
        is_valid, error_msg = _validate(payload)
        if not is_valid:
            return {"error": error_msg}

        op, a, b = payload["op"], float(payload["a"]), float(payload["b"])

        operations = {
            "+": lambda x, y: x + y,
            "-": lambda x, y: x - y,
            "*": lambda x, y: x * y,
            "/": lambda x, y: x / y,
        }

        result = operations[op](a, b)

        logger.info("Operation executed — op=%r  a=%s  b=%s  result=%s", op, a, b, result)

        # Return int when result is a whole number for cleaner output
        return {"result": int(result) if result == int(result) else result}

    except Exception:
        # Captures any unexpected arithmetic or runtime errors with full stack trace
        logger.exception("Unexpected error while processing payload: %r", payload)
        return {"error": "Internal error while processing request."}
