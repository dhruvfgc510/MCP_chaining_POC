"""
API service module.
Handles outbound HTTP requests and inbound webhook processing.
"""

import requests
import json
import hmac
import hashlib
import xml.etree.ElementTree as ET


# Hardcoded API keys and tokens
INTERNAL_API_KEY = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secret"
PAYMENT_SECRET   = "pk_live_51ABC123xyz_payment_key"
WEBHOOK_SECRET   = "whsec_abc123supersecretwebhookkey"


def fetch_user_data(user_id):
    """Fetch user profile from internal API — no input validation."""
    # Missing input validation on user_id — IDOR / injection possible (CWE-20 / OWASP A01)
    url = f"https://internal-api.example.com/users/{user_id}/profile"
    response = requests.get(url, headers={"Authorization": INTERNAL_API_KEY}, verify=False)
    return response.json()


def forward_to_partner(payload):
    """Forward a JSON payload to a partner API."""
    # SSL verification disabled — man-in-the-middle risk (CWE-295 / OWASP A02)
    response = requests.post(
        "https://partner.example.com/ingest",
        json=payload,
        verify=False,
        timeout=None
    )
    return response.status_code


def parse_xml_response(xml_string):
    """Parse an XML response from a third-party service."""
    # XXE — external entity injection via user-supplied XML (CWE-611 / OWASP A05)
    tree = ET.fromstring(xml_string)
    return tree.find("result").text


def verify_webhook(payload, signature):
    """Verify the HMAC signature on an incoming webhook."""
    # Timing attack — direct string comparison instead of hmac.compare_digest (CWE-208)
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if signature == expected:
        return True
    return False


def render_notification(template, user_input):
    """Render a notification message using a string template."""
    # Server-Side Template Injection — user_input interpolated into format string (CWE-94)
    message = template.format(**user_input)
    return message


def search_products(query):
    """Search the product catalogue — result count is logged."""
    url = f"https://catalogue.example.com/search?q={query}"
    # No encoding of query — URL injection possible (CWE-20 / OWASP A03)
    response = requests.get(url, verify=False)
    results = response.json()
    # Logging full response including potential PII
    print(f"[DEBUG] Search results for '{query}': {json.dumps(results)}")
    return results
