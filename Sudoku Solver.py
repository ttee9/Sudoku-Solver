############################################################
# CIS 521: Homework 5
############################################################

student_name = "Thomas Tee"

############################################################
# Imports
############################################################

# Include your imports here, if any are used.
import collections
import copy
import itertools
import random
import math

############################################################
# Sudoku Solver
############################################################

def sudoku_cells():
    allCells = []
    for x in range(9):
        for y in range(9):
            allCells.append((x, y))
    return allCells

def sudoku_arcs():
    allArcs = []
    allCells = sudoku_cells()
    for cell1 in allCells:
        for cell2 in allCells:
            # same cell
            if cell1 == cell2:
                continue
            # same row
            if cell1[0] == cell2[0]:
                allArcs.append((cell1, cell2))
                continue
            # same column
            if cell1[1] == cell2[1]:
                allArcs.append((cell1, cell2))
                continue
            # same block
            # // used for integer division
            if cell1[0]//3 == cell2[0]//3 and cell1[1]//3 == cell2[1]//3:
                allArcs.append((cell1, cell2))
    return allArcs

def read_board(path):
    f = open(path)
    # Board is dictionary with coordinates as key
    board = {}
    row = 0
    # Read each line
    for line in f:
        # Read each char
        for col in range(9):
            if line[col] == '*':
                board[(row, col)] = set(range(1, 10))
            else:
                board[(row, col)] = set([int(line[col])])
        row = row + 1
    return board

class Sudoku(object):

    CELLS = sudoku_cells()
    ARCS = sudoku_arcs()

    def __init__(self, board):
        self.board = board

    def get_values(self, cell):
        return self.board[cell]

    def remove_inconsistent_values(self, cell1, cell2):
        # ARCS pair
        if (cell1, cell2) in self.ARCS:
            # Cell2 is one value and certain
            if self.is_certain(cell2):
                # Cell2 is a subset of cell1
                if self.board[cell2].issubset(self.board[cell1]):
                    # Remove cell2 value from cell1 set using difference_update
                    # This removes inconsistent values
                    self.board[cell1].difference_update(self.board[cell2])
                    return True
        return False

    def is_certain(self, cell):
        # If cell value is 1, then it is certain
        if len(self.board[cell]) == 1:
            return True
        return False

    def infer_ac3(self):
        queue = set()
        # Go through all ARCS and create queue
        for arcs in self.ARCS:
            # Cell1 is not certain and Cell2 is certain (remove_inconsistent_values capable)
            if not self.is_certain(arcs[0]) and self.is_certain(arcs[1]):
                queue.add(arcs)
        # Go through queue
        while queue:
            firstArcs = queue.pop()
            # Perform remove_inconsistent_values to narrow down Cell1
            if self.remove_inconsistent_values(firstArcs[0], firstArcs[1]):
                # If Cell1 is only one value now certain
                if self.is_certain(firstArcs[0]):
                    # Go through all arcs again
                    for secondArcs in self.ARCS:
                        # Use Cell1 from firstArcs (which is now certain) as Cell2 to narrow down Cell1 from arcs
                        if secondArcs[1] == firstArcs[0] and not self.is_certain(secondArcs[0]):
                            queue.add(secondArcs)

    def infer_improved(self):
        # infer_ac3
        self.infer_ac3()
        while self.infer_improved_helper():
            self.infer_ac3()

    def infer_improved_helper(self):
        is_changed = False
        if not self.is_solvable():
            # Return false
            return is_changed
        # Go through all cells
        for cell in self.CELLS:
            # Check that more than one value in cell
            if len(self.board[cell]) > 1:
                # Go through each value in Cell
                for value in self.board[cell]:
                    # Exam possible values for other cells in the same row
                    do_change = True
                    # For all columns
                    for col in range(9):
                        neighbor = (cell[0], col)
                        # Skip itself
                        if neighbor == cell:
                            continue
                        # If cell's value is one of neighbor's possible values, cell's value is not unique
                        if value in self.board[neighbor]:
                            do_change = False
                            break
                    # If value is unique, make change, stop and break out of loop
                    if do_change == True:
                        self.board[cell] = set([value])
                        is_changed = True
                        break
                    # Exam possible values for other cells in the same column
                    do_change = True
                    for row in range(9):
                        neighbor = (row, cell[1])
                        if neighbor == cell:
                            continue
                        if value in self.board[neighbor]:
                            do_change = False
                            break
                    if do_change == True:
                        self.board[cell] = set([value])
                        is_changed = True
                        break
                    # Exam possible values for other cells in the same block
                    do_change = True
                    block_row = cell[0] // 3 * 3
                    block_col = cell[1] // 3 * 3
                    for delta_row in range(3):
                        for delta_col in range(3):
                            neighbor = (block_row + delta_row, block_col + delta_col)
                            if neighbor == cell:
                                continue
                            if value in self.board[neighbor]:
                                do_change = False
                                break
                    if do_change == True:
                        self.board[cell] = set([value])
                        is_changed = True
                        break
        return is_changed

    def infer_with_guessing(self):
        self.infer_improved()
        self.board = self.infer_with_guessing_helper()

    def infer_with_guessing_helper(self):
        # If Solved, return board
        if self.is_solved():
            return self.board
        # Choose a cell based on heuristics
        cell = self.heuristics()
        # Guess each of the values for cell
        for value in self.board[cell]:
            # Make copy in case guess is wrong
            sudoku = copy.deepcopy(self)
            # For cell to guess value
            sudoku.board[cell] = set([value])
            # Implement infer_improved
            sudoku.infer_improved()
            # If still solvable after guessing
            if sudoku.is_solvable():
                # Recurse further down the tree and guess again
                solution = sudoku.infer_with_guessing_helper()
                # Solution has been found
                if solution is not None:
                    # Pass solution back up tree
                    return solution
                # If solution is none, return nothing

    def heuristics(self):
        uncertain_cells = set()
        # Most constrained variable (least possible values)
        min_length = float('inf')
        for cell in self.CELLS:
            # Length of values
            length = len(self.board[cell])
            if length > 1:
                # Uncertain cells have more than 1 value
                uncertain_cells.add(cell)
                # Determine most constrained variable (At least 2 values)
                if length < min_length:
                    heuristic1 = set([cell])
                # Tie of most constrained variables
                elif length == min_length:
                    heuristic1.add(cell)
        # Most constraining variable (most number of neighbors)
        max_length = 0
        if len(heuristic1) > 1:
            # For each cell in heuristic1
            for cell in heuristic1:
                count = 0
                # Return cells only in uncertain cells but not in cell (from heuristic1)
                for another_cell in uncertain_cells.difference(set(cell)):
                    # Add up the number of neighbors in each cell using self.ARCS
                    # If cell and another cell has arc, add 1 to count
                    if (cell, another_cell) in self.ARCS:
                        count += 1
                # Find a most constraining variable
                if count > max_length:
                    max_length = count
                    heuristic2 = cell
            return heuristic2
        else:
            # Cannot break tie, return the top cell from heuristic1
            return heuristic1.pop()

    def is_solved(self):
        for cell in self.CELLS:
            # Check if every cell is solved or not
            if self.is_certain(cell) is False:
                return False
        return True

    def is_solvable(self):
        for cell in self.CELLS:
            # If one of the cells has a value of 0, it is not solvable
            if len(self.board[cell]) == 0:
                return False
        return True
