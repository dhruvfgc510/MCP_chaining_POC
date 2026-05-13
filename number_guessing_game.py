import random
import time


DIFFICULTIES = {
    "easy":   {"range": (1, 50),  "attempts": 15, "label": "Easy   (1–50,  15 attempts)"},
    "medium": {"range": (1, 100), "attempts": 10, "label": "Medium (1–100, 10 attempts)"},
    "hard":   {"range": (1, 200), "attempts":  7, "label": "Hard   (1–200,  7 attempts)"},
}


def get_difficulty():
    print("\nSelect difficulty:")
    for key, val in DIFFICULTIES.items():
        print(f"  [{key[0].upper()}] {val['label']}")

    while True:
        choice = input("Enter E / M / H: ").strip().lower()
        if choice in ("e", "easy"):
            return "easy"
        if choice in ("m", "medium"):
            return "medium"
        if choice in ("h", "hard"):
            return "hard"
        print("Invalid choice. Please enter E, M, or H.")


def calculate_score(attempts_used, max_attempts, elapsed):
    base = max(0, (max_attempts - attempts_used + 1) * 100)
    time_bonus = max(0, 30 - int(elapsed)) * 5
    return base + time_bonus


def give_hint(guess, secret, attempts_left):
    diff = abs(guess - secret)
    if attempts_left <= 0:
        return
    if diff <= 5:
        print("  Hint: You are very close!")
    elif diff <= 15:
        print("  Hint: Getting warmer.")
    else:
        print("  Hint: Still quite far away.")


def display_progress_bar(attempts_used, max_attempts):
    filled = attempts_used
    empty = max_attempts - attempts_used
    bar = "[" + "#" * filled + "-" * empty + "]"
    print(f"  Attempts: {bar} {attempts_used}/{max_attempts}")


def play_round(difficulty, round_number):
    cfg = DIFFICULTIES[difficulty]
    low, high = cfg["range"]
    max_attempts = cfg["attempts"]
    secret = random.randint(low, high)
    attempts = 0
    start_time = time.time()

    print(f"\n--- Round {round_number} | {difficulty.capitalize()} ---")
    print(f"Guess a number between {low} and {high}. You have {max_attempts} attempts.")

    while attempts < max_attempts:
        display_progress_bar(attempts, max_attempts)
        try:
            raw = input(f"  Your guess: ").strip()
            if raw.lower() == "quit":
                print("  Quitting current round.")
                return None
            guess = int(raw)
        except ValueError:
            print("  Please enter a valid integer.")
            continue

        if guess < low or guess > high:
            print(f"  Out of range! Enter a number between {low} and {high}.")
            continue

        attempts += 1
        elapsed = time.time() - start_time

        if guess < secret:
            print("  Too low!")
            give_hint(guess, secret, max_attempts - attempts)
        elif guess > secret:
            print("  Too high!")
            give_hint(guess, secret, max_attempts - attempts)
        else:
            elapsed = time.time() - start_time
            score = calculate_score(attempts, max_attempts, elapsed)
            print(f"\n  Correct! The number was {secret}.")
            print(f"  You guessed it in {attempts} attempt(s) and {elapsed:.1f}s.")
            print(f"  Score: {score} points")
            return score

    print(f"\n  Out of attempts! The number was {secret}.")
    return 0


def show_scoreboard(scores):
    print("\n========== SCOREBOARD ==========")
    total = 0
    for i, s in enumerate(scores, 1):
        print(f"  Round {i}: {s} points")
        total += s
    print(f"  ---------------------------------")
    print(f"  Total : {total} points")
    print("=================================")


def ask_play_again():
    while True:
        ans = input("\nPlay another round? (Y/N): ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Please enter Y or N.")


def ask_change_difficulty():
    while True:
        ans = input("Change difficulty? (Y/N): ").strip().lower()
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Please enter Y or N.")


def main():
    print("=========================================")
    print("       Welcome to Number Guessing Game   ")
    print("=========================================")
    print("Type 'quit' during a round to exit early.")

    difficulty = get_difficulty()
    scores = []
    round_number = 1

    while True:
        result = play_round(difficulty, round_number)

        if result is None:
            break

        scores.append(result)
        round_number += 1

        if not ask_play_again():
            break

        if ask_change_difficulty():
            difficulty = get_difficulty()

    if scores:
        show_scoreboard(scores)

    print("\nThanks for playing! Goodbye.")


if __name__ == "__main__":
    main()
