import random
import logging
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set

logger = logging.getLogger(__name__)

DEFAULT_MAX_WRONG = 6

WORD_LIST: List[str] = [
    "python", "rocket", "bridge", "castle", "forest",
    "planet", "cactus", "violin", "magnet", "jungle",
    "sphere", "goblin", "anchor", "falcon", "lantern",
    "marble", "oyster", "pillow", "quartz", "shadow",
]


# ---------------------------------------------------------------------------
# Pure core helpers
# ---------------------------------------------------------------------------

def mask_word(word: str, guessed: FrozenSet[str]) -> str:
    """Return the word with unguessed letters replaced by '_'."""
    return " ".join(ch if ch in guessed else "_" for ch in word)


def is_word_complete(word: str, guessed: FrozenSet[str]) -> bool:
    """Return True when every letter in word has been guessed."""
    return all(ch in guessed for ch in word)


def evaluate_letter(
    letter: str,
    word: str,
    guessed: FrozenSet[str],
    wrong_count: int,
    max_wrong: int,
) -> Dict[str, Any]:
    """
    Process a single letter guess.

    Returns a dict with:
        correct         - True if letter is in word
        already_guessed - True if letter was guessed before
        guessed         - updated frozenset of guessed letters
        wrong_count     - updated wrong-guess count
        masked_word     - word display string
        won             - True when word is fully revealed
        game_over       - True when won or wrong limit reached
    """
    letter = letter.lower()

    if letter in guessed:
        logger.debug("Letter '%s' already guessed", letter)
        return {
            "correct": letter in word,
            "already_guessed": True,
            "guessed": guessed,
            "wrong_count": wrong_count,
            "masked_word": mask_word(word, guessed),
            "won": is_word_complete(word, guessed),
            "game_over": is_word_complete(word, guessed) or wrong_count >= max_wrong,
        }

    updated_guessed = guessed | frozenset([letter])
    correct = letter in word
    updated_wrong = wrong_count if correct else wrong_count + 1
    won = is_word_complete(word, updated_guessed)
    game_over = won or updated_wrong >= max_wrong

    logger.debug(
        "evaluate_letter: letter='%s' correct=%s wrong_count=%d game_over=%s",
        letter, correct, updated_wrong, game_over,
    )
    return {
        "correct": correct,
        "already_guessed": False,
        "guessed": updated_guessed,
        "wrong_count": updated_wrong,
        "masked_word": mask_word(word, updated_guessed),
        "won": won,
        "game_over": game_over,
    }


# ---------------------------------------------------------------------------
# Dict adapter
# ---------------------------------------------------------------------------

def play(input_data: Any) -> Dict[str, Any]:
    """
    Accept a dict with 'letter', 'word', 'guessed' (list), 'wrong_count', 'max_wrong'.
    Returns evaluation result or error dict.
    """
    if not isinstance(input_data, dict):
        return {"error": "Input must be a dict"}

    required = ("letter", "word", "guessed", "wrong_count", "max_wrong")
    for key in required:
        if key not in input_data:
            return {"error": f"Missing required field: {key}"}

    letter = input_data["letter"]
    if not isinstance(letter, str) or len(letter) != 1 or not letter.isalpha():
        return {"error": "letter must be a single alphabetic character"}

    word = input_data["word"]
    if not isinstance(word, str) or not word.isalpha():
        return {"error": "word must be a non-empty alphabetic string"}

    try:
        guessed: FrozenSet[str] = frozenset(str(g).lower() for g in input_data["guessed"])
        wrong_count = int(input_data["wrong_count"])
        max_wrong = int(input_data["max_wrong"])
    except (ValueError, TypeError) as exc:
        logger.warning("Type conversion failed: %s", exc)
        return {"error": "wrong_count and max_wrong must be integers"}

    if max_wrong <= 0:
        return {"error": "max_wrong must be positive"}
    if wrong_count < 0 or wrong_count >= max_wrong:
        return {"error": "wrong_count is out of valid range"}

    result = evaluate_letter(letter, word.lower(), guessed, wrong_count, max_wrong)
    return {**result, "guessed": sorted(result["guessed"])}


# ---------------------------------------------------------------------------
# Interactive CLI runner
# ---------------------------------------------------------------------------

def run_cli(
    max_wrong: int = DEFAULT_MAX_WRONG,
    choice: Callable[[List[str]], str] = random.choice,
) -> None:
    """Run an interactive word-guessing game in the terminal."""
    word = choice(WORD_LIST).lower()
    guessed: FrozenSet[str] = frozenset()
    wrong_count = 0

    print(f"\nWord Guessing Game — guess the {len(word)}-letter word.")
    print(f"You may make up to {max_wrong} wrong guess(es).\n")

    try:
        while True:
            print(f"  Word   : {mask_word(word, guessed)}")
            print(f"  Guessed: {', '.join(sorted(guessed)) or '—'}")
            print(f"  Wrong  : {wrong_count}/{max_wrong}\n")

            try:
                raw = input("Enter a letter: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting game. Goodbye!\n")
                logger.info("run_cli terminated by user (EOF/KeyboardInterrupt)")
                return

            if len(raw) != 1 or not raw.isalpha():
                print("  Please enter a single letter.\n")
                continue

            result = evaluate_letter(raw, word, guessed, wrong_count, max_wrong)
            guessed = result["guessed"]
            wrong_count = result["wrong_count"]

            if result["already_guessed"]:
                print(f"  You already guessed '{raw}'.\n")
                continue

            if result["correct"]:
                print(f"  '{raw}' is in the word!\n")
            else:
                print(f"  '{raw}' is not in the word.\n")

            if result["won"]:
                print(f"  {mask_word(word, guessed)}")
                print(f"\n  You guessed it! The word was '{word}'. Congratulations!\n")
                break

            if result["game_over"]:
                print(f"\n  Too many wrong guesses. The word was '{word}'. Better luck next time!\n")
                break
    except Exception:
        logger.exception("Unexpected error in run_cli")
        print("\nAn unexpected error occurred; exiting the game.\n")


# ---------------------------------------------------------------------------
# Manual smoke-test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    run_cli()
