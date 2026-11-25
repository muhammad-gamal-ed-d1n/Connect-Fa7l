"""Tkinter interface for human-versus-computer Connect Four."""

import tkinter as tk
from queue import Empty, Queue
from threading import Thread
from tkinter import messagebox, ttk
from typing import Optional

from game_engine import Engine, SearchCancelled, SearchNode
from model import Disc, Game


class ConnectFourGUI:
    """Draw the board, accept human moves, and display the search tree."""

    def __init__(self, root: tk.Tk):
        """Create widgets and initialize the GUI before a game is started."""
        self.root = root
        self.root.title("Connect-Fa7l — Connect Four")
        self.root.minsize(860, 570)
        self.game: Optional[Game] = None
        self.engine: Optional[Engine] = None
        self.human_color = Disc.Yellow
        self.turn_color = Disc.Red
        self.ai_pending = False
        self.ai_callback_id: Optional[str] = None
        self._search_generation = 0
        self._search_results: Queue[
            tuple[int, Engine, Optional[int], Optional[Exception]]
        ] = Queue()
        self.game_over = False

        self._build_layout()
        self._refresh_board()

    def _build_layout(self) -> None:
        """Build game controls, board canvas, and bounded tree viewer."""
        controls = ttk.Frame(self.root, padding=(12, 10))
        controls.pack(fill="x")

        ttk.Label(controls, text="Your color:").pack(side="left")
        self.color_choice = tk.StringVar(value="Yellow")
        ttk.Combobox(
            controls,
            textvariable=self.color_choice,
            values=("Red", "Yellow"),
            state="readonly",
            width=9,
        ).pack(side="left", padx=(6, 14))

        ttk.Label(controls, text="Search depth K:").pack(side="left")
        self.depth_choice = tk.StringVar(value="4")
        ttk.Entry(
            controls,
            textvariable=self.depth_choice,
            width=8,
        ).pack(side="left", padx=(6, 14))
        ttk.Button(controls, text="New game", command=self.start_game).pack(side="left")

        self.status = tk.StringVar(value="Choose your color and search depth, then start.")
        ttk.Label(self.root, textvariable=self.status, padding=(12, 0, 12, 8)).pack(
            anchor="w"
        )

        panes = ttk.Panedwindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        board_panel = ttk.Frame(panes, padding=(0, 0, 12, 0))
        panes.add(board_panel, weight=1)
        self.score = tk.StringVar(value="Red 0  —  Yellow 0")
        ttk.Label(board_panel, textvariable=self.score, font=("TkDefaultFont", 11, "bold")).pack(
            pady=(0, 8)
        )
        self.canvas = tk.Canvas(
            board_panel,
            width=490,
            height=440,
            background="#174ea6",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_board_click)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        tree_panel = ttk.Frame(panes)
        panes.add(tree_panel, weight=1)
        ttk.Label(
            tree_panel,
            text="Minimax search tree (h = board heuristic; V = minimax value)",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        tree_frame = ttk.Frame(tree_panel)
        tree_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("depth", "heuristic", "value", "bounds"),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="Move / node")
        self.tree.heading("depth", text="Depth")
        self.tree.heading("heuristic", text="h")
        self.tree.heading("value", text="V")
        self.tree.heading("bounds", text="Alpha / beta")
        self.tree.column("#0", width=190, minwidth=140)
        self.tree.column("depth", width=48, anchor="center")
        self.tree.column("heuristic", width=75, anchor="e")
        self.tree.column("value", width=75, anchor="e")
        self.tree.column("bounds", width=145, anchor="e")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.insert("", "end", text="Start a game to see its search tree.")

    def start_game(self) -> None:
        """Start a fresh game after validating the requested positive K."""
        try:
            depth = int(self.depth_choice.get().strip())
            if depth < 1:
                raise ValueError
        except (tk.TclError, ValueError):
            messagebox.showerror(
                "Invalid search depth",
                "Search depth K must be a positive integer (K >= 1).",
            )
            return

        if self.ai_pending and self.engine is not None:
            self.engine.cancel_search()
        self._search_generation += 1
        if self.ai_callback_id is not None:
            self.root.after_cancel(self.ai_callback_id)
            self.ai_callback_id = None

        self.human_color = Disc.Red if self.color_choice.get() == "Red" else Disc.Yellow
        computer_color = self.human_color.get_other_color()
        self.game = Game(length=6, width=7)
        self.engine = Engine(self.game, computer_color, depth)
        self.turn_color = Disc.Red
        self.ai_pending = False
        self.game_over = False
        self._clear_tree()
        self.status.set(f"New game — you are {self.human_color.name}.")
        self._refresh_board()
        if self.turn_color is computer_color:
            self._schedule_computer_move()

    def _on_board_click(self, event: tk.Event) -> None:
        """Place a human disc when it is the human's turn and the move is legal."""
        if (
            self.game is None
            or self.game_over
            or self.ai_pending
            or self.turn_color is not self.human_color
        ):
            return
        column_width = self.canvas.winfo_width() / self.game.width
        column = int(event.x / column_width)
        if not 0 <= column < self.game.width or not self.game.is_valid(column):
            return
        self.game.insert(column, self.human_color)
        self.turn_color = self.human_color.get_other_color()
        self._refresh_board()
        if self._finish_if_full():
            return
        self._schedule_computer_move()

    def _schedule_computer_move(self) -> None:
        """Search in a worker thread while keeping Tk's event loop responsive."""
        if self.engine is None:
            return
        self.ai_pending = True
        self.status.set("Computer is searching…")
        worker = Thread(
            target=self._search_computer_move,
            args=(self._search_generation, self.engine),
            daemon=True,
        )
        worker.start()
        self.ai_callback_id = self.root.after(100, self._play_computer_move)

    def _search_computer_move(self, generation: int, engine: Engine) -> None:
        """Run AI search off the UI thread and queue its result or failure."""
        try:
            column = engine.choose_move()
        except SearchCancelled:
            return
        except Exception as error:
            self._search_results.put((generation, engine, None, error))
            return
        self._search_results.put((generation, engine, column, None))

    def _play_computer_move(self) -> None:
        """Consume a completed search result and update the game on the UI thread."""
        self.ai_callback_id = None
        result = None
        while result is None:
            try:
                candidate = self._search_results.get_nowait()
            except Empty:
                if self.ai_pending:
                    self.ai_callback_id = self.root.after(100, self._play_computer_move)
                return
            generation, engine, _, _ = candidate
            if generation == self._search_generation and engine is self.engine:
                result = candidate

        _, engine, column, error = result
        self.ai_pending = False
        if error is not None:
            self.status.set("Computer search failed.")
            messagebox.showerror("Search failed", str(error))
            return
        if self.engine is None or self.game is None or self.game_over:
            return
        if self.turn_color is not engine.computer_color:
            return
        if column is None:
            self._finish_if_full()
            return
        self.game.insert(column, engine.computer_color)

        self.turn_color = self.human_color
        self._show_tree(engine.last_tree)
        print(
            f"\nAI chose column {column + 1}; "
            f"{engine.nodes_expanded} nodes in {engine.search_seconds:.3f}s"
        )
        print(engine.tree_as_text())
        self._refresh_board()
        if not self._finish_if_full():
            self.status.set(
                f"Your turn ({self.human_color.name}). "
                f"AI searched {engine.nodes_expanded} nodes "
                f"in {engine.search_seconds:.3f}s."
            )

    def _refresh_board(self) -> None:
        """Redraw the current board and update the connected-four score."""
        width = max(self.canvas.winfo_width(), 420)
        height = max(self.canvas.winfo_height(), 360)
        self.canvas.delete("all")
        if self.game is None:
            rows, columns = 6, 7
            board = [[Disc.Vacant for _ in range(columns)] for _ in range(rows)]
        else:
            rows, columns, board = self.game.length, self.game.width, self.game.board
        cell_width, cell_height = width / columns, height / rows
        for column in range(columns):
            self.canvas.create_text(
                (column + 0.5) * cell_width,
                16,
                text=str(column + 1),
                fill="white",
                font=("TkDefaultFont", 11, "bold"),
            )
        for row in range(rows):
            for column in range(columns):
                x = (column + 0.5) * cell_width
                y = (row + 0.5) * cell_height + 12
                radius = min(cell_width, cell_height) * 0.37
                disc = board[row][column]
                fill = (
                    "#d83232" if disc is Disc.Red else
                    "#f5d547" if disc is Disc.Yellow else
                    "#f4f6fa"
                )
                self.canvas.create_oval(
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                    fill=fill,
                    outline="#102f62",
                    width=2,
                )
        red_score = self.game.calculate_score(Disc.Red) if self.game else 0
        yellow_score = self.game.calculate_score(Disc.Yellow) if self.game else 0
        self.score.set(f"Red {red_score}  —  Yellow {yellow_score}")

    def _on_canvas_resize(self, _event: tk.Event) -> None:
        """Keep the board drawing fitted to its resized canvas."""
        self._refresh_board()

    def _finish_if_full(self) -> bool:
        """Show the final score when the board is full; return whether finished."""
        if self.game is None or not self.game.is_full():
            return False
        self.game_over = True
        red_score = self.game.calculate_score(Disc.Red)
        yellow_score = self.game.calculate_score(Disc.Yellow)
        if red_score > yellow_score:
            result = "Red wins"
        elif yellow_score > red_score:
            result = "Yellow wins"
        else:
            result = "The game is a draw"
        self.status.set(
            f"Game over — {result}. Final score: Red {red_score}, Yellow {yellow_score}."
        )
        messagebox.showinfo(
            "Game over",
            f"{result}!\nFinal score: Red {red_score} — Yellow {yellow_score}",
        )
        return True

    def _clear_tree(self) -> None:
        """Replace old search output with the initial empty-tree message."""
        self.tree.delete(*self.tree.get_children())
        self.tree.insert("", "end", text="The tree will appear after the computer searches.")

    def _show_tree(self, root: Optional[SearchNode]) -> None:
        """Display a bounded tree iteratively, so depth does not recurse in Tk."""
        self.tree.delete(*self.tree.get_children())
        if root is None:
            self.tree.insert("", "end", text="No search tree was produced.")
            return

        inserted = 0
        limit = 2_500

        # A stack avoids Python recursion for deep trees and caps Tk widget work.
        stack = [("", root)]
        while stack and inserted < limit:
            parent, node = stack.pop()
            move = "Root" if node.move is None else f"Column {node.move + 1}"
            role = "MAX" if node.maximizing else "MIN"
            value = "" if node.value is None else str(node.value)
            alpha = self._format_bound(node.alpha)
            beta = self._format_bound(node.beta)
            item = self.tree.insert(
                parent,
                "end",
                text=f"{move} — {role}",
                values=(node.depth, node.heuristic, value, f"{alpha} / {beta}"),
                open=node.depth < 2,
            )
            inserted += 1
            if node.pruned_moves and inserted < limit:
                self.tree.insert(
                    item,
                    "end",
                    text="Pruned: columns " + ", ".join(
                        str(column + 1) for column in node.pruned_moves
                    ),
                    values=("", "", "", ""),
                )
                inserted += 1
            for child in reversed(node.children):
                stack.append((item, child))

        if stack:
            self.tree.insert(
                "",
                "end",
                text=f"Tree display truncated at {limit} entries; "
                "the AI search itself completed in full.",
            )
        roots = self.tree.get_children()
        if roots:
            self.tree.see(roots[0])

    @staticmethod
    def _format_bound(value: float) -> str:
        """Format infinite alpha-beta bounds compactly for the tree columns."""
        if value == float("inf"):
            return "∞"
        if value == float("-inf"):
            return "−∞"
        return str(int(value))


def main() -> None:
    """Launch the Connect Four window."""
    root = tk.Tk()
    ConnectFourGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
