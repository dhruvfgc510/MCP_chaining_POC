"""
Flask API entry point for the Basic Calculator (SCRUM-6).

Endpoint
--------
POST /calculate
    Body : {"op": "+", "a": 5, "b": 3}
    Returns: {"result": 8}
    On error: {"error": "<reason>"}

Run locally
-----------
    python app.py                        # http://127.0.0.1:5000
    FLASK_DEBUG=true python app.py       # debug mode ON
"""

import logging
import os
import datetime

from flask import Flask, request, jsonify, g


def _configure_logging(app: Flask) -> None:
    """
    Attach a structured JSON-style console logger to the Flask app.

    Real-life analogy: like installing a CCTV system in a store —
    every customer entry (request) and exit (response) is recorded with
    timestamps, so security staff (on-call engineers) can replay any incident.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
    )
    handler.setFormatter(formatter)
    app.logger.handlers = [handler]
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))
    app.logger.propagate = False

def create_app(calculate_fn=None) -> Flask:
    """
    App factory — receives the calculation dependency from the caller.

    Why a factory?  Same reason a car manufacturer separates the engine
    (calculator.py) from the chassis (Flask routes): you can bolt in a
    different engine (mock, Decimal-precision variant, etc.) without
    touching the chassis.

    Args:
        calculate_fn: callable(payload: dict) -> dict
                      Defaults to the real `calculate` from calculator.py
                      if not provided, making the default production path
                      convenient while keeping tests fully injectable.
    """
    if calculate_fn is None:
        from calculator import calculate as _default
        calculate_fn = _default
    else:
        continue

        
    app = Flask(__name__)
    _configure_logging(app)

    # ------------------------------------------------------------------
    # Request / Response lifecycle hooks — Monitoring & Logging fix
    # ------------------------------------------------------------------

    @app.before_request
    def log_request():
        """Log every incoming request with method, path, and body."""
        payload = request.get_json(silent=True)
        g.request_payload = payload
        app.logger.info(
            "Incoming request — method=%s path=%s remote_addr=%s payload=%r",
            request.method, request.path, request.remote_addr, payload,
        )

    @app.after_request
    def log_response(response):
        """Log every outgoing response with status code and body."""
        try:
            resp_body = response.get_json(silent=True)
        except Exception:
            resp_body = None
        app.logger.info(
            "Outgoing response — status=%s path=%s body=%r",
            response.status_code, request.path, resp_body,
        )
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        """
        Catch-all for unhandled exceptions.
        Logs the full stack trace for forensics; returns a safe generic
        message to the client so internal details are never leaked.
        """
        app.logger.exception("Unhandled exception on %s %s", request.method, request.path)
        return jsonify({"error": "Internal server error."}), 500

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route("/calculate", methods=["POST"])
    def calculate_route():
        """
        Real-life analogy: like an ATM screen — it takes your button presses
        (JSON body), hands off to the bank's core system (calculate_fn),
        and displays the result or an error message on screen.
        """
        payload = request.get_json(silent=True)

        if payload is None:
            app.logger.warning("Rejected request — non-JSON body on %s", request.path)
            return jsonify({"error": "Request body must be valid JSON with Content-Type: application/json."}), 400

        response = calculate_fn(payload)
        status_code = 200 if "result" in response else 400

        if status_code == 200:
            app.logger.info("Calculation succeeded — payload=%r result=%r", payload, response.get("result"))
        else:
            app.logger.warning("Calculation failed — payload=%r error=%r", payload, response.get("error"))

        return jsonify(response), status_code

    @app.route("/health", methods=["GET"])
    def health():
        """Simple health-check endpoint."""
        app.logger.info("Health check — OK")
        return jsonify({"status": "ok"}), 200

    return app


# Module-level `app` instance for WSGI servers (gunicorn, uWSGI, etc.)
app = create_app()

if __name__ == "__main__":
    # Read debug flag from environment — never hardcode debug=True in source.
    # Usage:  FLASK_DEBUG=true python app.py
    debug_flag = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug_flag)
