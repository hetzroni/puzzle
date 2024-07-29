import functools, itertools
from pprint import pprint as pp

# TODO: Support non 9x9 boards

# TODO: A helpful optimization that's essentially another (relatively trivial) sudoku solving trick:
# for each pair of cell permutations with more than 1 cell in common: filter on "co-permutations".
# This'll probably remove the need to add the `legal()` clause in `gen_caged_permutation`

# TODO: Some sudokus still may be onsolvable with this script. The next step would be to add backtracking.
# For backtracking it's probably better to track the guesses and their side-effects (responses from `reduce`), than to copy the whole board in each recursion.
# To do this, change `_reduce_d` to return _which_ cells changed instead of "whether a cell changed".
# Possibly return the cell's _before_ and _after_ values (or even just the _before_ value). Maybe also changes to the permutations?

VALUES = range(1, 10)
ROWS = 'ABCDEFGHI'
COLUMNS = VALUES

# A list of cells and all legal permutations for these cells. The list shrinks over time as information is analyzed until a single permutation remains
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
  return c1[0] == c2[0] or c1[1] == c2[1] or same_block(c1, c2)


def legal(cells, perm):
  for i, j in itertools.combinations(range(len(cells)), 2):
    if perm[i] == perm[j] and cant_be_same(cells[i], cells[j]):
      return False
  return True


def gen_caged_permutation(cells, total):
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
  # legal_values is a list of sets from which the values can be chosen
  legal_values = [d[cell] for cell in cells]
  # `indices` is a suggested order of assignment of the cells to find collisions as early as possible in the recursion
  indices = tuple(i for i, _ in sorted(enumerate(legal_values), key=lambda pair: len(pair[1])))
  permutations = aux_constrained_permutations(legal_values, set(), indices, [], [0] * len(indices))
  return CellPermutation(cells, permutations)


def cell_str(s):  # For print_board
  if len(s) == 1:
    return str(next(iter(s)))
  return '(' + ','.join(map(str, s)) + ')'


def chunks(l, size):  # For print_board
  return zip(*[iter(l)] * size)


class Sudoku:
  def __init__(self):
    # legal values for each cell:
    self.d = {f'{c}{i}': set(VALUES) for c, i in itertools.product(ROWS, COLUMNS)}
    self.cell_permutations = []
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


def main():
  sudoku = Sudoku()

  # if there are any known digits on the board, here'd be the time to add them

  # only for cage sudoku:
  # page 22:
  # cage_permutations = [gen_caged_permutation(*x) for x in (('A1', 1), ('A2 B1 B2', 9), ('A3 A4', 11), ('A5 A6 B4 B5', 15), ('A7 A8 A9', 23), ('B3', 9), ('B6 C6 C7 D7 E7', 28), ('B7', 2), ('B8 C8', 11), ('B9 C9 D9', 16), ('C1 C2 C3 C4', 21), ('C5 D5 D6 E5', 21), ('D1 D2 D3 D4', 10), ('D8 E8 E9', 21), ('E1', 3), ('E2 F1 F2', 24), ('E3 E4 F3', 19), ('E6 F6 G6 H6', 10), ('F4 F5 G4 G5', 30), ('F7 G7 G8 G9', 18), ('F8 F9', 3), ('G1 H1 I1', 21), ('G2 G3', 3), ('H2 H3 I2', 18), ('H4 H5 I5 I6', 24), ('H7 I7 I8 I9', 26), ('H8 H9', 4), ('I3 I4', 4))]
  # page 19:
  cage_permutation_params = [('A1 A2', 13), ('A3', 9), ('A4 B2 B3 B4', 20), ('A5 B5 C5', 14), ('A6 A7', 10), ('A8 A9 B8 B9', 17), ('B1 C1 D1 E1', 10), ('B6 C6 D6', 17), ('B7 C7', 5), ('C2 D2 E2', 10), ('C3 C4 D3', 12), ('C8 C9', 17), ('D4 D5 E5 E6', 23), ('D7 D8 D9 E8 E9', 25), ('E3 E4 F4 G4', 26), ('E7 F7 G7', 24), ('F1 G1 H1 I1', 30), ('F2 G2 G3', 15), ('F3', 5), ('F5 G5 G6 H6 H7', 24), ('F6', 3), ('F8 F9 G9', 6), ('G8 H8 H9', 21), ('H2 I2 I3 I4', 18), ('H3', 1), ('H4 H5', 5), ('I5 I6', 16), ('I7 I8', 3), ('I9', 6)]
  for cells, total in cage_permutation_params:
    sudoku.add_cell_permutation(gen_caged_permutation(cells, total))

  # time to add rows, cols, blocks:
  # Note: Complex permutations may be added later on if their initial complexity is too high at first
  sudoku.add_row_permutations()
  sudoku.add_col_permutations()
  sudoku.add_block_permutations()

  sudoku.solve()
  print()
  sudoku.print_board(pretty=False)


if __name__ == '__main__':
  main()
