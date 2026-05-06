import random


WORDS = [
    "python", "developer", "keyboard", "monitor", "algorithm",
    "function", "variable", "database", "network", "interface",
    "elephant", "library", "computer", "software", "hardware",
    "chocolate", "adventure", "universe", "symphony", "waterfall",
]

MAX_ATTEMPTS = 6


def choose_word():
    return random.choice(WORDS)


def display_state(word, guessed_letters, attempts_left):
    display = " ".join(letter if letter in guessed_letters else "_" for letter in word)
    print(f"\nWord: {display}")
    print(f"Guessed: {', '.join(sorted(guessed_letters)) if guessed_letters else 'None'}")
    print(f"Attempts left: {attempts_left}")


def draw_hangman(attempts_left):
    stages = [
        """
   -----
   |   |
   O   |
  /|\\  |
  / \\  |
        |
=========""",
        """
   -----
   |   |
   O   |
  /|\\  |
  /    |
        |
=========""",
        """
   -----
   |   |
   O   |
  /|\\  |
        |
        |
=========""",
        """
   -----
   |   |
   O   |
  /|   |
        |
        |
=========""",
        """
   -----
   |   |
   O   |
   |   |
        |
        |
=========""",
        """
   -----
   |   |
   O   |
        |
        |
        |
=========""",
        """
   -----
   |   |
        |
        |
        |
        |
=========""",
    ]
    print(stages[attempts_left])


def get_guess(guessed_letters):
    while True:
        guess = input("Guess a letter: ").strip().lower()
        if len(guess) != 1:
            print("Please enter a single letter.")
        elif not guess.isalpha():
            print("Please enter a valid letter.")
        elif guess in guessed_letters:
            print(f"You already guessed '{guess}'. Try a different letter.")
        else:
            return guess


def play_game():
    word = choose_word()
    guessed_letters = set()
    attempts_left = MAX_ATTEMPTS
    wrong_guesses = 0

    print("\n=== WORD GUESSING GAME ===")
    print(f"Guess the {len(word)}-letter word! You have {MAX_ATTEMPTS} attempts.")

    while attempts_left > 0:
        draw_hangman(wrong_guesses)
        display_state(word, guessed_letters, attempts_left)

        if all(letter in guessed_letters for letter in word):
            print(f"\nYou won! The word was '{word}'.")
            return True

        guess = get_guess(guessed_letters)
        guessed_letters.add(guess)

        if guess in word:
            print(f"Good guess! '{guess}' is in the word.")
        else:
            attempts_left -= 1
            wrong_guesses += 1
            print(f"Wrong! '{guess}' is not in the word.")

    draw_hangman(wrong_guesses)
    print(f"\nGame over! The word was '{word}'.")
    return False


def main():
    while True:
        play_game()
        again = input("\nPlay again? (yes/no): ").strip().lower()
        if again not in ("yes", "y"):
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
