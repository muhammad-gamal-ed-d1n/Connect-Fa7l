import heapq
import math
import time
from model import Game, Disc, Node
from typing import List, Optional, Dict, Any

class Engine:
    def __init__(self, game: Game, computer_color: Disc, depth: int):
        self.game: Game = game
        self.computer_color: Disc = computer_color
        self.depth: int = depth
        self.last_tree: Optional[Dict[str, Any]] = None
        self.nodes_expanded: int = 0
        self.last_move_time: float = 0.0
        self.turn_number: int = 0

    # Update board/ make move.
    def update(self, column: int, color: Disc):
        self.game.insert(column, color)

    # Computer move.
    def make_move(self) -> Optional[int]:
        if self.game.is_full():
            return None

        start_time: float = time.perf_counter()
        self.nodes_expanded = 0
        self.turn_number += 1

        best_score: float = -math.inf
        best_col: int = -1
        alpha: float = -math.inf
        beta: float = math.inf

        root_trace: Dict[str, Any] = {
            "role": "MAX (ROOT)",
            "column": None,
            "k": 0,
            "move_h": None,
            "value": None,
            "alpha": alpha,
            "beta": beta,
            "pruned": False,
            "is_leaf": False,
            "board": [row[:] for row in self.game.board],
            "children": []
        }

        # Create root children ordered by move-ordering heuristic.
        children: List[Node] = []
        for col in range(self.game.width):
            try:
                child: Node = Node(
                    board=[row[:] for row in self.game.board],
                    column=col,
                    color=self.computer_color,
                    alpha=alpha,
                    beta=beta,
                    k=1,
                    will_insert=True
                )

                # Make insertion.
                child.insert(col)

                # Change color.
                child.color = child.color.get_other_color()

                # Add child to heap.
                heapq.heappush_max(children, child)

            except IndexError:
                # Column was full, don't create child.
                continue

        while children:
            child: Node = heapq.heappop_max(children)
            child.alpha = alpha

            child_trace: Dict[str, Any] = {
                "role": "MIN",
                "column": child.column,
                "k": child.k,
                "move_h": child.h,
                "value": None,
                "alpha": child.alpha,
                "beta": child.beta,
                "pruned": False,
                "is_leaf": False,
                "board": [row[:] for row in child.board],
                "children": []
            }
            root_trace["children"].append(child_trace)

            val: int = self.minimize(child, self.depth, child_trace)
            child_trace["value"] = val
            child_trace["beta"] = child.beta

            if val > best_score:
                best_score = val
                best_col = child.column

            alpha = max(alpha, best_score)

        root_trace["value"] = best_score
        root_trace["alpha"] = alpha
        root_trace["chosen_col"] = best_col
        self.last_tree = root_trace
        self.last_move_time = time.perf_counter() - start_time

        # Print Minimax tree trace to console.
        self.print_tree()

        # Apply best move to game board.
        self.game.insert(best_col, self.computer_color)
        return best_col

    def maximize(self, node: Node, K: int, trace: Optional[Dict[str, Any]] = None) -> int:
        self.nodes_expanded += 1

        # Check whether we reached the maximum depth.
        if node.k == K:
            node.alpha = node.evaluate(self.computer_color)
            if trace is not None:
                trace["value"] = node.alpha
                trace["alpha"] = node.alpha
                trace["is_leaf"] = True
            return node.alpha # Return base heuristic.

        max_alpha: int = node.alpha

        # Create children.
        children: List[Node] = []
        for col in range(node.width):
            try:
                child: Node = Node(
                    board=[row[:] for row in node.board], # Must pass copy because the board gets mutated.
                    column=col,
                    color=node.color, # Don't change the color right away because we need to calculate the heuristic first.
                    alpha=node.alpha,
                    beta=node.beta,
                    k=node.k + 1,
                    will_insert=True # Minor optimization. Prevents calculating the heuristic twice.
                )

                # Make insertion.
                child.insert(col)

                # Change color.
                child.color = child.color.get_other_color()

                # Add child to heap.
                heapq.heappush_max(children, child)

            except IndexError:
                # Column was full, don't create child.
                continue

        if not children:
            val: int = node.evaluate(self.computer_color)
            if trace is not None:
                trace["value"] = val
                trace["is_leaf"] = True
            return val

        while children:
            child: Node = heapq.heappop_max(children)

            child.alpha = max_alpha # Update alpha.

            child_trace: Optional[Dict[str, Any]] = None
            if trace is not None:
                child_trace = {
                    "role": "MIN",
                    "column": child.column,
                    "k": child.k,
                    "move_h": child.h,
                    "value": None,
                    "alpha": child.alpha,
                    "beta": child.beta,
                    "pruned": False,
                    "is_leaf": False,
                    "board": [row[:] for row in child.board],
                    "children": []
                }
                trace["children"].append(child_trace)

            val: int = self.minimize(child, K, child_trace)

            if child_trace is not None:
                child_trace["value"] = val
                child_trace["beta"] = child.beta

            # Update alpha.
            max_alpha = max(val, max_alpha)

            # Pruning condition.
            if max_alpha >= node.beta:
                # Record remaining unvisited branches as pruned.
                if trace is not None:
                    while children:
                        pruned_child: Node = heapq.heappop_max(children)
                        trace["children"].append({
                            "role": "MIN",
                            "column": pruned_child.column,
                            "k": pruned_child.k,
                            "move_h": pruned_child.h,
                            "value": None,
                            "alpha": max_alpha,
                            "beta": node.beta,
                            "pruned": True,
                            "is_leaf": False,
                            "board": [row[:] for row in pruned_child.board],
                            "children": []
                        })
                break

        # Update node's alpha.
        node.alpha = max_alpha
        if trace is not None:
            trace["value"] = max_alpha
            trace["alpha"] = max_alpha

        return max_alpha

    def minimize(self, node: Node, K: int, trace: Optional[Dict[str, Any]] = None) -> Optional[int]:
        self.nodes_expanded += 1

        # Check if we hit the max depth K.
        if node.k == K:
            node.beta = node.evaluate(self.computer_color) # Update beta.
            if trace is not None:
                trace["value"] = node.beta
                trace["beta"] = node.beta
                trace["is_leaf"] = True
            return node.beta

        min_beta: int = node.beta

        # Create children.
        children: List[Node] = []
        for col in range(node.width):
            try:
                child: Node = Node(
                    board=[row[:] for row in node.board], # Must pass copy because the board gets mutated.
                    column=col,
                    color=node.color, # Don't change the color right away because we need to calculate the heuristic first.
                    alpha=node.alpha, 
                    beta=node.beta,
                    k=node.k + 1,
                    will_insert=True # Minor optimization. Prevents calculating the heuristic twice.
                )

                # Make insertion.
                child.insert(col)

                # Change color.
                child.color = child.color.get_other_color()

                # Add child to heap.
                heapq.heappush_max(children, child)

            except IndexError:
                # column was full, don't create child
                continue

        if not children:
            val: int = node.evaluate(self.computer_color)
            if trace is not None:
                trace["value"] = val
                trace["is_leaf"] = True
            return val

        while children:
            child: Node = heapq.heappop_max(children)

            child.beta = min_beta # Update beta.

            child_trace: Optional[Dict[str, Any]] = None
            if trace is not None:
                child_trace = {
                    "role": "MAX",
                    "column": child.column,
                    "k": child.k,
                    "move_h": child.h,
                    "value": None,
                    "alpha": child.alpha,
                    "beta": child.beta,
                    "pruned": False,
                    "is_leaf": False,
                    "board": [row[:] for row in child.board],
                    "children": []
                }
                trace["children"].append(child_trace)

            val: int = self.maximize(child, K, child_trace)

            if child_trace is not None:
                child_trace["value"] = val
                child_trace["alpha"] = child.alpha

            # Update beta.
            min_beta = min(min_beta, val)

            # Pruning condition.
            if node.alpha >= min_beta:
                # Record remaining unvisited branches as pruned.
                if trace is not None:
                    while children:
                        pruned_child: Node = heapq.heappop_max(children)
                        trace["children"].append({
                            "role": "MAX",
                            "column": pruned_child.column,
                            "k": pruned_child.k,
                            "move_h": pruned_child.h,
                            "value": None,
                            "alpha": node.alpha,
                            "beta": min_beta,
                            "pruned": True,
                            "is_leaf": False,
                            "board": [row[:] for row in pruned_child.board],
                            "children": []
                        })
                break

        # Update node's beta.
        node.beta = min_beta
        if trace is not None:
            trace["value"] = min_beta
            trace["beta"] = min_beta

        return min_beta

    # Formats a 2D board state into compact rows for console/GUI display.
    @staticmethod
    def format_board(board: List[List[Disc]]) -> str:
        symbols = {Disc.Vacant: ".", Disc.Red: "R", Disc.Yellow: "Y"}
        return "\n".join(" ".join(symbols[cell] for cell in row) for row in board)

    # Prints the last Minimax search tree with heuristic values to the console.
    def print_tree(self):
        if self.last_tree is None:
            return

        print("\n" + "=" * 68)
        print(
            f"AI Turn #{self.turn_number} | Depth K={self.depth} | "
            f"Chosen Col={self.last_tree.get('chosen_col')} | "
            f"Nodes Expanded={self.nodes_expanded} | Time={self.last_move_time * 1000:.2f} ms"
        )
        print("=" * 68)

        def _print_node(node_data: Dict[str, Any], prefix: str = "", is_last: bool = True):
            connector = "└── " if is_last else "├── "
            col_str = f"Col {node_data['column']}" if node_data["column"] is not None else "Root"
            if node_data["pruned"]:
                line = (
                    f"{prefix}{connector}[{node_data['role']}] {col_str} (k={node_data['k']}, "
                    f"order_h={node_data['move_h']}) -> PRUNED [alpha={node_data['alpha']}, beta={node_data['beta']}]"
                )
                print(line)
                return

            leaf_tag = " [LEAF HEURISTIC]" if node_data["is_leaf"] else ""
            order_str = f", order_h={node_data['move_h']}" if node_data["move_h"] is not None else ""
            line = (
                f"{prefix}{connector}[{node_data['role']}] {col_str} (k={node_data['k']}{order_str}) "
                f"-> val={node_data['value']} [alpha={node_data['alpha']}, beta={node_data['beta']}]{leaf_tag}"
            )
            print(line)

            # Print the board state and heuristic value at evaluated leaf nodes.
            if node_data["is_leaf"]:
                child_prefix = prefix + ("    " if is_last else "│   ")
                for row_str in self.format_board(node_data["board"]).splitlines():
                    print(f"{child_prefix}   {row_str}")

            children_list = node_data.get("children", [])
            for idx, child_node in enumerate(children_list):
                next_prefix = prefix + ("    " if is_last else "│   ")
                _print_node(child_node, next_prefix, idx == len(children_list) - 1)

        _print_node(self.last_tree)
        print("=" * 68 + "\n")