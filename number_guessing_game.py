import random

MAX_ATTEMPTS = 7


def safe_input(prompt, input_fn=input):
    try:
        return input_fn(prompt)
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("\nInput interrupted. Exiting game.")


def get_guess(input_fn=input, output_fn=print):
    while True:
        raw = safe_input("Your guess: ", input_fn).strip()
        if raw.lstrip("-").isdigit():
            return int(raw)
        output_fn("Enter a valid integer.")


def play(secret, max_attempts, input_fn=input, output_fn=print):
    for attempt in range(1, max_attempts + 1):
        remaining = max_attempts - attempt + 1
        output_fn(f"Attempt {attempt}/{max_attempts} ({remaining} left)")
        guess = get_guess(input_fn, output_fn)
        if guess == secret:
            output_fn(f"Correct! You guessed it in {attempt} attempt(s).")
            return True
        output_fn("Too high." if guess > secret else "Too low.")
    output_fn(f"Out of attempts. The number was {secret}.")
    return False


def main(input_fn=input, output_fn=print, randint=random.randint):
    output_fn("Number Guessing Game")
    output_fn(f"Guess a number between 1 and 100. You have {MAX_ATTEMPTS} attempts.")
    secret = randint(1, 100)
    try:
        play(secret, MAX_ATTEMPTS, input_fn, output_fn)
    except SystemExit as err:
        output_fn(str(err))


if __name__ == "__main__":
    main()
