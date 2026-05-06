def print_board(board):
    for i, row in enumerate(board):
        print(" | ".join(row))
        if i < 2:
            print("-" * 9)


def check_winner(board, player):
    for row in board:
        if all(cell == player for cell in row):
            return True
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False


def is_board_full(board):
    return all(cell != " " for row in board for cell in row)


def get_move(board, player):
    while True:
        try:
            move = int(input(f"Player {player}, enter position (1-9): ")) - 1
            row, col = divmod(move, 3)
            if 0 <= move <= 8 and board[row][col] == " ":
                return row, col
            print("Invalid move. Try again.")
        except (ValueError, IndexError):
            print("Enter a number between 1 and 9.")


def play():
    board = [[" "] * 3 for _ in range(3)]
    players = ["X", "O"]
    print("Positions: 1-9 left to right, top to bottom\n")

    for turn in range(9):
        player = players[turn % 2]
        print_board(board)
        row, col = get_move(board, player)
        board[row][col] = player

        if check_winner(board, player):
            print_board(board)
            print(f"\nPlayer {player} wins!")
            return

    print_board(board)
    print("\nIt's a draw!")


if __name__ == "__main__":
    play()
