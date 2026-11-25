import math
from enum import Enum
from typing import List, Optional

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
        self.board: List[List[Disc]] = [[Disc.Vacant] * width for _ in range(length)]

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

    # Checks whether the board is completely full.
    def is_full(self) -> bool:
        return all(cell != Disc.Vacant for cell in self.board[0])

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
    def __init__(self, board: List[List[Disc]], column: int, color: Disc, alpha: int, beta: int, k: int = 0, will_insert: bool = False):
        self.board: List[List[Disc]] = board
        self.column: int = column
        self.color: Disc = color
        self.alpha: int = alpha
        self.beta: int = beta
        self.h: Optional[int] = self.get_heuristic() if not will_insert else None
        self.k: int = k
        self.length: int = len(board)
        self.width: int = len(board[0])

    # Evaluate node heuristic.
    def evaluate(self, computer_color: Disc) -> int:
        human_color = computer_color.get_other_color()
        return self.get_base_heuristic(computer_color) - int(1.25 * self.get_base_heuristic(human_color))

    # Helper to weight longer connections non-linearly.
    @staticmethod
    def _connection_weight(connection_length: int) -> int:
        if connection_length >= 4:
            return 100
        if connection_length == 3:
            return 25
        if connection_length == 2:
            return 5
        return 1

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

        # Small center-column preference to break ties naturally instead of always picking col 0.
        h: int = (width // 2) - abs(self.column - (width // 2))

        # get vertical connection score
        i: int = pos+1
        while i < length and self.board[i][self.column] == self.color:
            i+=1
            h+=2
        if i + 1 < length and self.board[i][self.column] == Disc.Vacant and self.board[i + 1][self.column] == self.color:
            h += 1

        i = pos - 1
        while i >= 0 and self.board[i][self.column] == self.color:
            i-=1
            h+=2
        if i - 1 >= 0 and self.board[i][self.column] == Disc.Vacant and self.board[i - 1][self.column] == self.color:
            h += 1

        # get horizontal connection score
        j: int = self.column + 1
        while j < width and self.board[pos][j] == self.color:
            j+=1
            h+=2
        if j + 1 < width and self.board[pos][j] == Disc.Vacant and self.board[pos][j + 1] == self.color:
            h += 1

        j = self.column - 1
        while j >= 0 and self.board[pos][j] == self.color:
            j-=1
            h+=2
        if j - 1 >= 0 and self.board[pos][j] == Disc.Vacant and self.board[pos][j - 1] == self.color:
            h += 1

        # get diagonal score
        i = pos + 1
        j = self.column + 1
        while i < length and j < width and self.board[i][j] == self.color:
            i+=1
            j+=1
            h+=2
        if i + 1 < length and j + 1 < width and self.board[i][j] == Disc.Vacant and self.board[i + 1][j + 1] == self.color:
            h += 1

        i = pos - 1
        j = self.column - 1
        while i >= 0 and j >= 0 and self.board[i][j] == self.color:
            i-=1
            j-=1
            h+=2
        if i - 1 >= 0 and j - 1 >= 0 and self.board[i][j] == Disc.Vacant and self.board[i - 1][j - 1] == self.color:
            h += 1

        # get anti-diagonal score
        i = pos + 1
        j = self.column - 1
        while i < length and j >= 0 and self.board[i][j] == self.color:
            i += 1
            j -= 1
            h += 2
        if i + 1 < length and j - 1 >= 0 and self.board[i][j] == Disc.Vacant and self.board[i + 1][j - 1] == self.color:
            h += 1

        i = pos - 1
        j = self.column + 1
        while i >= 0 and j < width and self.board[i][j] == self.color:
            i -= 1
            j += 1
            h += 2
        if i - 1 >= 0 and j + 1 < width and self.board[i][j] == Disc.Vacant and self.board[i - 1][j + 1] == self.color:
            h += 1

        # calculate disconnections

        # get vertical disconnection score
        i = pos+1
        while i < length and self.board[i][self.column] == self.color.get_other_color():
            i+=1
            h+=2

        i = pos - 1
        while i >= 0 and self.board[i][self.column] == self.color.get_other_color():
            i-=1
            h+=2

        # get horizontal disconnection score
        j = self.column + 1
        while j < width and self.board[pos][j] == self.color.get_other_color():
            j+=1
            h+=2

        j = self.column - 1
        while j >= 0 and self.board[pos][j] == self.color.get_other_color():
            j-=1
            h+=2

        # get diagonal disconnection score
        i = pos + 1
        j = self.column + 1
        while i < length and j < width and self.board[i][j] == self.color.get_other_color():
            i+=1
            j+=1
            h+=2

        i = pos - 1
        j = self.column - 1
        while i >= 0 and j >= 0 and self.board[i][j] == self.color.get_other_color():
            i-=1
            j-=1
            h+=2

        # get anti-diagonal disconnection score
        i = pos + 1
        j = self.column - 1
        while i < length and j >= 0 and self.board[i][j] == self.color.get_other_color():
            i += 1
            j -= 1
            h += 2

        i = pos - 1
        j = self.column + 1
        while i >= 0 and j < width and self.board[i][j] == self.color.get_other_color():
            i -= 1
            j += 1
            h += 2

        return h
    
    def is_valid(self, column: int) -> bool:
        return self.board[0][column] == Disc.Vacant

    def insert(self, column: int):
        # check validity.
        if not self.is_valid(column):
            raise IndexError('Invalid insertion into full column.')

        # update heuristic before placing disc.
        self.h = self.get_heuristic()

        # determine position.
        pos: int = 0
        
        while pos < self.length and self.board[pos][column] == Disc.Vacant:
            pos+=1
        pos-=1

        # update position.
        self.board[pos][column] = self.color

    def __lt__(self, other: "Node"):
        if self.h is None:
            return False
        if other.h is None:
            return True

        return self.h > other.h

    # Calculates the heuristic at the leaf nodes.
    def get_base_heuristic(self, color: Disc) -> int:
        h: int = 0

        # Calculate horizontal connections.
        for i in range(self.length):

            j: int = 0
            while j < self.width:
                connection_length: int = 0

                while j < self.width and self.board[i][j] != color: # Find first connection.
                    j += 1

                if j >= self.width:
                    break

                start_j: int = j

                # Count vacant space available to the left.
                left_space: int = 0
                k: int = start_j - 1
                while k >= 0 and self.board[i][k] == Disc.Vacant and left_space < 4:
                    left_space += 1
                    k -= 1

                # Get connection length.
                while j < self.width and self.board[i][j] == color:
                    connection_length += 1
                    j += 1

                # Count vacant space available to the right.
                right_space: int = 0
                k = j
                while k < self.width and self.board[i][k] == Disc.Vacant and right_space < 4:
                    right_space += 1
                    k += 1

                # Skip if there isn't enough room to ever form 4-in-a-row.
                if connection_length + left_space + right_space < 4:
                    continue
                else:
                    # Check two steps forward for a possible connection.
                    if j + 1 < self.width and self.board[i][j] == Disc.Vacant and self.board[i][j + 1] == color:
                        h += 3

                    # Check two steps backwards for a possible connection.
                    if start_j - 2 >= 0 and self.board[i][start_j - 1] == Disc.Vacant and self.board[i][start_j - 2] == color:
                        h += 3

                    h += self._connection_weight(connection_length)

        # Calculate vertical connections.
        for j in range(self.width):

            i: int = 0
            while i < self.length:
                connection_length: int = 0

                while i < self.length and self.board[i][j] != color: # Find first connection.
                    i += 1

                if i >= self.length:
                    break

                start_i: int = i

                # Count vacant space available upwards.
                up_space: int = 0
                k: int = start_i - 1
                while k >= 0 and self.board[k][j] == Disc.Vacant and up_space < 4:
                    up_space += 1
                    k -= 1

                # Get connection length.
                while i < self.length and self.board[i][j] == color:
                    connection_length += 1
                    i += 1

                # Count vacant space available downwards.
                down_space: int = 0
                k = i
                while k < self.length and self.board[k][j] == Disc.Vacant and down_space < 4:
                    down_space += 1
                    k += 1

                # Skip if column doesn't have enough height left to form 4-in-a-row.
                if connection_length + up_space + down_space < 4:
                    pass
                else:
                    # Check two steps forward for a possible connection.
                    if i + 1 < self.length and self.board[i][j] == Disc.Vacant and self.board[i + 1][j] == color:
                        h += 3

                    # Check two steps backwards for a possible connection.
                    if start_i - 2 >= 0 and self.board[start_i - 1][j] == Disc.Vacant and self.board[start_i - 2][j] == color:
                        h += 3

                    h += self._connection_weight(connection_length)

        # Calculate diagonal connections.
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

                start_r: int = r
                start_c: int = c

                # Count vacant space available up-left.
                up_space: int = 0
                kr, kc = start_r - 1, start_c - 1
                while kr >= 0 and kc >= 0 and self.board[kr][kc] == Disc.Vacant and up_space < 4:
                    up_space += 1
                    kr -= 1
                    kc -= 1

                # Get connection length.
                while (r < self.length and c < self.width) and self.board[r][c] == color:
                    connection_length += 1
                    r += 1
                    c += 1

                # Count vacant space available down-right.
                down_space: int = 0
                kr, kc = r, c
                while kr < self.length and kc < self.width and self.board[kr][kc] == Disc.Vacant and down_space < 4:
                    down_space += 1
                    kr += 1
                    kc += 1

                if connection_length + up_space + down_space < 4:
                    pass
                else:
                    # Check two steps forward for a possible connection.
                    if r + 1 < self.length and c + 1 < self.width and self.board[r][c] == Disc.Vacant and self.board[r + 1][c + 1] == color:
                        h += 3

                    # Check two steps backwards for a possible connection.
                    if start_r - 2 >= 0 and start_c - 2 >= 0 and self.board[start_r - 1][start_c - 1] == Disc.Vacant and self.board[start_r - 2][start_c - 2] == color:
                        h += 3

                    h += self._connection_weight(connection_length)

        # Calculate anti-diagonal connections.
        for d in range(self.length + self.width - 1):

            r = max(0, d - (self.width - 1))
            c = min(self.width - 1, d)
            while r < self.length and c >= 0:
                connection_length: int = 0

                # Find first connection.
                while (r < self.length and c >= 0) and self.board[r][c] != color:
                    r += 1
                    c -= 1

                # Stop if we walked off the board without finding a disc.
                if r >= self.length or c < 0:
                    break

                start_r: int = r
                start_c: int = c

                # Count vacant space available up-right.
                up_space: int = 0
                kr, kc = start_r - 1, start_c + 1
                while kr >= 0 and kc < self.width and self.board[kr][kc] == Disc.Vacant and up_space < 4:
                    up_space += 1
                    kr -= 1
                    kc += 1

                # Get connection length.
                while (r < self.length and c >= 0) and self.board[r][c] == color:
                    connection_length += 1
                    r += 1
                    c -= 1

                # Count vacant space available down-left.
                down_space: int = 0
                kr, kc = r, c
                while kr < self.length and kc >= 0 and self.board[kr][kc] == Disc.Vacant and down_space < 4:
                    down_space += 1
                    kr += 1
                    kc -= 1

                if connection_length + up_space + down_space < 4:
                    pass
                else:
                    # Check two steps forward for a possible connection.
                    if r + 1 < self.length and c - 1 >= 0 and self.board[r][c] == Disc.Vacant and self.board[r + 1][c - 1] == color:
                        h += 3

                    # Check two steps backwards for a possible connection.
                    if start_r - 2 >= 0 and start_c + 2 < self.width and self.board[start_r - 1][start_c + 1] == Disc.Vacant and self.board[start_r - 2][start_c + 2] == color:
                        h += 3

                    h += self._connection_weight(connection_length)

        return h