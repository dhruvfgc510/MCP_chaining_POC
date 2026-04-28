import random
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_LOW = 1
DEFAULT_HIGH = 100
DEFAULT_MAX_ATTEMPTS = 7


# ---------------------------------------------------------------------------
# Pure core helpers
# ---------------------------------------------------------------------------

def make_hint(guess: int, secret: int) -> str:
    """Return 'too_low', 'too_high', or 'correct'."""
    if guess < secret:
        return "too_low"
    if guess > secret:
        return "too_high"
    return "correct"


def evaluate_guess(
    guess: int,
    secret: int,
    attempts_used: int,
    max_attempts: int,
) -> Dict[str, Any]:
    """
    Evaluate a single guess against the secret number.

    Returns a dict with:
        hint            - 'too_low' | 'too_high' | 'correct'
        won             - True if guess is correct
        game_over       - True when won or no attempts remain
        attempts_used   - updated count after this guess
        attempts_left   - remaining attempts
    """
    hint = make_hint(guess, secret)
    won = hint == "correct"
    used = attempts_used + 1
    left = max_attempts - used
    game_over = won or left <= 0

    logger.debug(
        "evaluate_guess: guess=%d hint=%s used=%d left=%d",
        guess, hint, used, left,
    )
    return {
        "hint": hint,
        "won": won,
        "game_over": game_over,
        "attempts_used": used,
        "attempts_left": left,
    }


# ---------------------------------------------------------------------------
# Dict adapter
# ---------------------------------------------------------------------------

def play(input_data: Any) -> Dict[str, Any]:
    """
    Accept a dict with 'guess', 'secret', 'attempts_used', 'max_attempts'.
    Returns evaluation result or error dict.
    """
    if not isinstance(input_data, dict):
        return {"error": "Input must be a dict"}

    required = ("guess", "secret", "attempts_used", "max_attempts")
    for key in required:
        if key not in input_data:
            return {"error": f"Missing required field: {key}"}

    try:
        guess = int(input_data["guess"])
        secret = int(input_data["secret"])
        attempts_used = int(input_data["attempts_used"])
        max_attempts = int(input_data["max_attempts"])
    except (ValueError, TypeError) as exc:
        logger.warning("Type conversion failed: %s", exc)
        return {"error": "All fields must be integers"}

    if max_attempts <= 0:
        return {"error": "max_attempts must be positive"}
    if attempts_used < 0 or attempts_used >= max_attempts:
        return {"error": "attempts_used is out of valid range"}

    return evaluate_guess(guess, secret, attempts_used, max_attempts)


# ---------------------------------------------------------------------------
# Interactive CLI runner
# ---------------------------------------------------------------------------

def run_cli(
    low: int = DEFAULT_LOW,
    high: int = DEFAULT_HIGH,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    randint: Callable[[int, int], int] = random.randint,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    """Run an interactive number-guessing game in the terminal."""
    if not isinstance(low, int) or not isinstance(high, int):
        raise TypeError("low and high must be integers")
    if low > high:
        raise ValueError(f"Invalid range: low ({low}) must be <= high ({high})")
    if not isinstance(max_attempts, int) or max_attempts <= 0:
        raise ValueError("max_attempts must be a positive integer")
    if not callable(randint):
        raise TypeError("randint must be callable")

    try:
        secret = randint(low, high)
    except Exception as exc:
        raise RuntimeError(f"Failed to obtain secret from randint: {exc}") from exc

    attempts_used = 0

    output_fn(f"\nGuess the number between {low} and {high}.")
    output_fn(f"You have {max_attempts} attempt(s).\n")

    try:
        while True:
            try:
                raw = input_fn("Your guess: ")
            except EOFError:
                output_fn("\nInput closed. Exiting game.\n")
                return
            except KeyboardInterrupt:
                output_fn("\nGame interrupted by user. Goodbye!\n")
                return

            raw = raw.strip()
            try:
                guess = int(raw)
            except ValueError:
                output_fn("  Please enter a valid integer.\n")
                continue

            if guess < low or guess > high:
                output_fn(f"  Please enter a number between {low} and {high}.\n")
                continue

            result = evaluate_guess(guess, secret, attempts_used, max_attempts)
            attempts_used = result["attempts_used"]

            if result["won"]:
                output_fn(f"\n  Correct! You guessed it in {attempts_used} attempt(s). Well done!\n")
                return

            if result["game_over"]:
                output_fn(f"\n  No attempts left. The number was {secret}. Better luck next time!\n")
                return

            hint_msg = "Too high!" if result["hint"] == "too_high" else "Too low!"
            output_fn(f"  {hint_msg} {result['attempts_left']} attempt(s) remaining.\n")
    except Exception:
        logger.exception("Unexpected error in run_cli")
        output_fn("An unexpected error occurred. Please check the logs for details.")
        return


# ---------------------------------------------------------------------------
# Manual smoke-test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    run_cli()
