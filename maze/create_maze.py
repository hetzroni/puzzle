import copy
import random

import typer

TOP, RIGHT, BOTTOM, LEFT = 'trbl'
BLACK, RED, WHITE = 0, 0x0000ff, 0xffffff
PIXEL_SIZE = 10


class UnionFind:
  def __init__(self, cells):
    self.array = [-1] * len(cells)
    self.keys = {cell: i for i, cell in enumerate(cells)}

  def find(self, cell):
    idx = self.keys[cell]
    if self.array[idx] < 0:
      return idx
    while self.array[self.array[idx]] >= 0:
      temp = self.array[self.array[idx]], self.array[idx]
      self.array[idx], idx = temp
    return self.array[idx]

  # def same(self, cell1, cell2):
  #   return self.find(cell1) == self.find(cell2)

  def union(self, cell1, cell2) -> bool:
    """Unify the two groups. Return whether a union occurred. False if they were already together"""
    idx1 = self.find(cell1)
    idx2 = self.find(cell2)
    if idx1 == idx2:
      return False
    if self.array[idx1] < self.array[idx2]:
      idx2, idx1 = idx1, idx2
    self.array[idx2] += self.array[idx1]
    self.array[idx1] = idx2
    return True


class MazeGenerator:
  def __init__(self, height, width, start, end):
    self.height = height
    self.width = width
    self.halls = UnionFind([(i, j) for i in range(height) for j in range(width)])
    self.remaining_neighbors = list(self._gen_neighbor_pairs())
    self.holes = set()
    self.waypoints = [self._wall_to_pixel(wp) for wp in (start, end)]

  @staticmethod
  def from_image(path, start, end):
    from PIL import Image
    im = Image.open(path)

    pixels = list(im.getdata())
    width, height = im.size
    pixels = [pixels[i * width:(i + 1) * width] for i in range(height)]
    st = '\n'.join(''.join('#' if p else ' ' for p in line) for line in pixels)
    return MazeGenerator.from_string(st, start, end)

  @staticmethod
  def from_file(path, start, end):  # TODO: figure out a better way to specify start and end
    with open(path) as f:
      data = f.read()
    return MazeGenerator.from_string(data, start, end)

  @staticmethod
  def from_string(st, start, end):
    lines = st.splitlines()
    height, width = len(lines), len(lines[0])
    maze_gen = MazeGenerator(height, width, start, end)
    for i in range(height):
      for j in range(width):
        if lines[i][j] != ' ':
          if i < height - 1 and lines[i + 1][j] != ' ':
            maze_gen.connect((i, j), (i + 1, j))
          if j < width - 1 and lines[i][j + 1] != ' ':
            maze_gen.connect((i, j), (i, j + 1))
    return maze_gen

  def connect(self, cell1, cell2):
    pair = cell1, cell2
    self.remaining_neighbors.remove(pair)
    self.holes.add(pair)
    return self.halls.union(cell1, cell2)

  def generate(self):
    random.shuffle(self.remaining_neighbors)
    for pair in self.remaining_neighbors:
      cell1, cell2 = pair
      if self.halls.union(cell1, cell2):
        self.holes.add(pair)
    return self.get_board()

  def get_board(self):
    s, h, v, c = ' |-+'
    lines = [list(c + v * (self.width * 2 - 1) + c)]
    for i in range(self.height):
      # left-right pairs:
      lines.append(list(h + s + s.join(s if ((i, j), (i, j + 1)) in self.holes else h for j in range(self.width - 1)) + s + h))
      if i < self.height - 1:
        # up-down pairs:
        lines.append(list(c + c.join(s if ((i, j), (i + 1, j)) in self.holes else v for j in range(self.width)) + c))
    lines.append(list(c + v * (self.width * 2 - 1) + c))
    for wp in self.waypoints:
        lines[wp[0]][wp[1]] = s
    return Maze(lines, *self.waypoints)

  def _wall_to_pixel(self, wall):
    side, idx = wall
    pixel = (1 + idx * 2, 0 if side in (TOP, LEFT) else 2 * self.height if side == BOTTOM else 2 * self.width)
    return pixel if side in (LEFT, RIGHT) else pixel[::-1]

  def _gen_neighbor_pairs(self):
    for i in range(self.height):
      for j in range(self.width - 1):
        yield (i, j), (i, j + 1)
    for j in range(self.width):
      for i in range(self.height - 1):
        yield (i, j), (i + 1, j)


class Maze:
  def __init__(self, lines, start, end):
    self.lines = lines
    self.width = len(lines[0])
    self.height = len(lines)
    self.start = start
    self.end = end

  def solve(self) -> list:
    # nope = set() - unnecessary in mazes with no cycles
    current = [(self.start, list(self._get_neighbors(self.start)))]
    self.lines[self.start[0]][self.start[1]] = '@'
    while current:
      pixel, neighbors = current[-1]
      if not neighbors:
        self.lines[pixel[0]][pixel[1]] = ' '
        current.pop()
        continue
      next_pixel = neighbors.pop()
      if self.lines[next_pixel[0]][next_pixel[1]] == ' ':
        current.append((next_pixel, list(self._get_neighbors(next_pixel))))
        self.lines[next_pixel[0]][next_pixel[1]] = '@'
      if next_pixel == self.end:
        route = [pixel for pixel, neighbors in current]
        for pixel in route:
          self.lines[pixel[0]][pixel[1]] = ' '
        return route
    return []

  def _get_neighbors(self, pixel):
    if pixel[0] > 0:
      yield pixel[0] - 1, pixel[1]
    if pixel[0] < self.height - 1:
      yield pixel[0] + 1, pixel[1]
    if pixel[1] > 0:
      yield pixel[0], pixel[1] - 1
    if pixel[1] < self.width - 1:
      yield pixel[0], pixel[1] + 1

  def copy_board(self, route):
    lines = copy.deepcopy(self.lines)
    for cell in route:
      lines[cell[0]][cell[1]] = '@'
    return lines

  def print_board(self, route=(), pretty=False):
    lines = self.copy_board(route)
    if pretty:
      lines = [[' ' if cell == ' ' else '\u25AA' if cell == '@' else '\u2588' for cell in line] for line in lines]
    print('\n'.join(''.join(line) for line in lines))

  def produce_image(self, route=(), size=1, path=None):
    from PIL import Image  # in case pillow isn't installed, best not to import prematurely so that the module is still useable
    cell_colors = {' ': WHITE, '@': RED}  # default: BLACK
    lines = self.copy_board(route)
    im = Image.new(mode="RGB", size=(self.width, self.height))
    for i, line in enumerate(lines):
      for j, cell in enumerate(line):
        im.putpixel((j, i), cell_colors.get(cell, BLACK))
    if size > 1:
      im = im.resize((self.width * size, self.height * size), Image.Resampling.BOX)
    if path is not None:
      im.save(path)
    return im


def main(out_file=None, solved_out_file=None, solved: bool = False):
  maze_gen = MazeGenerator.from_image('AMIR.PNG', (TOP, 0), (RIGHT, 149))
  # maze_gen = MazeGenerator.from_file('input.txt', (TOP, 0), (RIGHT, 6))
  # maze_gen = MazeGenerator.from_string('####\n#   \n#   \n#   ', (TOP, 0), (RIGHT, 2))
  # maze_gen = MazeGenerator(height, width, (TOP, 0), (RIGHT, height - 1))
  maze = maze_gen.generate()
  route = maze.solve() if solved else []
  if out_file:
    maze.produce_image(path=out_file, size=PIXEL_SIZE)
  else:
    maze.print_board(route=route, pretty=True)
  if solved_out_file:
    route = route if route else maze.solve()
    maze.produce_image(route=route, path=solved_out_file, size=PIXEL_SIZE)


if __name__ == "__main__":
  typer.run(main)
