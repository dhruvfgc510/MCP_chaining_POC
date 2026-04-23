import logging
import random

CHOICES = ("snake", "water", "gun")
BEATS = {"snake": "water", "water": "gun", "gun": "snake"}
LOGGER = logging.getLogger(__name__)


def decide(player, computer):
    if player == computer:
        return "draw"
    return "win" if BEATS[player] == computer else "lose"


def safe_input(prompt, input_fn=input):
    try:
        return input_fn(prompt)
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("\nInput interrupted. Exiting game.")


def get_rounds(input_fn=input, output_fn=print):
    while True:
        raw = safe_input("How many rounds? ", input_fn).strip()
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        output_fn("Enter a positive number.")


def get_player_choice(input_fn=input, output_fn=print):
    while True:
        choice = safe_input("Choose snake/water/gun: ", input_fn).strip().lower()
        if choice in CHOICES:
            return choice
        output_fn("Invalid choice. Try again.")


def play_rounds(rounds, player_choice_fn, computer_choice_fn, output_fn=print):
    wins = losses = draws = 0
    for index in range(1, rounds + 1):
        output_fn(f"\nRound {index}")
        player = player_choice_fn()
        computer = computer_choice_fn()
        result = decide(player, computer)
        output_fn(f"You: {player} | Computer: {computer}")
        if result == "win":
            wins += 1
            output_fn("You win this round.")
        elif result == "lose":
            losses += 1
            output_fn("Computer wins this round.")
        else:
            draws += 1
            output_fn("Round draw.")
    return wins, losses, draws


def main(input_fn=input, output_fn=print, chooser=random.choice):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
    output_fn("Snake Water Gun")
    rounds = get_rounds(input_fn, output_fn)
    try:
        wins, losses, draws = play_rounds(
            rounds,
            lambda: get_player_choice(input_fn, output_fn),
            lambda: chooser(CHOICES),
            output_fn,
        )
    except SystemExit as err:
        output_fn(str(err))
        return
    LOGGER.info("Game finished: wins=%s losses=%s draws=%s", wins, losses, draws)
    output_fn("\nFinal Score")
    output_fn(f"You: {wins}, Computer: {losses}, Draws: {draws}")
    output_fn("You won the game." if wins > losses else "Computer won the game." if wins < losses else "Match tied.")


if __name__ == "__main__":
    main()
