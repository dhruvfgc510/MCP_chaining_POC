"""Word Guessing Game — guess the hidden word one letter at a time."""

import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Set

MAX_ATTEMPTS = 6

WORDS = [
    "python", "rocket", "bridge", "castle", "jungle", "planet",
    "trophy", "mirror", "breeze", "famine", "glitch", "museum",
    "oyster", "quartz", "riddle", "sphinx", "tundra", "walrus",
    "zipper", "cobalt", "dagger", "falcon", "gravel", "herald",
]


def show_title() -> None:
    print(
        "\n+==========================+\n"
        "|    WORD GUESSING GAME    |\n"
        "|  One letter at a time!   |\n"
        "+==========================+\n"
    )


def safe_input(prompt: str) -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nInput interrupted. Exiting game. Goodbye!")
        sys.exit(0)


@dataclass
class GameState:
    word: str
    guessed: Set[str] = field(default_factory=set)
    attempts_left: int = MAX_ATTEMPTS


def display(state: GameState) -> str:
    return " ".join(ch if ch in state.guessed else "_" for ch in state.word)


def is_won(state: GameState) -> bool:
    return all(ch in state.guessed for ch in state.word)


def play(select_word: Callable[[], str] = lambda: random.choice(WORDS)) -> None:
    state = GameState(word=select_word())

    print(f"Guess the {len(state.word)}-letter word. You have {MAX_ATTEMPTS} wrong attempts allowed.\n")

    while state.attempts_left > 0:
        revealed = display(state)
        print(f"  Word:    {revealed}")
        if state.guessed:
            print(f"  Guessed: {', '.join(sorted(state.guessed))}")
        print(f"  Attempts left: {state.attempts_left}\n")

        if is_won(state):
            print(f"You got it! The word was '{state.word}'.")
            return

        raw = safe_input("Guess a letter: ").strip().lower()

        if len(raw) != 1 or not raw.isalpha():
            print("Enter a single letter.\n")
            continue

        if raw in state.guessed:
            print(f"You already guessed '{raw}'.\n")
            continue

        state.guessed.add(raw)

        if raw in state.word:
            print(f"  '{raw}' is in the word!\n")
        else:
            state.attempts_left -= 1
            print(f"  '{raw}' is not in the word.\n")

    print(f"Out of attempts! The word was '{state.word}'.")


def main() -> None:
    show_title()
    while True:
        play()
        again = safe_input("\nPlay again? (y/n): ").strip().lower()
        if again != "y":
            print("Thanks for playing!")
            break
        print()


if __name__ == "__main__":
    main()
