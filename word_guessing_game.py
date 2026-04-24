import random
import logging

WORD_LIST = [
    "python", "rocket", "jungle", "marble", "wizard",
    "bridge", "candle", "planet", "forest", "knight",
]
MAX_ATTEMPTS = 6
LOGGER = logging.getLogger(__name__)


def safe_input(prompt, input_fn=input):
    try:
        return input_fn(prompt)
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("\nInput interrupted. Exiting game.")


def display_word(word, guessed):
    return " ".join(ch if ch in guessed else "_" for ch in word)


def get_letter(guessed, input_fn=input, output_fn=print):
    while True:
        raw = safe_input("Guess a letter: ", input_fn).strip().lower()
        if len(raw) != 1 or not raw.isalpha():
            output_fn("Enter a single letter.")
            LOGGER.debug("Invalid input: %r", raw)
        elif raw in guessed:
            output_fn("Already guessed that letter.")
            LOGGER.debug("Repeated guess: %s", raw)
        else:
            LOGGER.info("Player guessed letter: %s", raw)
            return raw


def play(word, max_attempts, input_fn=input, output_fn=print):
    LOGGER.info("Game started: word_length=%d max_attempts=%d", len(word), max_attempts)
    LOGGER.debug("Chosen word: %s", word)
    guessed = set()
    wrong = 0
    while wrong < max_attempts:
        output_fn(f"\n{display_word(word, guessed)}")
        output_fn(f"Wrong guesses: {wrong}/{max_attempts}  Guessed: {', '.join(sorted(guessed)) or 'none'}")
        if all(ch in guessed for ch in word):
            output_fn(f"You guessed the word: {word}")
            LOGGER.info("Game result: WIN wrong=%d guesses=%d", wrong, len(guessed))
            return True
        try:
            letter = get_letter(guessed, input_fn, output_fn)
        except SystemExit:
            LOGGER.warning("Input interrupted during guessing.")
            raise
        guessed.add(letter)
        if letter in word:
            output_fn("Correct!")
            LOGGER.info("Correct guess: %s", letter)
        else:
            wrong += 1
            output_fn("Wrong.")
            LOGGER.warning("Wrong guess: %s wrong_count=%d", letter, wrong)
    output_fn(f"\nOut of attempts. The word was '{word}'.")
    LOGGER.info("Game result: LOSE word=%s wrong=%d guesses=%d", word, wrong, len(guessed))
    return False


def main(input_fn=input, output_fn=print, chooser=random.choice):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
    output_fn("Word Guessing Game")
    output_fn(f"Guess the hidden word one letter at a time. You have {MAX_ATTEMPTS} wrong attempts allowed.")
    word = chooser(WORD_LIST)
    LOGGER.info("New session started.")
    try:
        play(word, MAX_ATTEMPTS, input_fn, output_fn)
    except SystemExit as err:
        LOGGER.info("Session terminated: %s", err)
        output_fn(str(err))


if __name__ == "__main__":
    main()
