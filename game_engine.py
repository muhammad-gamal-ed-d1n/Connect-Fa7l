"""Depth-limited minimax search with alpha-beta pruning and tree reporting."""

import time
from dataclasses import dataclass, field
from threading import Event
from typing import List, Optional

from model import Board, Disc, Game


class SearchCancelled(Exception):
    """Raised when a running search is cancelled by its caller."""


@dataclass
class SearchNode:
    """One position and its search/evaluation metadata."""

    board: Board
    player: Disc
    depth: int
    move: Optional[int]
    maximizing: bool
    heuristic: int
    alpha: float = float("-inf")
    beta: float = float("inf")
    value: Optional[int] = None
    children: List["SearchNode"] = field(default_factory=list)
    pruned_moves: List[int] = field(default_factory=list)


class Engine:
    """Choose computer moves using minimax and alpha-beta pruning."""

    def __init__(self, game: Game, computer_color: Disc, depth: int):
        """Bind the board, computer color, and positive ply search depth."""
        if computer_color is Disc.Vacant:
            raise ValueError("The computer must play Red or Yellow.")
        if not isinstance(depth, int) or isinstance(depth, bool) or depth < 1:
            raise ValueError("Search depth K must be a positive integer.")
        self.game = game
        self.computer_color = computer_color
        self.depth = depth
        self.last_tree: Optional[SearchNode] = None
        self.nodes_expanded = 0
        self.search_seconds = 0.0
        self._cancel_requested = Event()

    def update(self, column: int, color: Disc) -> int:
        """Insert a disc through the engine's board."""
        return self.game.insert(column, color)

    def choose_move(self) -> Optional[int]:
        """Find the best column; K counts plies from the current board."""
        self.nodes_expanded = 0
        started = time.perf_counter()
        root = SearchNode(
            board=[row[:] for row in self.game.board],
            player=self.computer_color,
            depth=0,
            move=None,
            maximizing=True,
            heuristic=Game.evaluate_board(self.game.board, self.computer_color),
        )
        self.last_tree = root
        try:
            self._search(root, float("-inf"), float("inf"))
        finally:
            self.search_seconds = time.perf_counter() - started

        if not root.children:
            return None
        best_child = max(
            root.children,
            key=lambda child: child.value if child.value is not None else float("-inf"),
        )
        return best_child.move

    def make_move(self) -> Optional[int]:
        """Choose and play the computer's move, returning its column."""
        column = self.choose_move()
        if column is not None:
            self.game.insert(column, self.computer_color)
        return column

    def cancel_search(self) -> None:
        """Permanently request cooperative cancellation for this engine."""
        self._cancel_requested.set()

    def _search(self, node: SearchNode, alpha: float, beta: float) -> int:
        """Search one node, placing promising moves first to improve pruning."""
        if self._cancel_requested.is_set():
            raise SearchCancelled
        self.nodes_expanded += 1
        node.alpha, node.beta = alpha, beta
        moves = Game.valid_moves_on(node.board)
        if node.depth >= self.depth or not moves:
            node.value = node.heuristic
            return node.value

        candidates = []
        next_player = node.player.get_other_color()
        for column in moves:
            landing_row = Game.landing_row_on(node.board, column)
            if landing_row is None:
                continue
            child_board = [row[:] for row in node.board]
            child_board[landing_row][column] = node.player
            heuristic = Game.evaluate_board(child_board, self.computer_color)
            candidates.append((heuristic, column, child_board))

        # Visit promising moves first to make alpha-beta cutoffs more effective.
        candidates.sort(key=lambda candidate: candidate[0], reverse=node.maximizing)
        best_value = float("-inf") if node.maximizing else float("inf")

        for index, (heuristic, column, board) in enumerate(candidates):
            child = SearchNode(
                board=board,
                player=next_player,
                depth=node.depth + 1,
                move=column,
                maximizing=not node.maximizing,
                heuristic=heuristic,
                alpha=alpha,
                beta=beta,
            )
            node.children.append(child)
            value = self._search(child, alpha, beta)
            if node.maximizing:
                best_value = max(best_value, value)
                alpha = max(alpha, best_value)
            else:
                best_value = min(best_value, value)
                beta = min(beta, best_value)

            if alpha >= beta:
                node.pruned_moves = [
                    remaining_column
                    for _, remaining_column, _ in candidates[index + 1 :]
                ]
                break

        node.alpha, node.beta = alpha, beta
        node.value = int(best_value)
        return node.value

    def tree_as_text(self, max_nodes: int = 2_000) -> str:
        """Render at most ``max_nodes`` nodes without recursive traversal."""
        if self.last_tree is None:
            return "No search tree yet."
        if max_nodes < 1:
            raise ValueError("max_nodes must be at least 1.")

        lines: List[str] = []
        stack = [(self.last_tree, "", "")]
        while stack and len(lines) < max_nodes:
            node, prefix, label = stack.pop()
            move_text = "root" if node.move is None else f"column {node.move + 1}"
            role = "MAX" if node.maximizing else "MIN"
            line = (
                f"{prefix}{label}{move_text} [{role}, depth={node.depth}] "
                f"h={node.heuristic}, value={node.value}, "
                f"alpha={node.alpha}, beta={node.beta}"
            )
            if node.pruned_moves:
                pruned = ", ".join(str(column + 1) for column in node.pruned_moves)
                line += f", pruned columns={pruned}"
            lines.append(line)
            child_prefix = prefix + ("    " if label else "│   ")
            for index in range(len(node.children) - 1, -1, -1):
                child = node.children[index]
                last = index == len(node.children) - 1 and not node.pruned_moves
                child_label = "└── " if last else "├── "
                stack.append((child, child_prefix, child_label))
        if stack:
            lines.append(
                f"... tree display truncated at {max_nodes} nodes; "
                "remaining branches omitted."
            )
        return "\n".join(lines)
