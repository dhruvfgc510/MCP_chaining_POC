import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_MAX_ATTEMPTS = 6

_SENSITIVE_LOG_KEYS = {"word", "password", "secret", "token"}


def _sanitize_raw_input_for_log(value: Any, max_chars: int = 120) -> str:
    """Return a sanitized, truncated string for logging — strips control chars."""
    if value is None:
        return "<None>"
    s = str(value).replace("\n", "\\n").replace("\r", "\\r")
    return s[:max_chars] + "...[truncated]" if len(s) > max_chars else s


def _should_redact_key(key: str) -> bool:
    """Return True if the key (case-insensitive) contains any sensitive token."""
    if not isinstance(key, str):
        return False
    kl = key.lower()
    return any(s in kl for s in _SENSITIVE_LOG_KEYS)


def _sanitize_value_for_log(value: Any, max_chars: int = 120) -> Any:
    """Sanitize a primitive value for safe logging."""
    if value is None:
        return "<None>"
    if isinstance(value, (int, float, bool)):
        return value
    s = str(value).replace("\n", "\\n").replace("\r", "\\r")
    return s[:max_chars] + "...[truncated]" if len(s) > max_chars else s


def _redact_parsed_payload_for_log(data: Any, max_string_len: int = 120) -> Any:
    """Recursively redact sensitive keys and sanitize values for safe logging."""
    if isinstance(data, dict):
        return {
            k: "<redacted>" if _should_redact_key(k) else _redact_parsed_payload_for_log(v, max_string_len)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_redact_parsed_payload_for_log(item, max_string_len) for item in data]
    return _sanitize_value_for_log(data, max_string_len)


def build_display(word: str, guessed: List[str]) -> str:
    """Return the word with unguessed letters replaced by '_'."""
    return "".join(c if c in guessed else "_" for c in word)


def is_word_complete(word: str, guessed: List[str]) -> bool:
    """Return True if every letter in the word has been guessed."""
    return all(c in guessed for c in word)


def validate_letter(raw: Any) -> Optional[str]:
    """Normalize input to a single lowercase letter; return None if invalid."""
    if raw is None:
        return None
    s = str(raw).lower().strip()
    return s if len(s) == 1 and s.isalpha() else None


def play_core(
    letter: str,
    word: str,
    guessed_letters: List[str],
    remaining_attempts: int,
) -> Dict[str, Any]:
    """Evaluate one letter guess and return the updated game state."""
    if letter in guessed_letters:
        return {
            "display": build_display(word, guessed_letters),
            "guessed_letters": guessed_letters,
            "remaining_attempts": remaining_attempts,
            "result": "already_guessed",
        }

    updated_guessed = guessed_letters + [letter]
    hit = letter in word
    new_remaining = remaining_attempts if hit else remaining_attempts - 1
    display = build_display(word, updated_guessed)

    if is_word_complete(word, updated_guessed):
        result = "win"
    elif new_remaining <= 0:
        result = "lose"
    else:
        result = "in_progress"

    response: Dict[str, Any] = {
        "display": display,
        "guessed_letters": updated_guessed,
        "remaining_attempts": new_remaining,
        "result": result,
    }
    if result == "lose":
        response["word"] = word
    return response


def play(input_data: Any) -> Dict[str, Any]:
    """
    Accept a dict and run one letter-guess round.

    Required: "letter", "word"
    Optional: "guessed_letters", "remaining_attempts"
    """
    if not isinstance(input_data, dict):
        logger.warning("play() received non-dict input: %s", type(input_data))
        return {"error": "Invalid input"}

    raw_letter = input_data.get("letter")
    letter = validate_letter(raw_letter)
    if letter is None:
        return {"error": "Invalid letter: must be a single alphabetic character"}

    word_raw = input_data.get("word")
    if not word_raw or not isinstance(word_raw, str):
        return {"error": "Missing or invalid 'word'"}
    word = word_raw.lower().strip()
    if not word.isalpha():
        return {"error": "Word must contain only alphabetic characters"}

    guessed_raw = input_data.get("guessed_letters", [])
    if not isinstance(guessed_raw, list):
        return {"error": "Invalid 'guessed_letters': must be a list"}
    guessed_letters = [str(g).lower() for g in guessed_raw if g]

    raw_remaining = input_data.get("remaining_attempts", DEFAULT_MAX_ATTEMPTS)
    try:
        remaining_attempts = int(raw_remaining)
        if remaining_attempts < 0:
            raise ValueError("remaining_attempts must be non-negative")
    except (TypeError, ValueError) as exc:
        logger.warning("Invalid 'remaining_attempts' value provided (%s)", type(raw_remaining).__name__)
        return {"error": "Invalid 'remaining_attempts': must be a non-negative integer"}

    return play_core(letter, word, guessed_letters, remaining_attempts)


def play_json(json_input: str) -> str:
    """Accept a JSON string, run one letter-guess round, return a JSON string."""
    logger.debug("play_json() called; input_summary=%s", _sanitize_raw_input_for_log(json_input))
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

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Parsed JSON payload (sanitized): %s", _redact_parsed_payload_for_log(data))

    try:
        result = play(data)
    except Exception as exc:
        logger.exception("Unexpected error while executing play(): %s", exc)
        return json.dumps({"error": "Internal error"})
    return json.dumps(result)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    test_cases = [
        '{"letter": "p", "word": "python", "guessed_letters": [], "remaining_attempts": 6}',
        '{"letter": "y", "word": "python", "guessed_letters": ["p"], "remaining_attempts": 6}',
        '{"letter": "z", "word": "python", "guessed_letters": ["p", "y"], "remaining_attempts": 6}',
        '{"letter": "p", "word": "python", "guessed_letters": ["p", "y"], "remaining_attempts": 5}',
        '{"letter": "t", "word": "hi", "guessed_letters": ["h"], "remaining_attempts": 1}',
        '{"letter": "i", "word": "hi", "guessed_letters": ["h"], "remaining_attempts": 5}',
        '{"letter": "ab", "word": "python"}',
        '{"word": "python"}',
        '{"letter": "a", "word": "python", "remaining_attempts": "bad"}',
        '"not-a-dict"',
        'bad-json',
    ]

    for tc in test_cases:
        print(f"Input : {tc}")
        print(f"Output: {play_json(tc)}\n")
