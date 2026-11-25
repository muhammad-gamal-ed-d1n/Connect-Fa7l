import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
from model import Game, Disc
from game_engine import Engine


class Connect4GUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Connect 4 AI - Minimax with Alpha-Beta Pruning")
        self.root.geometry("1220x740")
        self.root.minsize(1050, 650)

        # Game state variables.
        self.game: Optional[Game] = None
        self.engine: Optional[Engine] = None
        self.human_color: Disc = Disc.Red
        self.computer_color: Disc = Disc.Yellow
        self.human_turn: bool = True
        self.ai_thinking: bool = False
        self.hover_col: Optional[int] = None
        self.tree_node_map: Dict[str, Dict[str, Any]] = {}

        # Setup UI variables.
        self.color_var = tk.StringVar(value="Red")
        self.starter_var = tk.StringVar(value="Human")
        self.depth_var = tk.IntVar(value=3)
        self.rows_var = tk.IntVar(value=6)
        self.cols_var = tk.IntVar(value=7)

        self._build_layout()
        self.start_new_game()

    # Builds the main setup bar, board canvas, and Minimax tree viewer.
    def _build_layout(self):
        # Top configuration bar.
        config_frame = ttk.LabelFrame(self.root, text="Game Parameters", padding=8)
        config_frame.pack(fill=tk.X, padx=10, pady=(8, 4))

        ttk.Label(config_frame, text="Your Color:").pack(side=tk.LEFT, padx=(4, 4))
        color_combo = ttk.Combobox(
            config_frame, textvariable=self.color_var, values=["Red", "Yellow"], state="readonly", width=8
        )
        color_combo.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(config_frame, text="First Turn:").pack(side=tk.LEFT, padx=(0, 4))
        starter_combo = ttk.Combobox(
            config_frame, textvariable=self.starter_var, values=["Human", "Computer"], state="readonly", width=10
        )
        starter_combo.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(config_frame, text="Depth K:").pack(side=tk.LEFT, padx=(0, 4))
        depth_spin = ttk.Spinbox(config_frame, from_=1, to=8, textvariable=self.depth_var, width=5)
        depth_spin.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(config_frame, text="Rows (>=6):").pack(side=tk.LEFT, padx=(0, 4))
        rows_spin = ttk.Spinbox(config_frame, from_=6, to=12, textvariable=self.rows_var, width=5)
        rows_spin.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(config_frame, text="Cols (>=7):").pack(side=tk.LEFT, padx=(0, 4))
        cols_spin = ttk.Spinbox(config_frame, from_=7, to=14, textvariable=self.cols_var, width=5)
        cols_spin.pack(side=tk.LEFT, padx=(0, 14))

        ttk.Button(config_frame, text="Start / Reset Game", command=self.start_new_game).pack(side=tk.LEFT, padx=4)

        # Main split area: Left = Game Board, Right = Minimax Tree & Heuristic Inspector.
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 10))

        # Left panel: Scoreboard + Board Canvas.
        left_frame = ttk.Frame(main_pane, padding=6)
        main_pane.add(left_frame, weight=3)

        score_frame = ttk.Frame(left_frame)
        score_frame.pack(fill=tk.X, pady=(0, 6))

        self.red_score_label = ttk.Label(score_frame, text="Red Connected-4s: 0", font=("Segoe UI", 11, "bold"), foreground="#c62828")
        self.red_score_label.pack(side=tk.LEFT, padx=(4, 16))

        self.yellow_score_label = ttk.Label(score_frame, text="Yellow Connected-4s: 0", font=("Segoe UI", 11, "bold"), foreground="#b28704")
        self.yellow_score_label.pack(side=tk.LEFT, padx=(0, 16))

        self.status_label = ttk.Label(left_frame, text="Your turn", font=("Segoe UI", 11, "bold"))
        self.status_label.pack(fill=tk.X, pady=(0, 6))

        self.canvas = tk.Canvas(left_frame, bg="#1565c0", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_board())
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", self._on_mouse_leave)
        self.canvas.bind("<Button-1>", self._on_board_click)

        # Right panel: Minimax Tree Trace & Board Heuristic Viewer.
        right_frame = ttk.LabelFrame(main_pane, text="Minimax Tree Trace & Heuristic Values", padding=6)
        main_pane.add(right_frame, weight=3)

        stats_bar = ttk.Frame(right_frame)
        stats_bar.pack(fill=tk.X, pady=(0, 6))

        self.stats_label = ttk.Label(stats_bar, text="Waiting for AI turn...", font=("Segoe UI", 9, "bold"))
        self.stats_label.pack(side=tk.LEFT)

        ttk.Button(stats_bar, text="Collapse All", command=lambda: self._toggle_all_tree(False)).pack(side=tk.RIGHT, padx=2)
        ttk.Button(stats_bar, text="Expand All", command=lambda: self._toggle_all_tree(True)).pack(side=tk.RIGHT, padx=2)

        # Treeview widget for tracing MAX/MIN/LEAF/PRUNED nodes.
        tree_container = ttk.Frame(right_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        columns = ("move", "depth", "order_h", "val", "bounds", "status")
        self.tree_view = ttk.Treeview(tree_container, columns=columns, show="tree headings", selectmode="browse")
        self.tree_view.heading("#0", text="Node Role")
        self.tree_view.heading("move", text="Col")
        self.tree_view.heading("depth", text="k")
        self.tree_view.heading("order_h", text="Order h")
        self.tree_view.heading("val", text="Heuristic / Val")
        self.tree_view.heading("bounds", text="[Alpha, Beta]")
        self.tree_view.heading("status", text="State")

        self.tree_view.column("#0", width=135, anchor=tk.W)
        self.tree_view.column("move", width=48, anchor=tk.CENTER)
        self.tree_view.column("depth", width=36, anchor=tk.CENTER)
        self.tree_view.column("order_h", width=62, anchor=tk.CENTER)
        self.tree_view.column("val", width=95, anchor=tk.CENTER)
        self.tree_view.column("bounds", width=115, anchor=tk.CENTER)
        self.tree_view.column("status", width=85, anchor=tk.CENTER)

        self.tree_view.tag_configure("pruned", foreground="#9e9e9e")
        self.tree_view.tag_configure("leaf", foreground="#1b5e20")
        self.tree_view.tag_configure("chosen", background="#e3f2fd")

        y_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree_view.yview)
        x_scroll = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree_view.xview)
        self.tree_view.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree_view.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tree_view.bind("<<TreeviewSelect>>", self._on_tree_node_select)

        # Selected node board & heuristic preview panel.
        inspector_frame = ttk.LabelFrame(right_frame, text="Selected Node Board State & Heuristic Value", padding=6)
        inspector_frame.pack(fill=tk.X, pady=(6, 0))

        self.node_info_label = ttk.Label(
            inspector_frame,
            text="Click any node in the Minimax tree above to inspect its board state and heuristic score.",
            font=("Segoe UI", 9)
        )
        self.node_info_label.pack(anchor=tk.W, pady=(0, 4))

        self.node_board_text = tk.Text(
            inspector_frame, height=8, font=("Consolas", 10), state=tk.DISABLED, bg="#f8f9fa", relief=tk.FLAT
        )
        self.node_board_text.pack(fill=tk.X)

    # Validates parameters and initializes a fresh Game and Engine instance.
    def start_new_game(self):
        if self.ai_thinking:
            return

        try:
            length = int(self.rows_var.get())
            width = int(self.cols_var.get())
            depth = int(self.depth_var.get())
        except tk.TclError:
            messagebox.showerror("Invalid Input", "Please enter valid integer values for K, Rows, and Cols.")
            return

        if length < 6 or width < 7:
            messagebox.showwarning("Invalid Dimensions", "Dimensions must satisfy Rows >= 6 and Cols >= 7.")
            return
        if depth < 1:
            messagebox.showwarning("Invalid Depth", "Depth K must be at least 1.")
            return

        self.human_color = Disc.Red if self.color_var.get() == "Red" else Disc.Yellow
        self.computer_color = self.human_color.get_other_color()
        self.human_turn = self.starter_var.get() == "Human"

        self.game = Game(length, width)
        self.engine = Engine(self.game, self.computer_color, depth)
        self.hover_col = None

        # Clear tree viewer.
        self.tree_view.delete(*self.tree_view.get_children())
        self.tree_node_map.clear()
        self.stats_label.config(text=f"Ready | Depth K={depth} | You={self.human_color.name}, AI={self.computer_color.name}")
        self._set_inspector_board("No AI tree generated yet.", [])

        self.update_scores_and_status()
        self.draw_board()

        if not self.human_turn:
            self._trigger_ai_move()

    # Draws the Connect 4 grid, discs, column indices, and hover preview.
    def draw_board(self):
        if self.game is None:
            return

        self.canvas.delete("all")
        w = max(self.canvas.winfo_width(), 200)
        h = max(self.canvas.winfo_height(), 200)

        rows = self.game.length
        cols = self.game.width
        top_margin = 52
        bottom_margin = 28
        side_margin = 16

        cell_size = min((w - 2 * side_margin) / cols, (h - top_margin - bottom_margin) / rows)
        board_w = cell_size * cols
        board_h = cell_size * rows
        offset_x = (w - board_w) / 2
        offset_y = top_margin

        # Top preview strip background.
        self.canvas.create_rectangle(0, 0, w, top_margin, fill="#eef3f8", outline="")

        # Hover disc indicator.
        if self.human_turn and not self.ai_thinking and not self.game.is_full() and self.hover_col is not None:
            if 0 <= self.hover_col < cols and self.game.is_valid(self.hover_col):
                cx = offset_x + (self.hover_col + 0.5) * cell_size
                cy = top_margin / 2
                r = cell_size * 0.36
                fill_color = "#e53935" if self.human_color == Disc.Red else "#fdd835"
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill_color, outline="#333333", width=2)

        # Board background.
        self.canvas.create_rectangle(
            offset_x, offset_y, offset_x + board_w, offset_y + board_h, fill="#1565c0", outline="#0d47a1", width=3
        )

        # Draw grid cells and discs.
        pad = cell_size * 0.12
        for r in range(rows):
            for c in range(cols):
                x1 = offset_x + c * cell_size + pad
                y1 = offset_y + r * cell_size + pad
                x2 = offset_x + (c + 1) * cell_size - pad
                y2 = offset_y + (r + 1) * cell_size - pad

                cell = self.game.board[r][c]
                if cell == Disc.Red:
                    color = "#e53935"
                elif cell == Disc.Yellow:
                    color = "#fdd835"
                else:
                    color = "#ffffff"

                self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline="#0d47a1", width=2)

        # Column labels along the bottom.
        for c in range(cols):
            cx = offset_x + (c + 0.5) * cell_size
            cy = offset_y + board_h + bottom_margin / 2
            self.canvas.create_text(cx, cy, text=str(c), fill="#ffffff", font=("Segoe UI", 10, "bold"))

    # Maps mouse x-coordinate to a board column index.
    def _pixel_to_col(self, x: float) -> Optional[int]:
        if self.game is None:
            return None
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        rows, cols = self.game.length, self.game.width
        cell_size = min((w - 32) / cols, (h - 80) / rows)
        board_w = cell_size * cols
        offset_x = (w - board_w) / 2
        if offset_x <= x <= offset_x + board_w:
            return int((x - offset_x) // cell_size)
        return None

    def _on_mouse_move(self, event):
        col = self._pixel_to_col(event.x)
        if col != self.hover_col:
            self.hover_col = col
            self.draw_board()

    def _on_mouse_leave(self, _event):
        self.hover_col = None
        self.draw_board()

    # Handles human column click.
    def _on_board_click(self, event):
        if self.game is None or self.engine is None:
            return
        if not self.human_turn or self.ai_thinking or self.game.is_full():
            return

        col = self._pixel_to_col(event.x)
        if col is None or not self.game.is_valid(col):
            return

        self.engine.update(col, self.human_color)
        self.draw_board()
        self.update_scores_and_status()

        if self.game.is_full():
            self._announce_winner()
            return

        self.human_turn = False
        self._trigger_ai_move()

    # Runs AI Minimax search on a background thread so the GUI remains responsive.
    def _trigger_ai_move(self):
        self.ai_thinking = True
        self.status_label.config(text=f"Computer ({self.computer_color.name}) is thinking (Depth K={self.engine.depth})...")
        self.draw_board()

        def _worker():
            chosen_col = self.engine.make_move()
            self.root.after(0, lambda: self._on_ai_move_complete(chosen_col))

        threading.Thread(target=_worker, daemon=True).start()

    # Updates board, scores, and Minimax tree view after AI finishes moving.
    def _on_ai_move_complete(self, chosen_col: Optional[int]):
        self.ai_thinking = False
        self.human_turn = True
        self.draw_board()
        self.update_scores_and_status()
        self._populate_tree_view()

        if self.game.is_full():
            self._announce_winner()
        elif chosen_col is not None:
            self.status_label.config(
                text=f"Computer played Column {chosen_col}. Your turn ({self.human_color.name})."
            )

    # Updates live connected-four counters and turn banner.
    def update_scores_and_status(self):
        if self.game is None:
            return
        red_score = self.game.calculate_score(Disc.Red)
        yellow_score = self.game.calculate_score(Disc.Yellow)
        self.red_score_label.config(text=f"Red Connected-4s: {red_score}")
        self.yellow_score_label.config(text=f"Yellow Connected-4s: {yellow_score}")

        if not self.game.is_full() and not self.ai_thinking and self.human_turn:
            self.status_label.config(text=f"Your turn ({self.human_color.name}) — click a column to drop a disc.")

    # Displays final scores, pruning stats, and benchmarking table when the board is full.
    def _announce_winner(self):
        red_score = self.game.calculate_score(Disc.Red)
        yellow_score = self.game.calculate_score(Disc.Yellow)
        human_score = red_score if self.human_color == Disc.Red else yellow_score
        ai_score = yellow_score if self.computer_color == Disc.Yellow else red_score

        if human_score > ai_score:
            result = f"Game Over — You Win! ({human_score} vs {ai_score})"
        elif ai_score > human_score:
            result = f"Game Over — Computer Wins! ({ai_score} vs {human_score})"
        else:
            result = f"Game Over — Draw! ({human_score} vs {ai_score})"

        self.status_label.config(text=result)

        summary_table = self.engine.format_summary_table()
        print("\n" + summary_table + "\n")

        summary_win = tk.Toplevel(self.root)
        summary_win.title("Game Summary & Alpha-Beta Pruning Benchmark")
        summary_win.geometry("760x450")

        ttk.Label(
            summary_win,
            text=f"Board is Full!   Red: {red_score}  |  Yellow: {yellow_score}\n{result}",
            font=("Segoe UI", 11, "bold"),
            justify=tk.CENTER
        ).pack(pady=10)

        text_box = tk.Text(summary_win, font=("Consolas", 10), bg="#f8f9fa")
        text_box.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        text_box.insert(tk.END, summary_table)
        text_box.config(state=tk.DISABLED)

    # Renders the AI's Minimax search tree into the GUI Treeview.
    def _populate_tree_view(self):
        self.tree_view.delete(*self.tree_view.get_children())
        self.tree_node_map.clear()

        if self.engine is None or self.engine.last_tree is None:
            return

        root_data = self.engine.last_tree
        chosen_col = root_data.get("chosen_col")
        total_seen = self.engine.nodes_expanded + self.engine.nodes_pruned
        prune_pct = (self.engine.nodes_pruned / total_seen * 100.0) if total_seen > 0 else 0.0
        self.stats_label.config(
            text=(
                f"Turn #{self.engine.turn_number} | Col: {chosen_col} | Eval: {root_data.get('value')} | "
                f"Expanded: {self.engine.nodes_expanded} | Pruned: {self.engine.nodes_pruned} ({prune_pct:.1f}%) | "
                f"Time: {self.engine.last_move_time * 1000:.2f} ms"
            )
        )

        def _insert_node(parent_iid: str, node_data: Dict[str, Any], is_chosen_branch: bool = False):
            col_str = str(node_data["column"]) if node_data["column"] is not None else "-"
            order_h_str = str(node_data["move_h"]) if node_data["move_h"] is not None else "-"
            val_str = "PRUNED" if node_data["pruned"] else str(node_data["value"])
            bounds_str = f"[{node_data['alpha']}, {node_data['beta']}]"

            if node_data["pruned"]:
                status_str = "PRUNED"
                tags = ("pruned",)
            elif node_data["is_leaf"]:
                status_str = "LEAF EVAL"
                tags = ("leaf",)
            elif is_chosen_branch:
                status_str = "CHOSEN"
                tags = ("chosen",)
            else:
                status_str = "EXPANDED"
                tags = ()

            iid = self.tree_view.insert(
                parent_iid,
                tk.END,
                text=node_data["role"],
                values=(col_str, node_data["k"], order_h_str, val_str, bounds_str, status_str),
                open=(node_data["k"] <= 1),
                tags=tags
            )
            self.tree_node_map[iid] = node_data

            for child in node_data.get("children", []):
                _insert_node(iid, child, False)

        # Insert root and its depth-1 children.
        root_iid = self.tree_view.insert(
            "",
            tk.END,
            text=root_data["role"],
            values=("-", 0, "-", str(root_data["value"]), f"[{root_data['alpha']}, {root_data['beta']}]", f"Col {chosen_col}"),
            open=True
        )
        self.tree_node_map[root_iid] = root_data

        for child in root_data.get("children", []):
            _insert_node(root_iid, child, is_chosen_branch=(child["column"] == chosen_col))

        self.tree_view.selection_set(root_iid)
        self._on_tree_node_select(None)

    def _toggle_all_tree(self, expand: bool):
        def _recurse(item_id: str):
            self.tree_view.item(item_id, open=expand)
            for child_id in self.tree_view.get_children(item_id):
                _recurse(child_id)

        for top_id in self.tree_view.get_children(""):
            _recurse(top_id)

    # Displays the selected tree node's 2D board and heuristic evaluation.
    def _on_tree_node_select(self, _event):
        selected = self.tree_view.selection()
        if not selected:
            return
        node_data = self.tree_node_map.get(selected[0])
        if not node_data:
            return

        col_str = f"Col {node_data['column']}" if node_data["column"] is not None else "Root"
        if node_data["pruned"]:
            summary = f"{node_data['role']} ({col_str}, k={node_data['k']}) — PRUNED before evaluation"
        elif node_data["is_leaf"]:
            summary = (
                f"{node_data['role']} ({col_str}, k={node_data['k']}) — "
                f"Leaf Heuristic Score = {node_data['value']} | [alpha={node_data['alpha']}, beta={node_data['beta']}]"
            )
        else:
            summary = (
                f"{node_data['role']} ({col_str}, k={node_data['k']}) — "
                f"Backed-Up Value = {node_data['value']} (Move Order h={node_data['move_h']}) | "
                f"[alpha={node_data['alpha']}, beta={node_data['beta']}]"
            )

        self._set_inspector_board(summary, node_data["board"])

    def _set_inspector_board(self, summary: str, board):
        self.node_info_label.config(text=summary)
        self.node_board_text.config(state=tk.NORMAL)
        self.node_board_text.delete("1.0", tk.END)
        if board:
            header = "   " + " ".join(str(c) for c in range(len(board[0]))) + "\n"
            body = "\n".join(
                f"{r}: " + Engine.format_board([row]) for r, row in enumerate(board)
            )
            self.node_board_text.insert(tk.END, header + body)
        self.node_board_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = Connect4GUI(root)
    root.mainloop()