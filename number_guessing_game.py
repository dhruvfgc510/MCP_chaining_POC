import json
import random
import logging
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_MIN = 1
DEFAULT_MAX = 100
DEFAULT_MAX_ATTEMPTS = 7


def _safe_preview(value: Any, max_chars: int = 120) -> str:
    """Return a sanitized, truncated string for logging — strips control chars."""
    if value is None:
        return "<None>"
    s = str(value).replace("\n", "\\n").replace("\r", "\\r")
    return s[:max_chars] + "...[truncated]" if len(s) > max_chars else s


def safe_int(value: Any, name: str, default: int) -> Tuple[Optional[int], Optional[str]]:
    """Parse value as int; return (parsed_value, None) or (None, error_message)."""
    try:
        return default if value is None else int(value), None
    except (TypeError, ValueError):
        return None, f"Invalid numeric value for '{name}': {value!r}"


def validate_guess(guess: Any, min_val: int, max_val: int) -> Optional[int]:
    """Parse and range-check a guess; return None if invalid."""
    try:
        value = int(guess)
    except (TypeError, ValueError):
        return None
    return value if min_val <= value <= max_val else None


def evaluate_guess(
    guess: int,
    target: int,
    attempts_made: int,
    max_attempts: int,
) -> Dict[str, Any]:
    """Return the result of a single guess against the target."""
    new_attempts = attempts_made + 1
    if guess == target:
        return {"hint": "correct", "attempts_made": new_attempts, "target": target, "result": "win"}
    hint = "too high" if guess > target else "too low"
    if new_attempts >= max_attempts:
        return {"hint": hint, "attempts_made": new_attempts, "target": target, "result": "lose"}
    return {"hint": hint, "attempts_made": new_attempts, "result": "in_progress"}


def play_core(
    guess: int,
    target: int,
    attempts_made: int,
    max_attempts: int,
) -> Dict[str, Any]:
    """Core game logic — evaluate one guess."""
    return evaluate_guess(guess, target, attempts_made, max_attempts)


def play(
    input_data: Any,
    chooser: Callable[[int, int], int] = random.randint,
) -> Dict[str, Any]:
    """
    Accept a dict and run one guess round.

    Required: "guess"
    Optional: "target", "attempts_made", "max_attempts", "min_val", "max_val"
    """
    if not isinstance(input_data, dict):
        logger.warning("play() received non-dict input: %s", type(input_data))
        return {"error": "Invalid input"}

    min_val, err = safe_int(input_data.get("min_val"), "min_val", DEFAULT_MIN)
    if err:
        return {"error": err}
    max_val, err = safe_int(input_data.get("max_val"), "max_val", DEFAULT_MAX)
    if err:
        return {"error": err}
    if min_val > max_val:
        return {"error": f"'min_val' ({min_val}) must be <= 'max_val' ({max_val})"}

    max_attempts, err = safe_int(input_data.get("max_attempts"), "max_attempts", DEFAULT_MAX_ATTEMPTS)
    if err:
        return {"error": err}
    if max_attempts <= 0:
        return {"error": "'max_attempts' must be a positive integer"}

    attempts_made, err = safe_int(input_data.get("attempts_made"), "attempts_made", 0)
    if err:
        return {"error": err}
    if attempts_made < 0:
        return {"error": "'attempts_made' must be non-negative"}
    if attempts_made >= max_attempts:
        return {"error": "'attempts_made' must be less than 'max_attempts'"}

    raw_guess = input_data.get("guess")
    if raw_guess is None:
        return {"error": "Missing 'guess'"}
    guess = validate_guess(raw_guess, min_val, max_val)
    if guess is None:
        return {"error": f"Guess must be an integer between {min_val} and {max_val}"}

    target_raw = input_data.get("target")
    if target_raw is not None:
        try:
            target = int(target_raw)
        except (TypeError, ValueError):
            return {"error": "Invalid target"}
        if not (min_val <= target <= max_val):
            return {"error": f"Target must be an integer between {min_val} and {max_val}"}
    else:
        target = chooser(min_val, max_val)

    return play_core(guess, target, attempts_made, max_attempts)


def play_json(
    json_input: str,
    chooser: Callable[[int, int], int] = random.randint,
) -> str:
    """Accept a JSON string, run one guess round, return a JSON string."""
    logger.debug("play_json() called; input_preview=%s", _safe_preview(json_input, max_chars=120))
    try:
        data = json.loads(json_input)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error(
            "Failed to parse JSON input: length=%d, type=%s; error: %s",
            len(str(json_input)) if json_input is not None else 0,
            type(json_input).__name__,
            exc,
        )
        return json.dumps({"error": "Invalid JSON"})

    if not isinstance(data, dict):
        logger.warning("Parsed JSON is not a dict: %s", type(data))
        return json.dumps({"error": "Invalid input"})

    try:
        result = play(data, chooser=chooser)
    except Exception as exc:
        logger.exception("Unexpected error while processing play(): %s", exc)
        return json.dumps({"error": "Internal error"})
    return json.dumps(result)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    test_cases = [
        '{"guess": 50, "target": 73, "attempts_made": 0}',
        '{"guess": 80, "target": 73, "attempts_made": 1}',
        '{"guess": 73, "target": 73, "attempts_made": 2}',
        '{"guess": 50, "target": 50, "attempts_made": 6, "max_attempts": 7}',
        '{"guess": 999, "target": 50}',
        '{"target": 50}',
        '{"guess": 50, "min_val": "bad"}',
        '{"guess": 50, "target": 200, "min_val": 1, "max_val": 100}',
        '"not-a-dict"',
        'bad-json',
    ]

    for tc in test_cases:
        print(f"Input : {tc}")
        print(f"Output: {play_json(tc)}\n")
