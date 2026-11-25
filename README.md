# Connect-Fa7l

Human-versus-computer Connect Four. The game uses a 6-row by 7-column board,
minimax with alpha-beta pruning, and continues until the board is full. The
winner is the player with the greater number of contiguous lines of four or
more discs.

## Run the GUI

```bash
python3 game_gui.py
```

The GUI requires Python's Tkinter module (often packaged separately as
`python3-tk` on Linux).

Choose your color and enter any positive integer search depth `K` before
starting (`K >= 1`; the default is 4). `K` counts plies from the current board.
Click a column to drop a disc. The right-hand panel displays up to 2,500 entries
from the computer's minimax tree, including each node's board heuristic (`h`),
minimax value (`V`), alpha/beta bounds, and pruned branches. If the limit is
reached, the panel clearly notes that the display is truncated; the search is
not truncated by this display limit. The search summary and a readable tree
(up to 2,000 nodes) are also printed to the terminal after each computer move.

## Benchmark search depths

Run searches at the default depths 1 through 4:

```bash
python3 benchmark.py
```

Choose any positive depths and, optionally, a comma-separated sequence of
1-based opening columns to benchmark a position reached by alternating Red
and Yellow:

```bash
python3 benchmark.py --depths 1 2 4 6 --opening 4,3,4,5
```

The report includes the chosen move, node count, and elapsed search time for
each depth. Search cost can grow rapidly with `K`; a deep search may therefore
take a long time. GUI searches run in a worker thread to keep the interface
interactive; starting a new game cancels the previous search. Tree-display
limits cap rendering work, not the minimax search itself.

The heuristic combines the connected-four score difference, center-column
preference, and open four-cell windows. Three-in-a-row windows whose empty
square is playable immediately receive extra weight to prioritize winning and
blocking threats. On a full board, evaluation uses only the final connected-
four score difference. Move ordering uses the same evaluation to improve
alpha-beta pruning. The score counts each maximal contiguous run of four or
more discs once.

Assignment-report notes: `K` counts each player's move as one ply. There is no
artificial upper bound on positive `K`, but search remains exponential and
the benchmark/GUI cannot make arbitrarily deep searches finish quickly. The
tree display limits affect presentation only. The game ends when the board is
full; a tie means both players have the same number of counted connected-four
runs. The minimax search does not end early after a win because the assignment
compares final connected-four scores.
