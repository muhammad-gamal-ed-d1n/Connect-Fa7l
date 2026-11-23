from model import Game, Disc

class Engine:
    def __init__(self, game):
        self.game: Game = game

    # update board/ make move.
    def update(self, column: int, color: Disc):
        self.game.insert(column, color)

    # computer minmax logic
    def make_move(self):
        pass