import random


def print_board(board, output_fn=print):
    for i in range(0, 9, 3):
        output_fn(" | ".join(board[i : i + 3]))
        if i < 6:
            output_fn("--+---+--")


def check_winner(board, mark):
    wins = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
            (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
    return any(board[a] == board[b] == board[c] == mark for a, b, c in wins)


def free_slots(board):
    return [i for i, cell in enumerate(board) if cell not in ("X", "O")]


def parse_slot(choice):
    if not choice.isdigit():
        raise ValueError("Enter a number.")
    idx = int(choice) - 1
    if idx not in range(9):
        raise ValueError("Pick between 1 and 9.")
    return idx


def apply_move(board, idx, mark):
    if idx in range(9) and board[idx] not in ("X", "O"):
        board[idx] = mark
        return True
    return False


def safe_input(prompt, input_fn=input):
    try:
        return input_fn(prompt)
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("\nInput interrupted. Exiting game.")


def player_turn(board, input_fn=input, output_fn=print):
    while True:
        try:
            idx = parse_slot(safe_input("Choose a slot (1-9): ", input_fn).strip())
        except ValueError as err:
            output_fn(str(err))
            continue
        if apply_move(board, idx, "X"):
            return
        output_fn("Slot already taken.")


def computer_turn(board, chooser=random.choice):
    slots = free_slots(board)
    if slots:
        apply_move(board, chooser(slots), "O")


def main(input_fn=input, output_fn=print, chooser=random.choice):
    output_fn("Tic Tac Toe: You are X, computer is O")
    board = [str(i) for i in range(1, 10)]
    try:
        while True:
            print_board(board, output_fn)
            player_turn(board, input_fn, output_fn)
            if check_winner(board, "X"):
                print_board(board, output_fn)
                output_fn("You win!")
                return
            if not free_slots(board):
                print_board(board, output_fn)
                output_fn("It's a draw!")
                return
            computer_turn(board, chooser)
            if check_winner(board, "O"):
                print_board(board, output_fn)
                output_fn("Computer wins!")
                return
    except SystemExit as err:
        output_fn(str(err))


if __name__ == "__main__":
    main()
