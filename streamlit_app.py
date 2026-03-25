"""
Streamlit Frontend for the Calculator App (SCRUM-7).

Calls the Flask backend POST /calculate endpoint.
Provides two number inputs, an operator dropdown, a Calculate button,
and displays the result or a user-friendly error message.

Run locally (make sure the Flask backend is running first):
    streamlit run streamlit_app.py

Real-life analogy: Think of this as a physical calculator keypad (Streamlit UI)
connected via a wire (HTTP) to a powerful computing chip (Flask backend).
The keypad only handles display; all math happens inside the chip.

Improvements applied per Codesherlock power_analysis:
  - Modularity      : UI, network, and rendering split into focused functions
  - Exception Handling : raise_for_status + explicit JSON-decode guard + 4xx vs 5xx
  - Monitoring/Logging : structured logger + UUID correlation IDs + X-Request-ID header
  - Dependency Injection: backend URL read from env; call_backend accepts injectable deps
  - Input Validation : finite-number guard + client-side division-by-zero pre-check
"""

import json
import logging
import math
import os
import uuid

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration — read from environment so tests or CI can override without
# touching source code.  Real-life analogy: a restaurant's kitchen has a
# single configuration board (env vars) that chefs (code) read from.
# ---------------------------------------------------------------------------
BACKEND_URL = os.getenv("CALCULATOR_BACKEND_URL", "http://127.0.0.1:5000/calculate")

OPERATOR_LABELS: dict[str, str] = {
    "Addition (+)": "+",
    "Subtraction (-)": "-",
    "Multiplication (×)": "*",
    "Division (÷)": "/",
}

# ---------------------------------------------------------------------------
# Structured logging — module-level logger so every function uses the same
# logger, and a StreamHandler with a timestamped format.
# Real-life analogy: a flight's black box — every action is recorded so we
# can reconstruct exactly what happened when something goes wrong.
# ---------------------------------------------------------------------------
logger = logging.getLogger("streamlit_calculator")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setLevel(logging.INFO)
    _handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Network layer — isolated and injectable for testability
# ---------------------------------------------------------------------------

def call_backend(
    payload: dict,
    backend_url: str = BACKEND_URL,
    timeout: int = 5,
    http_post=requests.post,
) -> tuple[bool, dict | str]:
    """
    POST payload to the calculator backend and return (ok, result).

    ok == True  -> result is the parsed JSON dict from the backend.
    ok == False -> result is a user-friendly error string.

    Args:
        payload     : {"op": str, "a": float, "b": float}
        backend_url : injectable so tests pass a fake endpoint without patching globals
        timeout     : seconds before the request is abandoned
        http_post   : injectable transport callable; defaults to requests.post so
                      unit tests can swap in a lightweight fake (Dependency Injection)

    Real-life analogy: like an embassy that accepts your application (payload),
    sends it to the consul (backend), and returns either a visa (result) or a
    rejection letter (error string) — always structured, never raw jargon.
    """
    request_id = str(uuid.uuid4())
    headers = {"X-Request-ID": request_id}

    logger.info(
        "[req=%s] Sending calculate request to %s payload=%r",
        request_id, backend_url, payload,
    )

    try:
        response = http_post(backend_url, json=payload, headers=headers, timeout=timeout)
    except requests.exceptions.ConnectionError:
        logger.exception("[req=%s] ConnectionError while calling backend", request_id)
        return False, (
            f"Cannot reach the calculator backend. "
            f"Please start the Flask server with: `python app.py`  (ref: {request_id})"
        )
    except requests.exceptions.Timeout:
        logger.exception("[req=%s] Timeout while calling backend", request_id)
        return False, (
            f"The request timed out. The backend may be overloaded. "
            f"Please try again.  (ref: {request_id})"
        )
    except requests.exceptions.RequestException:
        logger.exception("[req=%s] Network error while calling backend", request_id)
        return False, (
            f"Network error while contacting the backend. "
            f"Please check your connection and try again.  (ref: {request_id})"
        )

    logger.info(
        "[req=%s] Received response status=%s body_snippet=%r",
        request_id, response.status_code, response.text[:120],
    )

    # Check HTTP status before attempting to decode body
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        err_msg: str | None = None
        try:
            err_body = response.json()
            if isinstance(err_body, dict):
                err_msg = err_body.get("error") or err_body.get("message")
        except (ValueError, json.JSONDecodeError):
            err_msg = response.text.strip()[:200]

        if 400 <= response.status_code < 500:
            detail = f" — {err_msg}" if err_msg else ""
            logger.warning(
                "[req=%s] HTTP %s client error%s", request_id, response.status_code, detail
            )
            return False, (
                f"Request invalid ({response.status_code}){detail}. "
                f"Please check your inputs.  (ref: {request_id})"
            )
        logger.error(
            "[req=%s] HTTP %s server error — %s", request_id, response.status_code, err_msg
        )
        return False, (
            f"Server error ({response.status_code}). "
            f"Please try again later.  (ref: {request_id})"
        )

    # Parse JSON body
    try:
        data = response.json()
    except (ValueError, json.JSONDecodeError):
        logger.exception("[req=%s] Failed to decode JSON response", request_id)
        return False, (
            f"Invalid response from backend: expected JSON. "
            f"Please try again or contact support.  (ref: {request_id})"
        )

    if not isinstance(data, dict):
        logger.error("[req=%s] Unexpected response shape: %r", request_id, data)
        return False, f"Unexpected response format from backend.  (ref: {request_id})"

    logger.info("[req=%s] call_backend succeeded data=%r", request_id, data)
    return True, data


# ---------------------------------------------------------------------------
# UI components — each function owns one screen region (Modularity)
# ---------------------------------------------------------------------------

def render_inputs() -> tuple[float, float, str]:
    """
    Render the two number inputs and the operator dropdown.
    Returns (num_a, num_b, operator_symbol).

    Real-life analogy: the keypad of an ATM — it only collects your inputs
    and hands them off; it does no computation itself.
    """
    col1, col2 = st.columns(2)
    with col1:
        num_a = st.number_input(
            "First Number",
            value=0.0,
            format="%g",
            key="num_a",
            help="Enter the first operand. Example: 10",
        )
    with col2:
        num_b = st.number_input(
            "Second Number",
            value=0.0,
            format="%g",
            key="num_b",
            help="Enter the second operand. Example: 5",
        )

    operator_label = st.selectbox(
        "Operation",
        options=list(OPERATOR_LABELS.keys()),
        index=0,
        help="Choose the arithmetic operation to perform.",
    )
    operator = OPERATOR_LABELS[operator_label]
    return num_a, num_b, operator


def validate_inputs(num_a: float, num_b: float, operator: str) -> str | None:
    """
    Client-side input validation before hitting the backend.

    Returns an error message string if validation fails, or None if valid.

    Why validate on the frontend too? — Real-life analogy: a bouncer at a
    club (frontend) checks IDs before letting guests reach the dance floor
    (backend), saving the DJ (server) from interruptions.
    """
    if not (math.isfinite(num_a) and math.isfinite(num_b)):
        return (
            "Inputs must be finite numbers (not NaN or Infinity). "
            "Please correct the First Number and/or Second Number."
        )
    if operator == "/" and num_b == 0:
        return "Division by zero is not allowed. Please enter a non-zero Second Number."
    return None


def render_result(ok: bool, payload: dict, response_data: dict | str) -> None:
    """
    Display the backend's response (result or error) in the Streamlit UI.

    Keeps all UI output formatting in one place — changing the visual style
    of results only requires editing this function, nowhere else.
    """
    num_a, op, num_b = payload["a"], payload["op"], payload["b"]

    if not ok:
        st.error(f"**Error:** {response_data}")
        if isinstance(response_data, str) and "zero" in response_data.lower():
            st.warning(
                "Tip: Division by zero is mathematically undefined. "
                "Try using a non-zero Second Number."
            )
        return

    assert isinstance(response_data, dict)

    if "result" in response_data:
        result_value = response_data["result"]
        logger.info("Calculation succeeded: %s %s %s = %s", num_a, op, num_b, result_value)
        st.success(f"**Result:** `{num_a} {op} {num_b} = {result_value}`")
        st.metric(label="Calculation Result", value=result_value)
    else:
        error_msg = response_data.get("error", "Unknown error from backend.")
        logger.warning("Backend returned error payload: %s", error_msg)
        st.error(f"**Error:** {error_msg}")
        if "zero" in error_msg.lower():
            st.warning(
                "Tip: Division by zero is mathematically undefined. "
                "Try using a non-zero Second Number."
            )


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main(backend_url: str = BACKEND_URL) -> None:
    """
    Compose the full Streamlit page.

    Accepts backend_url as a parameter so integration tests or preview builds
    can point to a test server without changing source code (Dependency Injection).
    """
    st.set_page_config(
        page_title="Calculator",
        page_icon="🧮",
        layout="centered",
    )
    st.title("🧮 Calculator")
    st.caption("A clean, real-time calculator powered by a Flask backend.")
    st.divider()

    num_a, num_b, operator = render_inputs()
    st.divider()

    calculate_clicked = st.button("Calculate", type="primary", use_container_width=True)

    if calculate_clicked:
        validation_error = validate_inputs(num_a, num_b, operator)
        if validation_error:
            st.error(validation_error)
            st.stop()

        payload = {"op": operator, "a": float(num_a), "b": float(num_b)}

        with st.spinner("Calculating…"):
            ok, response = call_backend(payload, backend_url=backend_url)

        render_result(ok, payload, response)

    st.divider()
    st.caption("Backend: Flask `POST /calculate` · Frontend: Streamlit (SCRUM-7)")


if __name__ == "__main__":
    main()
