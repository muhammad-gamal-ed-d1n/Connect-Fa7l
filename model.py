"""Connect Four board model, scoring rules, and heuristic evaluation."""

from enum import Enum
from typing import List, Optional, Sequence, Tuple


class Disc(Enum):
    """The two playable disc colors and the empty-cell value."""

    Vacant = 0
    Red = 1
    Yellow = 2

    def get_other_color(self) -> "Disc":
        """Return the opposing playable color."""
        if self is Disc.Red:
            return Disc.Yellow
        if self is Disc.Yellow:
            return Disc.Red
        raise ValueError("A vacant cell has no opposing color.")


Board = List[List[Disc]]


class Game:
    """Connect Four board and scoring rules."""

    DIRECTIONS: Sequence[Tuple[int, int]] = ((0, 1), (1, 0), (1, 1), (1, -1))

    def __init__(self, length: int = 6, width: int = 7):
        """Create an empty board with at least four rows and columns."""
        if length < 4 or width < 4:
            raise ValueError("The board must be at least 4 rows by 4 columns.")
        self.length = length
        self.width = width
        self.board: Board = [[Disc.Vacant for _ in range(width)] for _ in range(length)]

    @classmethod
    def from_board(cls, board: Board) -> "Game":
        """Create a game using a defensive copy of an existing board."""
        game = cls(len(board), len(board[0]))
        game.board = [row[:] for row in board]
        return game

    def copy(self) -> "Game":
        """Return an independent copy of this game."""
        return self.from_board(self.board)

    def valid_moves(self) -> List[int]:
        """Return the indices of columns that can accept a disc."""
        return self.valid_moves_on(self.board)

    @staticmethod
    def valid_moves_on(board: Board) -> List[int]:
        """Return legal column indices without constructing another Game."""
        return [
            column
            for column in range(len(board[0]))
            if board[0][column] is Disc.Vacant
        ]

    def is_valid(self, column: int) -> bool:
        """Return whether a column index is in range and not full."""
        return (
            0 <= column < self.width
            and self.board[0][column] is Disc.Vacant
        )

    def landing_row(self, column: int) -> Optional[int]:
        """Return the row where a disc would land, or None for an invalid column."""
        if not self.is_valid(column):
            return None
        return self.landing_row_on(self.board, column)

    @staticmethod
    def landing_row_on(board: Board, column: int) -> Optional[int]:
        """Find a column's landing row directly from a board matrix."""
        if not 0 <= column < len(board[0]) or board[0][column] is not Disc.Vacant:
            return None
        row = len(board) - 1
        while row >= 0 and board[row][column] is not Disc.Vacant:
            row -= 1
        return row if row >= 0 else None

    def insert(self, column: int, color: Disc) -> int:
        """Drop a colored disc into a column and return its row."""
        if color is Disc.Vacant:
            raise ValueError("A vacant disc cannot be inserted.")
        row = self.landing_row(column)
        if row is None:
            raise IndexError("Invalid insertion into a full or invalid column.")
        self.board[row][column] = color
        return row

    def is_full(self) -> bool:
        """Return whether every column is full."""
        return not self.valid_moves()

    def calculate_score(self, color: Disc) -> int:
        """Count maximal, contiguous runs of four or more discs for a color."""
        return self.calculate_score_on(self.board, color)

    @classmethod
    def calculate_score_on(cls, board: Board, color: Disc) -> int:
        """Count connected-four runs directly on a board without copying it."""
        score = 0
        height, width = len(board), len(board[0])
        for row in range(height):
            for column in range(width):
                if board[row][column] is not color:
                    continue
                for dr, dc in cls.DIRECTIONS:
                    previous_row, previous_column = row - dr, column - dc
                    if (
                        0 <= previous_row < height
                        and 0 <= previous_column < width
                        and board[previous_row][previous_column] is color
                    ):
                        continue
                    run_length = 0
                    current_row, current_column = row, column
                    while (
                        0 <= current_row < height
                        and 0 <= current_column < width
                        and board[current_row][current_column] is color
                    ):
                        run_length += 1
                        current_row += dr
                        current_column += dc
                    if run_length >= 4:
                        score += 1
        return score

    @classmethod
    def base_heuristic(cls, board: Board, color: Disc) -> int:
        """Score center control and open four-cell windows for one color.

        A playable three-in-a-row is weighted heavily because its empty cell
        can be filled on the next turn. Unplayable threes and two-disc windows
        receive smaller weights to represent longer-term potential.
        """
        height, width = len(board), len(board[0])
        score = 0
        opponent = color.get_other_color()
        landing_rows = [
            cls.landing_row_on(board, column) for column in range(width)
        ]

        # Center discs belong to more possible winning lines than edge discs.
        center = (width - 1) / 2
        for row in range(height):
            for column in range(width):
                if board[row][column] is color:
                    score += int(width - abs(column - center) * 2)

        for row in range(height):
            for column in range(width):
                for dr, dc in cls.DIRECTIONS:
                    end_row = row + 3 * dr
                    end_column = column + 3 * dc
                    if not (0 <= end_row < height and 0 <= end_column < width):
                        continue
                    own_count = 0
                    empty_cells = []
                    blocked = False
                    for offset in range(4):
                        cell_row = row + offset * dr
                        cell_column = column + offset * dc
                        cell = board[cell_row][cell_column]
                        if cell is color:
                            own_count += 1
                        elif cell is opponent:
                            blocked = True
                            break
                        else:
                            empty_cells.append((cell_row, cell_column))
                    if own_count == 0 or blocked:
                        continue
                    if own_count == 4:
                        score += 100_000
                    elif own_count == 3:
                        playable = any(
                            landing_rows[empty_column] == empty_row
                            for empty_row, empty_column in empty_cells
                        )
                        score += 1_200 if playable else 180
                    elif own_count == 2:
                        score += 45
                    else:
                        score += 4
        return score

    @classmethod
    def evaluate_board(cls, board: Board, computer_color: Disc) -> int:
        """Return computer-minus-human score plus positional heuristic value."""
        opponent = computer_color.get_other_color()
        score_difference = (
            cls.calculate_score_on(board, computer_color)
            - cls.calculate_score_on(board, opponent)
        )
        if not cls.valid_moves_on(board):
            return score_difference * 1_000_000
        return (
            score_difference * 1_000_000
            + cls.base_heuristic(board, computer_color)
            - cls.base_heuristic(board, opponent)
        )
