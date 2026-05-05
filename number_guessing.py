"""Number Guessing Game — guess the computer's secret number."""

import random
import sys
from typing import Callable, Optional

MAX_ATTEMPTS = 7
LOW = 1
HIGH = 100


def show_title() -> None:
    print(
        "\n+==========================+\n"
        "|   NUMBER GUESSING GAME   |\n"
        "|   Can you find it?       |\n"
        "+==========================+\n"
    )


def safe_input(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        print("\nNo input detected (EOF). Exiting.")
        sys.exit(0)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(0)


def parse_guess(raw: str) -> Optional[int]:
    raw = raw.strip()
    if not raw.lstrip("-").isdigit():
        return None
    return int(raw)


def play(rng: Callable[[int, int], int] = random.randint) -> None:
    secret = rng(LOW, HIGH)
    attempts_left = MAX_ATTEMPTS

    print(f"I'm thinking of a number between {LOW} and {HIGH}.")
    print(f"You have {MAX_ATTEMPTS} attempts. Good luck!\n")

    while attempts_left > 0:
        guess = None
        while guess is None:
            raw = safe_input(f"Attempt {MAX_ATTEMPTS - attempts_left + 1}/{MAX_ATTEMPTS} — Your guess: ")
            guess = parse_guess(raw)
            if guess is None:
                print("Please enter a whole number.")

        attempts_left -= 1

        if guess == secret:
            used = MAX_ATTEMPTS - attempts_left
            print(f"\nCorrect! You got it in {used} attempt{'s' if used != 1 else ''}.")
            return

        if attempts_left == 0:
            break

        hint = "Too low!" if guess < secret else "Too high!"
        print(f"  {hint}  ({attempts_left} attempt{'s' if attempts_left != 1 else ''} left)\n")

    print(f"\nOut of attempts! The number was {secret}.")


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
