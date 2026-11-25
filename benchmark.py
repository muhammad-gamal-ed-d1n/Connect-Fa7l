"""Compare minimax search time and node counts at selected depths."""

import argparse

from game_engine import Engine
from model import Disc, Game


def parse_args() -> argparse.Namespace:
    """Parse depth and optional opening moves for a reproducible benchmark."""
    parser = argparse.ArgumentParser(
        description="Benchmark Connect Four minimax at one or more K values."
    )
    parser.add_argument(
        "--depths",
        nargs="+",
        type=int,
        default=[1, 2, 3, 4],
        metavar="K",
        help="positive search depths to compare (default: 1 2 3 4)",
    )
    parser.add_argument(
        "--opening",
        default="",
        metavar="COLUMNS",
        help="optional comma-separated 1-based opening columns, e.g. 4,3,4,5",
    )
    return parser.parse_args()


def make_position(opening: str) -> tuple[Game, Disc]:
    """Build a legal opening and return the color whose turn is next."""
    game = Game()
    if not opening:
        return game, Disc.Red

    color = Disc.Red
    try:
        columns = [int(value.strip()) - 1 for value in opening.split(",")]
    except ValueError as error:
        raise ValueError("Opening columns must be comma-separated integers.") from error
    for column in columns:
        game.insert(column, color)
        color = color.get_other_color()
    return game, color


def main() -> None:
    """Run each requested search and report move, nodes, and elapsed seconds."""
    args = parse_args()
    if any(depth < 1 for depth in args.depths):
        raise SystemExit("Every K value must be a positive integer.")
    try:
        position, side_to_move = make_position(args.opening)
    except (ValueError, IndexError) as error:
        raise SystemExit(str(error)) from error

    print("K  move  nodes  seconds")
    for depth in args.depths:
        game = position.copy()
        engine = Engine(game, side_to_move, depth)
        column = engine.choose_move()
        move = "-" if column is None else str(column + 1)
        print(
            f"{depth}  {move:>4}  {engine.nodes_expanded:>5}  "
            f"{engine.search_seconds:.6f}"
        )


if __name__ == "__main__":
    main()
