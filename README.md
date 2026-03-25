# Basic Calculator API — SCRUM-6

A lightweight REST API that performs arithmetic operations (add, subtract, multiply, divide) built with Python + Flask.

---

## Project Structure

```
MCP_chaining_POC/
├── calculator.py        # Core business logic (pure Python, no Flask dependency)
├── app.py               # Flask API layer
├── test_calculator.py   # Unit + integration tests (pytest)
├── requirements.txt     # Python dependencies
└── README.md
```

---

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python app.py
# Server running at http://127.0.0.1:5000
```

---

## API Reference

### `POST /calculate`

Perform an arithmetic operation.

**Request body**

| Field | Type          | Description                        |
|-------|---------------|------------------------------------|
| `op`  | string        | Operator: `+`, `-`, `*`, `/`       |
| `a`   | int or float  | Left operand                       |
| `b`   | int or float  | Right operand                      |

**Success response** — `200 OK`

```json
{"result": 8}
```

**Error response** — `400 Bad Request`

```json
{"error": "Division by zero is not allowed."}
```

---

## Usage Examples

### Addition
```bash
curl -X POST http://127.0.0.1:5000/calculate \
     -H "Content-Type: application/json" \
     -d '{"op": "+", "a": 5, "b": 3}'
# {"result": 8}
```

### Subtraction
```bash
curl -X POST http://127.0.0.1:5000/calculate \
     -H "Content-Type: application/json" \
     -d '{"op": "-", "a": 10, "b": 4}'
# {"result": 6}
```

### Multiplication with floats
```bash
curl -X POST http://127.0.0.1:5000/calculate \
     -H "Content-Type: application/json" \
     -d '{"op": "*", "a": 2.5, "b": 4}'
# {"result": 10}
```

### Division
```bash
curl -X POST http://127.0.0.1:5000/calculate \
     -H "Content-Type: application/json" \
     -d '{"op": "/", "a": 7, "b": 2}'
# {"result": 3.5}
```

### Division by zero (error case)
```bash
curl -X POST http://127.0.0.1:5000/calculate \
     -H "Content-Type: application/json" \
     -d '{"op": "/", "a": 5, "b": 0}'
# {"error": "Division by zero is not allowed."}
```

### Invalid operator (error case)
```bash
curl -X POST http://127.0.0.1:5000/calculate \
     -H "Content-Type: application/json" \
     -d '{"op": "^", "a": 2, "b": 3}'
# {"error": "Invalid operator '^'. Supported: ['+', '-', '*', '/']."}
```

### Health check
```bash
curl http://127.0.0.1:5000/health
# {"status": "ok"}
```

---

## Running Tests

```bash
pytest test_calculator.py -v
```

All tests cover the SCRUM-6 acceptance criteria:
- Division by zero handling
- Float input support
- Error JSON for invalid operators
- Missing/malformed fields

---

## Jira Reference

| Field    | Value   |
|----------|---------|
| Issue    | SCRUM-6 |
| Project  | Agentic Flow POC |
| Priority | Medium  |
| Status   | To Do   |
