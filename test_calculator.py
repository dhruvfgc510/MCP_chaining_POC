"""
Unit tests for SCRUM-6 acceptance criteria:
  - Handle division by zero
  - Support float inputs
  - Return error JSON for invalid ops
"""

import pytest
from calculator import calculate


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestAddition:
    def test_integer_addition(self):
        assert calculate({"op": "+", "a": 5, "b": 3}) == {"result": 8}

    def test_float_addition(self):
        assert calculate({"op": "+", "a": 2.5, "b": 1.5}) == {"result": 4}

    def test_negative_addition(self):
        assert calculate({"op": "+", "a": -4, "b": 2}) == {"result": -2}


class TestSubtraction:
    def test_integer_subtraction(self):
        assert calculate({"op": "-", "a": 10, "b": 4}) == {"result": 6}

    def test_float_subtraction(self):
        result = calculate({"op": "-", "a": 5.5, "b": 2.2})
        assert abs(result["result"] - 3.3) < 1e-9

    def test_result_is_negative(self):
        assert calculate({"op": "-", "a": 3, "b": 10}) == {"result": -7}


class TestMultiplication:
    def test_integer_multiplication(self):
        assert calculate({"op": "*", "a": 6, "b": 7}) == {"result": 42}

    def test_float_multiplication(self):
        assert calculate({"op": "*", "a": 2.5, "b": 4}) == {"result": 10}

    def test_multiply_by_zero(self):
        assert calculate({"op": "*", "a": 999, "b": 0}) == {"result": 0}


class TestDivision:
    def test_integer_division(self):
        assert calculate({"op": "/", "a": 10, "b": 2}) == {"result": 5}

    def test_float_division(self):
        result = calculate({"op": "/", "a": 7, "b": 2})
        assert result == {"result": 3.5}

    def test_float_inputs_division(self):
        assert calculate({"op": "/", "a": 9.0, "b": 3.0}) == {"result": 3}


# ---------------------------------------------------------------------------
# Acceptance criteria: error handling
# ---------------------------------------------------------------------------

class TestDivisionByZero:
    """SCRUM-6 AC: Handle division by zero."""

    def test_integer_zero(self):
        result = calculate({"op": "/", "a": 5, "b": 0})
        assert "error" in result
        assert "zero" in result["error"].lower()

    def test_float_zero(self):
        result = calculate({"op": "/", "a": 5.5, "b": 0.0})
        assert "error" in result


class TestInvalidOperator:
    """SCRUM-6 AC: Return error JSON for invalid ops."""

    def test_unknown_symbol(self):
        result = calculate({"op": "^", "a": 2, "b": 3})
        assert "error" in result

    def test_word_operator(self):
        result = calculate({"op": "add", "a": 2, "b": 3})
        assert "error" in result

    def test_empty_op(self):
        result = calculate({"op": "", "a": 2, "b": 3})
        assert "error" in result


class TestInputValidation:
    """SCRUM-6 AC: Input validation."""

    def test_missing_op(self):
        result = calculate({"a": 5, "b": 3})
        assert "error" in result

    def test_missing_operand(self):
        result = calculate({"op": "+", "a": 5})
        assert "error" in result

    def test_string_operand(self):
        result = calculate({"op": "+", "a": "five", "b": 3})
        assert "error" in result

    def test_non_dict_payload(self):
        result = calculate("not a dict")
        assert "error" in result

    def test_null_operand(self):
        result = calculate({"op": "+", "a": None, "b": 3})
        assert "error" in result


# ---------------------------------------------------------------------------
# Flask API integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """
    Uses the app factory so tests inject the real `calculate` function
    explicitly — mirrors how production boots the app, and makes it trivial
    to swap in a mock calculate_fn for isolated route tests in future.

    Real-life analogy: like a test kitchen that uses the same recipe (calculate)
    as the real restaurant, but operates in a controlled environment (TESTING=True).
    """
    from app import create_app
    from calculator import calculate
    test_app = create_app(calculate_fn=calculate)
    test_app.config["TESTING"] = True
    with test_app.test_client() as c:
        yield c


class TestAPI:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.get_json() == {"status": "ok"}

    def test_successful_calculation(self, client):
        response = client.post(
            "/calculate",
            json={"op": "+", "a": 5, "b": 3},
        )
        assert response.status_code == 200
        assert response.get_json() == {"result": 8}

    def test_division_by_zero_returns_400(self, client):
        response = client.post(
            "/calculate",
            json={"op": "/", "a": 5, "b": 0},
        )
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_invalid_op_returns_400(self, client):
        response = client.post(
            "/calculate",
            json={"op": "%", "a": 5, "b": 3},
        )
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_non_json_body_returns_400(self, client):
        response = client.post(
            "/calculate",
            data="not json",
            content_type="text/plain",
        )
        assert response.status_code == 400

    def test_float_inputs(self, client):
        response = client.post(
            "/calculate",
            json={"op": "*", "a": 2.5, "b": 4.0},
        )
        assert response.status_code == 200
        assert response.get_json() == {"result": 10}
