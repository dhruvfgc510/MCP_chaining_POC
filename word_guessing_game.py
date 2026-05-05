import logging
import random
import unicodedata
from typing import Callable

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 6

WORD_POOL = [
    "python", "random", "computer", "secret", "puzzle",
    "banana", "jungle", "rocket", "pillow", "castle",
    "bridge", "candle", "flower", "planet", "stream",
]


def choose_word(
    pool: list[str] = WORD_POOL,
    choice_fn: Callable[[list], str] = random.choice,
) -> str:
    if not pool:
        raise ValueError("word pool is empty")
    try:
        candidate = choice_fn(pool)
    except Exception:
        logger.exception("choice_fn raised an exception while selecting a word")
        raise
    if not isinstance(candidate, str):
        raise ValueError("choice_fn returned a non-string word")
    return unicodedata.normalize("NFKC", candidate).lower()


def build_display(word: str, guessed: set[str]) -> str:
    return " ".join(ch if ch in guessed else "_" for ch in word)


def is_won(word: str, guessed: set[str]) -> bool:
    return all(ch in guessed for ch in word)


def play_round(
    word: str,
    max_attempts: int = MAX_ATTEMPTS,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> bool:
    """Run one interactive round; return True if the player wins."""
    if not isinstance(word, str) or not word:
        raise ValueError("Invalid word provided to play_round")

    # Auto-reveal non-alphabetic characters so they cannot block a win
    guessed: set[str] = {ch for ch in word if not ch.isalpha()}
    remaining = max_attempts

    print_fn(f"Word has {len(word)} letters. You have {max_attempts} wrong-guess attempts.")

    while remaining > 0:
        display = build_display(word, guessed)
        print_fn(f"\n  {display}")
        print_fn(f"  Guessed: {', '.join(sorted(guessed)) or 'none'}  |  Wrong attempts left: {remaining}")

        try:
            raw_input = input_fn("Guess a letter: ")
        except (EOFError, KeyboardInterrupt):
            print_fn("\nInput interrupted. Exiting the round.")
            return False
        except Exception:
            logger.exception("Unexpected exception from input_fn")
            print_fn("\nAn error occurred reading input. Exiting the round.")
            return False

        raw = raw_input.strip().lower()

        if len(raw) != 1 or not raw.isalpha():
            print_fn("Please enter a single letter (A-Z).")
            continue

        if raw in guessed:
            print_fn(f"You already guessed '{raw}'.")
            continue

        guessed.add(raw)
        # Log masked display only — never log the secret word
        masked = build_display(word, guessed)
        logger.debug("letter=%s guessed=%s masked=%s", raw, ", ".join(sorted(guessed)), masked)

        if raw in word:
            print_fn(f"Good — '{raw}' is in the word!")
        else:
            remaining -= 1
            print_fn(f"No '{raw}' in the word. Attempts left: {remaining}.")

        if is_won(word, guessed):
            print_fn(f"\nYou won! The word was '{word}'.")
            return True

    print_fn(f"\nOut of attempts. The word was '{word}'.")
    return False


def main(
    choice_fn: Callable[[list], str] = random.choice,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> None:
    try:
        word = choose_word(choice_fn=choice_fn)
    except Exception:
        logger.exception("Failed to select a word")
        print_fn("Unable to select a word to play. Exiting.")
        return

    try:
        play_round(word, input_fn=input_fn, print_fn=print_fn)
    except Exception:
        logger.exception("Unexpected failure during play_round")
        print_fn("An internal error occurred. Exiting.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    main()
