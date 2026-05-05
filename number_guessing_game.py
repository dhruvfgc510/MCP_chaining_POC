import hashlib
import logging
import random
from typing import Callable

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 7
NUMBER_RANGE = (1, 100)


def _hash_secret(secret: int) -> str:
    return hashlib.sha256(str(secret).encode()).hexdigest()[:8]


def generate_secret(
    low: int = NUMBER_RANGE[0],
    high: int = NUMBER_RANGE[1],
    randint: Callable[[int, int], int] = random.randint,
) -> int:
    if not isinstance(low, int) or not isinstance(high, int):
        raise TypeError("low and high must be integers")
    if low > high:
        raise ValueError(f"Invalid range: low ({low}) must be <= high ({high})")
    return randint(low, high)


def evaluate_guess(guess: int, secret: int) -> str:
    if guess < secret:
        return "too low"
    if guess > secret:
        return "too high"
    return "correct"


def play_round(
    secret: int,
    max_attempts: int = MAX_ATTEMPTS,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> bool:
    """Run one interactive round; return True if the player wins."""
    if not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError("max_attempts must be a positive integer")

    low, high = NUMBER_RANGE
    logger.info("Starting round: range=%d-%d max_attempts=%d", low, high, max_attempts)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Round secret_hash=%s", _hash_secret(secret))

    print_fn(f"Guess the number between {low} and {high}. You have {max_attempts} attempts.")

    for attempt in range(1, max_attempts + 1):
        try:
            raw = input_fn(f"Attempt {attempt}/{max_attempts}: ")
        except (EOFError, KeyboardInterrupt):
            print_fn("\nInput interrupted. Exiting the game.")
            logger.info("User interrupted input on attempt %d", attempt)
            return False
        except Exception as exc:
            print_fn("An input error occurred. Exiting the game.")
            logger.exception("Unexpected exception from input_fn: %s", exc)
            return False

        if not isinstance(raw, str):
            print_fn("Invalid input received. Exiting the game.")
            logger.warning("input_fn returned non-str type %s on attempt %d", type(raw), attempt)
            return False

        raw = raw.strip()
        try:
            guess = int(raw)
        except ValueError:
            print_fn("Please enter a valid integer.")
            continue

        if guess < low or guess > high:
            print_fn(f"Please enter a number between {low} and {high}.")
            continue

        hint = evaluate_guess(guess, secret)
        logger.debug("attempt=%d guess=%d hint=%s", attempt, guess, hint)

        if hint == "correct":
            print_fn(f"Correct! You guessed it in {attempt} attempt(s).")
            logger.info("Round finished: result=win attempts=%d", attempt)
            return True
        print_fn(f"Hint: {hint}.")

    print_fn(f"Out of attempts. The number was {secret}.")
    logger.info("Round finished: result=loss attempts=%d", max_attempts)
    return False


def main(
    randint: Callable[[int, int], int] = random.randint,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> None:
    try:
        secret = generate_secret(randint=randint)
    except Exception as exc:
        logger.exception("Failed to generate secret number: %s", exc)
        print_fn("Internal error: could not start the game.")
        return

    try:
        play_round(secret, input_fn=input_fn, print_fn=print_fn)
    except (KeyboardInterrupt, EOFError):
        print_fn("\nGame interrupted. Goodbye.")
        logger.info("Game interrupted in main.")
    except Exception as exc:
        logger.exception("Unexpected error during game: %s", exc)
        print_fn("An unexpected error occurred. Exiting the game.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
