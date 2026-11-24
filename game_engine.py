import heapq
from model import Game, Disc, Node
from typing import List, Optional

class Engine:
    def __init__(self, game, computer_color: Disc, depth: int):
        self.game: Game = game
        self.computer_color: Disc = computer_color
        self.depth: int = depth

    # Update board/ make move.
    def update(self, column: int, color: Disc):
        self.game.insert(column, color)

    # Computer move.
    def make_move(self):
        pass

    def maximize(self, node: Node, K: int) -> int:
        # Check whether we reached the maximum depth.
        if node.k == K:
            node.alpha = node.evaluate(self.computer_color)
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
                    will_insert=True # Minor optimization. Prevents calulcuating the heuristic twice.
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
            return node.evaluate(self.computer_color)
            
        while children:
            child: Node = heapq.heappop_max(children)

            child.alpha = max_alpha # Update alpha.

            val: int = self.minimize(child, K)

            # Update alpha.
            max_alpha = max(val, max_alpha)

            # Pruning condition.
            if max_alpha >= node.beta: break

        # Update node's alpha.
        node.alpha = max_alpha

        return max_alpha

    def minimize(self, node: Node, K: int) -> Optional[int]:
        # Check if we hit the max depth K.
        if node.k == K:
            node.beta = node.evaluate(self.computer_color) # Update beta.
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
                    will_insert=True # Minor optimization. Prevents calulcuating the heuristic twice.
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
            return node.evaluate(self.computer_color)

        while children:
            child: Node = heapq.heappop_max(children)

            child.beta = min_beta # Update beta.

            val: int = self.maximize(child, K)

            # Update beta.
            min_beta = min(min_beta, val)

            # Pruning condition.
            if node.alpha >= min_beta: break

        # Update node's beta.
        node.beta = min_beta

        return min_beta