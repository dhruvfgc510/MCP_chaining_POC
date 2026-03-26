import json
import random
import logging
from typing import Callable, Optional, Dict, Any

logger = logging.getLogger(__name__)

VALID_CHOICES = {"stone", "paper", "scissors"}

# Rules: what each choice beats
WINS_AGAINST = {
    "stone": "scissors",
    "scissors": "paper",
    "paper": "stone",
}


# ---------------------------------------------------------------------------
# Pure core helpers
# ---------------------------------------------------------------------------

def normalize_choice(raw: Any) -> Optional[str]:
    """Lowercase-normalize a raw input; return None if it cannot be converted."""
    if raw is None:
        return None
    try:
        return str(raw).lower()
    except Exception:
        return None


def is_valid_choice(choice: Optional[str]) -> bool:
    """Return True only for the three valid game choices."""
    return choice in VALID_CHOICES


def determine_result(player: str, computer: str) -> str:
    """Return 'win', 'lose', or 'draw' from the player's perspective."""
    if player == computer:
        return "draw"
    return "win" if WINS_AGAINST[player] == computer else "lose"


# ---------------------------------------------------------------------------
# Core game function (pure, injectable randomness)
# ---------------------------------------------------------------------------

def play_core(
    player: str,
    computer: Optional[str] = None,
    chooser: Callable[[list], str] = random.choice,
) -> Dict[str, str]:
    """
    Core game logic operating on already-normalized strings.

    Args:
        player:   Normalized player choice (must be valid).
        computer: Normalized computer choice; random if None.
        chooser:  Callable used to pick a random choice (injectable for tests).

    Returns:
        dict with "result" key, or "error" key on invalid input.
    """
    if not is_valid_choice(player):
        logger.warning("Invalid player choice: %s", player)
        return {"error": "Invalid choice"}

    if computer is None:
        computer_choice = chooser(list(VALID_CHOICES))
        logger.debug("Computer choice randomized to: %s", computer_choice)
    else:
        computer_choice = computer
        if not is_valid_choice(computer_choice):
            logger.warning("Invalid computer choice: %s", computer_choice)
            return {"error": "Invalid choice"}

    result = determine_result(player, computer_choice)
    logger.info(
        "Game result",
        extra={"player": player, "computer": computer_choice, "result": result},
    )
    return {"result": result}


# ---------------------------------------------------------------------------
# Dict adapter
# ---------------------------------------------------------------------------

def play(
    input_data: Any,
    chooser: Callable[[list], str] = random.choice,
) -> Dict[str, str]:
    """
    Accept a dict input, validate/normalize, and delegate to play_core.

    Args:
        input_data: dict with "player" (required) and optional "computer".
        chooser:    Randomness provider (injectable for tests).

    Returns:
        dict with "result" or "error".
    """
    logger.debug("play() called with input_data=%s", input_data)

    # Defensive: ensure we received a mapping
    if not isinstance(input_data, dict):
        logger.warning("play() received non-dict input: %s", type(input_data))
        return {"error": "Invalid choice"}

    player = normalize_choice(input_data.get("player"))
    if player is None:
        logger.warning("Missing 'player' field in input: %s", input_data)
        return {"error": "Invalid choice"}

    computer_raw = input_data.get("computer")
    computer = normalize_choice(computer_raw) if computer_raw is not None else None

    return play_core(player, computer, chooser=chooser)


# ---------------------------------------------------------------------------
# JSON I/O adapter
# ---------------------------------------------------------------------------

def play_json(
    json_input: str,
    chooser: Callable[[list], str] = random.choice,
) -> str:
    """
    Accept a JSON string, run the game, and return a JSON string result.

    Args:
        json_input: JSON string e.g. '{"player": "stone", "computer": "paper"}'
        chooser:    Randomness provider (injectable for tests).

    Returns:
        JSON string e.g. '{"result": "lose"}'
    """
    logger.debug("play_json() called with json_input=%s", json_input)

    try:
        data = json.loads(json_input)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("Failed to parse JSON input: %s; error: %s", json_input, exc)
        return json.dumps({"error": "Invalid choice"})

    # Ensure parsed JSON is an object, not a string/list/number/null
    if not isinstance(data, dict):
        logger.warning("Parsed JSON is not a dict: %s", type(data))
        return json.dumps({"error": "Invalid choice"})

    try:
        result = play(data, chooser=chooser)
    except Exception as exc:
        logger.error("Unexpected error in play(): %s", exc, exc_info=True)
        return json.dumps({"error": "Invalid choice"})

    return json.dumps(result)


# ---------------------------------------------------------------------------
# Manual smoke-test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    test_cases = [
        '{"player": "stone", "computer": "paper"}',
        '{"player": "scissors", "computer": "scissors"}',
        '{"player": "Paper", "computer": "Stone"}',
        '{"player": "fire"}',
        '{"player": "stone"}',
        '"stone"',          # non-dict JSON
        'null',             # null JSON
        'not-json',         # malformed JSON
    ]

    for tc in test_cases:
        print(f"Input : {tc}")
        print(f"Output: {play_json(tc)}\n")
