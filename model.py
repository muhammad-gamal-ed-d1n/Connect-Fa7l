from enum import Enum
from typing import List, Optional
from model import Disc

class Disc(Enum):
    Vacant = 0
    Red = 1
    Yellow = 2

    def get_other_color(self):
        if self.value == 1: return Disc.Yellow
        if self.value == 2: return Disc.Red
        raise ValueError('Value of Disc.Vacant has no opposing value.')

# Represents game state.
class Game:
    def __init__(self, length: int, width: int):
        self.length: int = length
        self.width: int = width
        self.board: List[List[int]] = [[Disc.Vacant] * width] * length

    def insert(self, column: int, color: Disc):
        # check validity.
        if not self.is_valid(column):
            raise RuntimeError('Invalid insertion into full column.')

        # determine position.
        pos: int = 0
        
        while self.board[pos][column] == Disc.Vacant:
            pos+=1
        pos-=1

        # update position.
        self.board[pos][column] = color


    def is_valid(self, column) -> bool:
        return self.board[0][column] == Disc.Vacant

'''
Represents branch decisions and their states.
    Arguments:
        board: the board from the previous node.
        column: the column we will insert in.
'''
class Node:
    def __init__(self, board: List[List[int]], column: int, color: Disc, alpha: int, beta: int):
        self.board: List[List[int]] = board
        self.column: int = column
        self.color: Disc = color
        self.alpha: int = alpha
        self.beta: int = beta
        self.h = self.get_heuristic()

    # returns heuristic or null (if column is full)
    def get_heuristic(self) -> Optional[int]: 
        # check whether there is space or not
        length: int = len(self.board)
        width: int = len(self.board[0])
        if self.board[0][self.column] != Disc.Vacant:
            return None

        # get disc position
        pos: int = 1

        while pos < length and self.board[pos][self.column] == Disc.Vacant: pos+=1
        pos -= 1

        h: int = 0

        # get vertical connection score
        i: int = pos+1
        while i < length and self.board[i][self.column] == self.color:
            i+=1
            h+=1

        i = pos - 1
        while i >= 0 and self.board[i][self.column] == self.color:
            i-=1
            h+=1

        # get horizontal connection score
        j: int = self.column + 1
        while j < width and self.board[pos][j] == self.color:
            j+=1
            h+=1

        j = self.column - 1
        while j >= 0 and self.board[pos][j] == self.color:
            j-=1
            h+=1

        # get diagonal score
        i = pos + 1
        j = self.column + 1
        while i < length and j < width and self.board[i][j] == self.color:
            i+=1
            j+=1
            h+=1

        i = pos - 1
        j = self.column - 1
        while i >= 0 and j >= 0 and self.board[i][j] == self.color:
            i-=1
            j-=1
            h+=1

        # calculate disconnections

        # get vertical disconnection score
        i: int = pos+1
        while i < length and self.board[i][self.column] == self.color.get_other_color():
            i+=1
            h+=1

        i = pos - 1
        while i >= 0 and self.board[i][self.column] == self.color.get_other_color():
            i-=1
            h+=1

        # get horizontal disconnection score
        j: int = self.column + 1
        while j < width and self.board[pos][j] == self.color.get_other_color():
            j+=1
            h+=1

        j = self.column - 1
        while j >= 0 and self.board[pos][j] == self.color.get_other_color():
            j-=1
            h+=1

        # get diagonal disconnection score
        i = pos + 1
        j = self.column + 1
        while i < length and j < width and self.board[i][j] == self.color.get_other_color():
            i+=1
            j+=1
            h+=1

        i = pos - 1
        j = self.column - 1
        while i >= 0 and j >= 0 and self.board[i][j] == self.color.get_other_color():
            i-=1
            j-=1
            h+=1
    
        return h

        