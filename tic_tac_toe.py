import json
import logging
import re as _re
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

EMPTY, X, O = " ", "X", "O"
WIN_LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
_CTL = _re.compile(r"[\x00-\x1f\x7f]+")


def _safe(v: Any, n: int = 120) -> str:
    return _CTL.sub(" ", str(v))[:n]


def make_board() -> List[str]:
    return [EMPTY] * 9


def check_winner(board: List[str]) -> Optional[str]:
    for a, b, c in WIN_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    return None


def is_draw(board: List[str]) -> bool:
    return EMPTY not in board and check_winner(board) is None


def apply_move(board: List[str], pos: int, player: str) -> Dict[str, Any]:
    if not (0 <= pos <= 8):
        logger.warning("Position out of range: %d", pos)
        return {"error": "Position must be 0-8", "board": board}
    if board[pos] != EMPTY:
        logger.warning("Cell already occupied: %d", pos)
        return {"error": "Cell already occupied", "board": board}
    board = board[:]
    board[pos] = player
    winner = check_winner(board)
    draw = is_draw(board)
    logger.info("Move applied: player=%s pos=%d winner=%s draw=%s", player, pos, winner, draw)
    return {
        "board": board,
        "winner": winner,
        "draw": draw,
        "next_player": O if player == X else X,
    }


def play(input_data: Any) -> Dict[str, Any]:
    if not isinstance(input_data, dict):
        return {"error": "Input must be a dict"}
    board = input_data.get("board", make_board())
    if not isinstance(board, list) or len(board) != 9:
        return {"error": "board must be a list of 9 cells"}
    player = input_data.get("player")
    if player not in (X, O):
        return {"error": "player must be 'X' or 'O'"}
    pos = input_data.get("position")
    if not isinstance(pos, int):
        return {"error": "position must be an integer 0-8"}
    return apply_move(board, pos, player)


def play_json(json_input: str) -> str:
    logger.debug("play_json() called input_len=%d", len(str(json_input)))
    try:
        data = json.loads(json_input)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("JSON parse error: %s preview=%s", exc, _safe(json_input))
        return json.dumps({"error": "Invalid JSON"})
    try:
        result = play(data)
    except (MemoryError, RecursionError):
        raise
    except Exception:
        logger.exception("Unexpected error in play()")
        return json.dumps({"error": "Internal error"})
    try:
        return json.dumps(result, default=str)
    except (TypeError, ValueError):
        logger.exception("Serialization error")
        return json.dumps({"error": "Internal error"})


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    board = make_board()
    moves = [(0, X), (4, O), (1, X), (3, O), (2, X)]
    for pos, player in moves:
        result = play({"board": board, "player": player, "position": pos})
        board = result.get("board", board)
        print(f"Player {player} -> pos {pos}: winner={result.get('winner')}, draw={result.get('draw')}")
