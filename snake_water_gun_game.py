import json
import random
import logging
import re as _re
from typing import Callable, Optional, Dict, Any

logger = logging.getLogger(__name__)

VALID_CHOICES = {"snake", "water", "gun"}
WINS_AGAINST = {"snake": "water", "water": "gun", "gun": "snake"}
_CTL = _re.compile(r"[\x00-\x1f\x7f]+")


def _safe(v: Any, n: int = 120) -> str:
    return _CTL.sub(" ", str(v))[:n]


def normalize_choice(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    try:
        return str(raw).lower()
    except Exception:
        logger.exception("Failed to normalize choice for input: %r", raw)
        return None


def is_valid_choice(choice: Optional[str]) -> bool:
    return choice in VALID_CHOICES


def determine_result(player: str, computer: str) -> str:
    if player == computer:
        return "draw"
    return "win" if WINS_AGAINST[player] == computer else "lose"


def play_core(player: str, computer: Optional[str] = None, chooser: Callable[[list], str] = random.choice) -> Dict[str, str]:
    if not is_valid_choice(player):
        logger.warning("Invalid player choice: %s", _safe(player))
        return {"error": "Invalid choice"}
    if computer is None:
        computer = chooser(list(VALID_CHOICES))
        logger.debug("Computer choice randomized to: %s", computer)
    elif not is_valid_choice(computer):
        logger.warning("Invalid computer choice: %s", _safe(computer))
        return {"error": "Invalid choice"}
    result = determine_result(player, computer)
    logger.info("Game result: player=%s computer=%s result=%s", player, computer, result)
    return {"result": result, "computer": computer}


def play(input_data: Any, chooser: Callable[[list], str] = random.choice) -> Dict[str, str]:
    logger.debug("play() called input_type=%s", type(input_data).__name__)
    if not isinstance(input_data, dict):
        logger.warning("play() received non-dict input: %s", type(input_data).__name__)
        return {"error": "Invalid choice"}
    player = normalize_choice(input_data.get("player"))
    if player is None:
        return {"error": "Invalid choice"}
    computer_raw = input_data.get("computer")
    computer = normalize_choice(computer_raw) if computer_raw is not None else None
    return play_core(player, computer, chooser=chooser)


def play_json(json_input: str, chooser: Callable[[list], str] = random.choice) -> str:
    logger.debug("play_json() called input_len=%d", len(str(json_input)))
    try:
        data = json.loads(json_input)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("Failed to parse JSON; preview=%s error=%s", _safe(json_input), exc)
        return json.dumps({"error": "Invalid choice"})
    if not isinstance(data, dict):
        return json.dumps({"error": "Invalid choice"})
    try:
        return json.dumps(play(data, chooser=chooser))
    except Exception:
        logger.exception("Unexpected error in play()")
        return json.dumps({"error": "Invalid choice"})


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    test_cases = [
        '{"player": "snake", "computer": "water"}',
        '{"player": "water", "computer": "gun"}',
        '{"player": "Gun", "computer": "Snake"}',
        '{"player": "snake"}',
        '{"player": "fire"}',
        '"snake"',
        'not-json',
    ]
    for tc in test_cases:
        print(f"Input : {tc}")
        print(f"Output: {play_json(tc)}\n")
