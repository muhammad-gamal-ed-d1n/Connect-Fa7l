import math
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
        self.board: List[List[int]] = [[Disc.Vacant] * width for _ in range(length)]

    def insert(self, column: int, color: Disc):
        # check validity.
        if not self.is_valid(column):
            raise IndexError('Invalid insertion into full column.')

        # determine position.
        pos: int = 0
        
        while pos < self.length and self.board[pos][column] == Disc.Vacant:
            pos+=1
        pos-=1

        # update position.
        self.board[pos][column] = color


    def is_valid(self, column) -> bool:
        return self.board[0][column] == Disc.Vacant

    # Calculates the actual score (number of connected fours) for a given color.
    def calculate_score(self, color: Disc) -> int:
        score: int = 0

        # Calculate horizontal connected fours.
        for i in range(self.length):

            j: int = 0
            while j < self.width:
                connection_length: int = 0

                # Find first connection.
                while j < self.width and self.board[i][j] != color:
                    j += 1

                if j >= self.width:
                    break

                # Get connection length.
                while j < self.width and self.board[i][j] == color:
                    connection_length += 1
                    j += 1

                if connection_length >= 4:
                    score += 1

        # Calculate vertical connected fours.
        for j in range(self.width):

            i: int = 0
            while i < self.length:
                connection_length: int = 0

                # Find first connection.
                while i < self.length and self.board[i][j] != color:
                    i += 1

                if i >= self.length:
                    break

                # Get connection length.
                while i < self.length and self.board[i][j] == color:
                    connection_length += 1
                    i += 1

                if connection_length >= 4:
                    score += 1

        # Calculate diagonal connected fours.
        for d in range(-(self.width - 1), self.length):

            r = max(0, d)
            c = max(0, -d)
            while r < self.length and c < self.width:
                connection_length: int = 0

                # Find first connection.
                while (r < self.length and c < self.width) and self.board[r][c] != color:
                    r += 1
                    c += 1

                if r >= self.length or c >= self.width:
                    break

                # Get connection length.
                while (r < self.length and c < self.width) and self.board[r][c] == color:
                    connection_length += 1
                    r += 1
                    c += 1

                if connection_length >= 4:
                    score += 1

        # Calculate anti-diagonal connected fours.
        for d in range(self.length + self.width - 1):

            r = max(0, d - (self.width - 1))
            c = min(self.width - 1, d)
            while r < self.length and c >= 0:
                connection_length: int = 0

                # Find first connection.
                while (r < self.length and c >= 0) and self.board[r][c] != color:
                    r += 1
                    c -= 1

                if r >= self.length or c < 0:
                    break

                # Get connection length.
                while (r < self.length and c >= 0) and self.board[r][c] == color:
                    connection_length += 1
                    r += 1
                    c -= 1

                if connection_length >= 4:
                    score += 1

        return score

'''
Represents branch decisions and their states.
    Arguments:
        board: the board from the previous node.
        column: the column we will insert in.
'''
class Node:
    def __init__(self, board: List[List[int]], column: int, color: Disc, alpha: int, beta: int, k: int = 0, will_insert: bool = False):
        self.board: List[List[int]] = board
        self.column: int = column
        self.color: Disc = color
        self.alpha: int = alpha
        self.beta: int = beta
        self.h: int = self.get_heuristic() if not will_insert else None
        self.k: int = k
        self.length: int = len(board)
        self.width: int = len(board[0])

    # Evaluate node heuristic.
    def evaluate(self, computer_color: Disc) -> int:
        human_color = computer_color.get_other_color()
        return self.get_base_heuristic(computer_color) - self.get_base_heuristic(human_color)

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

        # get anti-diagonal score
        i = pos + 1
        j = self.column - 1
        while i < length and j >= 0 and self.board[i][j] == self.color:
            i += 1
            j -= 1
            h += 1

        i = pos - 1
        j = self.column + 1
        while i >= 0 and j < width and self.board[i][j] == self.color:
            i -= 1
            j += 1
            h += 1

        # get anti-diagonal disconnection score
        i = pos + 1
        j = self.column - 1
        while i < length and j >= 0 and self.board[i][j] == self.color.get_other_color():
            i += 1
            j -= 1
            h += 1

        i = pos - 1
        j = self.column + 1
        while i >= 0 and j < width and self.board[i][j] == self.color.get_other_color():
            i -= 1
            j += 1
            h += 1

        return h

    def is_valid(self, column: int):
        return self.board[0][column] == Disc.Vacant

    def insert(self, column: int):
        # check validity.
        if not self.is_valid(column):
            raise IndexError('Invalid insertion into full column.')

        # determine position.
        pos: int = 0
        
        while self.board[pos][column] == Disc.Vacant:
            pos+=1
        pos-=1

        # update position.
        self.board[pos][column] = self.color

        # update heuristic
        self.h = self.get_heuristic()


    def __lt__(self, other: "Node"):
        if self.h == None:
            return False
        if other.h == None:
            return False

        return self.h > other.h

# Calculates the heuristic at the leaf nodes.
    def get_base_heuristic(self, color: Disc) -> int:
        h: float = 0

        # Calculate horizontal connections.
        for i in range(self.length):

            j: int = 0
            while j < self.width:
                connection_length: float = 0

                surrounded: bool = False
                left: bool = False
                right: bool = False
                while j < self.width and self.board[i][j] != color: # Find first connection.
                    j+=1

                if j >= self.width:
                    break

                # Check whether we are constrained on the left side.
                left = j - 1 < 0 or color.get_other_color() == self.board[i][j-1]

                # Get connection length.
                while j < self.width and self.board[i][j] == color:
                    connection_length+=1
                    j+=1

                right = j >= self.width or color.get_other_color() == self.board[i][j]
                
                surrounded = left and right

                if surrounded and connection_length < 4:
                    continue # Don't add the sum as it is useless to us.
                else:
                    # Check two steps forward for a possible connection.
                    if j + 1 < self.width and self.board[i][j] == Disc.Vacant and self.board[i][j + 1] == color:
                        h += 1 / 8
    
                    # Check two steps backwards for a possible connection.
                    start_j: int = j - int(connection_length)
                    if start_j - 2 >= 0 and self.board[i][start_j - 1] == Disc.Vacant and self.board[i][start_j - 2] == color:
                        h += 1 / 8
                    h += connection_length / 4

        # Calculate vertical connections.
        for j in range(self.width):

            i: int = 0
            while i < self.length:
                connection_length: float = 0

                surrounded: bool = False
                up: bool = False
                down: bool = False
                while i < self.length and self.board[i][j] != color: # Find first connection.
                    i+=1

                if i >= self.length:
                    break

                # Check whether we are constrained from upwards.
                up = i - 1 < 0 or color.get_other_color() == self.board[i-1][j]

                # Get connection length.
                while i < self.length and self.board[i][j] == color:
                    connection_length+=1
                    i+=1

                # Check whether we are constrained from downwards.
                down = i >= self.length or color.get_other_color() == self.board[i][j]
                
                surrounded = up and down

                if surrounded and connection_length < 4:
                    pass # Don't add the sum as it is useless to us.
                else:
                    # Check two steps forward for a possible connection.
                    if i + 1 < self.length and self.board[i][j] == Disc.Vacant and self.board[i + 1][j] == color:
                        h += 1 / 8

                    # Check two steps backwards for a possible connection.
                    start_i: int = i - int(connection_length)
                    if start_i - 2 >= 0 and self.board[start_i - 1][j] == Disc.Vacant and self.board[start_i - 2][j] == color:
                        h += 1 / 8
                    h += connection_length / 4

        # Calculate diagonal connections.
        for d in range(-(self.width - 1), self.length):

            r = max(0, d)
            c = max(0, -d)
            while r < self.length and c < self.width:
                connection_length: float = 0
                
                surrounded: bool = False
                up: bool = False
                down: bool = False

                # Find first connection.
                while (r < self.length and c < self.width) and self.board[r][c] != color:
                    r+=1
                    c+=1

                if r >= self.length or c >= self.width:
                    break

                # Check if we are constrained from upwards.
                if r - 1 < 0 or c - 1 < 0:
                    up = True
                else:
                    up = self.board[r-1][c-1] == color.get_other_color()
                

                # Get connection length.
                while (r < self.length and c < self.width) and self.board[r][c] == color:
                    connection_length+=1
                    r+=1
                    c+=1

                # Check if we are constrained from downwards.
                if r >= self.length or c >= self.width:
                    down = True
                else:
                    down = self.board[r][c] == color.get_other_color()

                surrounded = up and down
                if surrounded and connection_length < 4:
                    pass
                else:
                    # Check two steps forward for a possible connection.
                    if r + 1 < self.length and c + 1 < self.width and self.board[r][c] == Disc.Vacant and self.board[r + 1][c + 1] == color:
                        h += 1 / 8

                    # Check two steps backwards for a possible connection.
                    start_r: int = r - int(connection_length)
                    start_c: int = c - int(connection_length)
                    if start_r - 2 >= 0 and start_c - 2 >= 0 and self.board[start_r - 1][start_c - 1] == Disc.Vacant and self.board[start_r - 2][start_c - 2] == color:
                        h += 1 / 8

                    h += connection_length / 4

        # Calculate anti-diagonal connections.
        for d in range(self.length + self.width - 1):

            r = max(0, d - (self.width - 1))
            c = min(self.width - 1, d)
            while r < self.length and c >= 0:
                connection_length: float = 0
                
                surrounded: bool = False
                up: bool = False
                down: bool = False

                # Find first connection.
                while (r < self.length and c >= 0) and self.board[r][c] != color:
                    r += 1
                    c -= 1

                # Stop if we walked off the board without finding a disc.
                if r >= self.length or c < 0:
                    break

                # Check if we are constrained from upwards.
                up = r - 1 < 0 or c + 1 >= self.width or self.board[r - 1][c + 1] == color.get_other_color()

                # Get connection length.
                while (r < self.length and c >= 0) and self.board[r][c] == color:
                    connection_length += 1
                    r += 1
                    c -= 1

                # Check if we are constrained from downwards (bottom-left).
                down = r >= self.length or c < 0 or self.board[r][c] == color.get_other_color()

                surrounded = up and down
                if surrounded and connection_length < 4:
                    pass
                else:
                    # Check two steps forward for a possible connection.
                    if r + 1 < self.length and c - 1 >= 0 and self.board[r][c] == Disc.Vacant and self.board[r + 1][c - 1] == color:
                        h += 1 / 8

                    # Check two steps backwards for a possible connection.
                    start_r: int = r - int(connection_length)
                    start_c: int = c + int(connection_length)
                    if start_r - 2 >= 0 and start_c + 2 < self.width and self.board[start_r - 1][start_c + 1] == Disc.Vacant and self.board[start_r - 2][start_c + 2] == color:
                        h += 1 / 8
                    h += connection_length / 4
        
        return math.ceil(h)