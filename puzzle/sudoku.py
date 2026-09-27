import functools, itertools

# Top row is A, bottom row is I. Left column in 1, right column is 9.
# E.g, in order to specify the value of the bottom left cell, you can type: sudoku.I1 = 3

# TODO: Support non 9x9 boards

# TODO: A helpful optimization that's essentially another (relatively trivial) sudoku solving trick:
# for each pair of cell permutations with more than 1 cell in common: filter on "co-permutations".
# This will probably remove the need to add the `legal()` clause in `gen_caged_permutation`

# TODO: Some sudokus still may be unsolvable with this script. The next obvious step would be to add backtracking.
# For backtracking it's probably better to track the guesses and their side-effects (responses from `reduce`), than to copy the whole board in each recursion.
# To do this, change `_reduce_d` to return _which_ cells changed instead of "whether a cell changed".
# Possibly return the cell's _before_ and _after_ values (or even just the _before_ value). Maybe also changes to the permutations?

VALUES = range(1, 10)
ROWS = 'ABCDEFGHI'
COLUMNS = VALUES

# A list of cells and all legal permutations for these cells. The list shrinks as solving progresses until a single permutation remains
class CellPermutation:
  def __init__(self, cells, permutations):
    self.cells = cells
    self.permutations = permutations
  def reduce(self, d):
    self.permutations = [perm for perm in self.permutations if self._legal(perm, d)]
    return self._reduce_d(d)
  def _legal(self, perm, d):
    return all(v in d[c] for c, v in zip(self.cells, perm))
  def _reduce_d(self, d):
    changed = False
    new_values = {c: set() for c in self.cells}
    for perm in self.permutations:
      for c, v in zip(self.cells, perm):
        new_values[c].add(v)
    for c in self.cells:
      if len(new_values[c]) < len(d[c]):
        d[c] = new_values[c]
        changed = True
    return changed


@functools.cache
def perms(length, total):
  """Return all permutations (repetitions allowed) of size `length` that sum up to `total`"""
  if length == 1:
    return [(total,)]
  retval = []
  for first in range(max(1, total - (length - 1) * 9), min(10, 2 + total - length)):
    for perm in perms(length - 1, total - first):
      retval.append((first,) + perm)
  return retval


def same_block(c1, c2):
  return ROWS.index(c1[0]) // 3 == ROWS.index(c2[0]) // 3 and COLUMNS.index(int(c1[1])) // 3 == COLUMNS.index(int(c2[1])) // 3


def cant_be_same(c1, c2):
  # asserts whether two different cells may be the same by checking if they're in the same row, column or block.
  return c1[0] == c2[0] or c1[1] == c2[1] or same_block(c1, c2)


def legal(cells, perm):
  for i, j in itertools.combinations(range(len(cells)), 2):
    if perm[i] == perm[j] and cant_be_same(cells[i], cells[j]):
      return False
  return True


def gen_caged_permutation(cells, total):
  # caged_permutation is a permutation where a specific list of cells must sum up to a given value
  cells = cells.split()
  permutations = [perm for perm in perms(len(cells), total) if legal(cells, perm)]
  return CellPermutation(cells, permutations)


def aux_constrained_permutations(legal_values, used, indices, solutions, new_solution):
  if indices:
    # if there are still indices not populated, iterate over the possible values for the first one:
    for new_solution[indices[0]] in legal_values[indices[0]] - used:
      # and recursively dive deeper into the remaining indices left to populate
      aux_constrained_permutations(legal_values, used | {new_solution[indices[0]]}, indices[1:], solutions, new_solution)
  else:
    solutions.append(tuple(new_solution)) # save a copy since `new_solution` mutates through the recursion
  return solutions


def gen_constrained_permutation(cells, d):
  # A "constrained_permutation" is a list of cells where all values must be unique
  # legal_values is a list of sets from which the values can be chosen
  legal_values = [d[cell] for cell in cells]
  # `indices` is a suggested order of assignment of the cells to find collisions as early as possible in the recursion
  indices = tuple(i for i, _ in sorted(enumerate(legal_values), key=lambda pair: len(pair[1])))
  permutations = aux_constrained_permutations(legal_values, set(), indices, [], [0] * len(indices))
  return CellPermutation(cells, permutations)


def cell_str(s):  # For print_board
  if len(s) == 1:
    return str(next(iter(s)))
  return '(' + ''.join(map(str, s)) + ')'


def chunks(l, size):  # For print_board
  return zip(*[iter(l)] * size)


class Sudoku:
  def __init__(self):
    # assigning using __dict__ because I'm overriding __setattr__. Maybe not worth it after all...
    # d holds the legal values for each cell:
    self.__dict__['d'] = {f'{c}{i}': set(VALUES) for c, i in itertools.product(ROWS, COLUMNS)}
    # cell_permutations holds a list of constraints on the grid.
    self.__dict__['cell_permutations'] = []

  def __setattr__(self, name, value):
    if name in self.d:
      self.d[name] = {value}
    else:
      super().__setattr__(name, value)

  def __getattr__(self, name):
    value = self.d[name]
    if len(value) == 1:
      return next(iter(value))
    return value

  def add_cell_permutation(self, cell_permutation):
    self.cell_permutations.append(cell_permutation)
    cell_permutation.reduce(self.d)

  def add_row_permutations(self):
    row_permutations = [gen_constrained_permutation([f'{c}{i}' for i in COLUMNS], self.d) for c in ROWS]
    for cell_permutation in row_permutations:
      self.add_cell_permutation(cell_permutation)

  def add_col_permutations(self):
    col_permutations = [gen_constrained_permutation([f'{c}{i}' for c in ROWS], self.d) for i in COLUMNS]
    for cell_permutation in col_permutations:
      self.add_cell_permutation(cell_permutation)

  def add_block_permutations(self):
    block_permutations = [gen_constrained_permutation([f'{ROWS[base // 3 * 3 + i // 3]}{VALUES[base % 3 * 3 + i % 3]}' for i in range(9)], self.d) for base in range(9)]
    for cell_permutation in block_permutations:
      self.add_cell_permutation(cell_permutation)

  def add_unique_constraint(self, cells: str|list):
    cells = cells.split() if isinstance(cells, str) else cells
    self.add_cell_permutation(gen_constrained_permutation(cells, self.d))

  def set_cells(self, cells):
    cells = cells.strip('\n')
    for r, row in zip(ROWS, cells.splitlines()):
      for c, v in zip(COLUMNS, row):
        if v.isdigit():
          self.d[f'{r}{c}'] = {int(v)}

  def iterate_once(self):
    changed = False
    self.print_sums()
    for permutation in self.cell_permutations:
      changed |= permutation.reduce(self.d)
    return changed

  def solve(self):
    while self.iterate_once():
      pass

  def print_board(self, pretty=True):
    # TODO: write a version that displays only known cells
    for i, c in enumerate(ROWS):
      if pretty and i % 3 == 0 and i > 0:
        print('---+---+---')
      joiner = '|' if pretty else ''
      cells = [cell_str(self.d[f'{c}{j}']) for j in COLUMNS]
      print(joiner.join(''.join(chunk) for chunk in chunks(cells, 3)))
  # The `*_sum` methods below are just for metrics and can be removed:

  def print_sums(self):
    print(self.d_sum(), self.perm_sum())

  def d_sum(self):
    return sum(len(vs) for vs in self.d.values())

  def perm_sum(self):
    return sum(len(perm.permutations) for perm in self.cell_permutations)


def main(sudoku, blocks=True, diagonals=False):
  """
  blocks: whether it's a "classic" sudoku, where numbers are unique in each block
  diagonals: whether the two diagonals must be unique
  """

  # time to add rows, cols, blocks:
  # Note: Complex permutations may be added later on if their initial complexity is too high at first
  sudoku.add_row_permutations()
  sudoku.add_col_permutations()
  if blocks:
    sudoku.add_block_permutations()
  if diagonals:
    sudoku.add_unique_constraint([f'{r}{c}' for r, c in zip(ROWS, COLUMNS)])
    sudoku.add_unique_constraint([f'{r}{c}' for r, c in zip(ROWS[::-1], COLUMNS)])

  sudoku.print_board(pretty=True)
  print()
  sudoku.solve()
  print()
  sudoku.print_board(pretty=True)


if __name__ == '__main__':
  s = Sudoku()

  s.set_cells("""
4.36721..
.72..3...
5.9..872.
...72..81
.........
65..34...
...3..2.9
......84.
....65..7
""")

  # Example for killer sudoku constraints:
  # cage_permutation_params = [
  #   ('A1 A2', 14), ('A3 A4', 16), ('A5 A6 B5 C4 C5 D4', 23), ('A7 A8 A9 B8 B9 C8 C9', 29),
  #   ('B1 B2 B3 B4 C1 D1', 34), ('B6 B7', 9),
  #   ('C2 C3 D2', 10), ('C6 D6', 6), ('C7 D7 D8 E8', 27),
  #   ('D3 E3', 10), ('D5 E4 E5 E6 F5', 30), ('D9 E9', 9),
  #   ('E1 F1', 11), ('E2 F2 F3 G3', 15), ('E7 F7', 7),
  #   ('F4 G4', 9), ('F6 G5 G6 H5 I4 I5', 27), ('F8 G7 G8', 16), ('F9 G9 H6 H7 H8 H9', 33),
  #   ('G1 G2 H1 H2 I1 I2 I3', 38),
  #   ('H3 H4', 11),
  #   ('I6 I7', 10), ('I8 I9', 11),
  #   ('H6 I6', 14), ('G3 H3', 7),
  #   ('F8 F9', 11),
  # ]
  # for cells, total in cage_permutation_params:
  #   sudoku.add_cell_permutation(gen_caged_permutation(cells, total))

  # TODO: Replace this with something that parses them out of a grid:
  # odd shaped blocks:
    # sudoku.add_unique_constraint('A1 A2 B1 C1 D1 E1 E2 F1 F2')
    # sudoku.add_unique_constraint('A3 B2 B3 B4 C2 D2 D3 E3 F3')
    # sudoku.add_unique_constraint('A4 A5 B5 B6 B7 C3 C4 C5 C7')
    # sudoku.add_unique_constraint('A6 A7 A8 A9 B8 B9 C9 D9 E9')
    # sudoku.add_unique_constraint('C6 C8 D6 D7 D8 E5 E6 F6 G6')
    # sudoku.add_unique_constraint('G1 G2 G3 H1 H2 H3 I1 I2 I3')
    # sudoku.add_unique_constraint('D4 D5 E4 F4 F5 G4 G5 H4 H5')
    # sudoku.add_unique_constraint('E7 E8 F7 F8 F9 G7 G9 H7 H9')
    # sudoku.add_unique_constraint('G8 H6 H8 I4 I5 I6 I7 I8 I9')

  main(s)
