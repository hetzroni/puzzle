import itertools
import re
import time
from pathlib import Path

import colorama
from colorama import Fore

NEW_COLOR = Fore.LIGHTCYAN_EX

colorama.init(autoreset=True)


class IllegalSolutionError(Exception):
    pass


def size(puzzle):
    rows, cols = puzzle
    return len(rows), len(cols)


def board_size(board):
    return (len(board), len(board[0]))


def new_board(puzzle):
    height, width = size(puzzle)
    return [['n'] * width for _ in range(height)]


def get_row(board, i):
    return ''.join(board[i])


def get_col(board, i):
    return ''.join(row[i] for row in board)


def compile_reg_pair(nums):
    return (
        re.compile('^[wn]*?' + '[wn]+?'.join(['([bn]{{{}}})'.format(n) for n in nums]) + '[wn]*?$'),
        re.compile('^[wn]*' + '[wn]+'.join(['([bn]{{{}}})'.format(n) for n in nums]) + '[wn]*$'),
    )


def compile_regs(puzzle):
    rows, cols = puzzle
    row_regs = [compile_reg_pair(row) for row in rows]
    col_regs = [compile_reg_pair(col) for col in cols]
    return row_regs, col_regs


def get_diff(reg_pair, line):
    first_reg, last_reg = reg_pair
    first_matches = first_reg.match(line)
    last_matches = last_reg.match(line)
    if not first_matches or not last_matches:
        raise IllegalSolutionError()
    diff = ['n' for _ in line]
    for i in range(1, first_reg.groups + 1):
        diff[last_matches.start(i):first_matches.end(i)] = ['b'] * (first_matches.end(i) - last_matches.start(i))
    diff[:first_matches.start(1)] = ['w'] * first_matches.start(1)
    for i in range(1, first_reg.groups):
        diff[last_matches.end(i):first_matches.start(i + 1)] = ['w'] * (first_matches.start(i + 1) - last_matches.end(i))
    diff[last_matches.end(last_reg.groups):] = ['w'] * (len(diff) - last_matches.end(last_reg.groups))
    for i, bit in enumerate(line):  # return only NEW results about the line
        if bit != 'n':
            diff[i] = 'n'
    if 'n' in line and 'w' in line:  # 'n' means not done, so next step is relevant. lack of 'w' means line with clean slate, so next step isn't relevant.
        for i, bit in enumerate(line):
            if bit == 'n':
                for new_bit, opposite in ('wb', 'bw'):
                    if not first_reg.match(line[:i] + new_bit + line[i + 1:]):
                        diff[i] = opposite
                        break
    return diff


def apply_row(board, i, diff):
    for col, change in enumerate(diff):
        if change != 'n':
            board[i][col] = NEW_COLOR + change + Fore.RESET


def apply_col(board, i, diff):
    for row, change in enumerate(diff):
        if change != 'n':
            board[row][i] = NEW_COLOR + change + Fore.RESET


def apply_row_diffs(board, row_diffs):
    for i, diff in enumerate(row_diffs):
        apply_row(board, i, diff)

def apply_col_diffs(board, col_diffs):
    for i, diff in enumerate(col_diffs):
        apply_col(board, i, diff)


def no_diffs(diffs):
    return all(all(bit == 'n' for bit in diff) for diff in diffs)


def solve(puzzle):
    rows, cols = puzzle
    row_regs, col_regs = compile_regs(puzzle)
    height, width = size(puzzle)
    board = new_board(puzzle)
    first = True
    print_board(board, True)
    while True:
        row_diffs = [get_diff(row_regs[i], get_row(board, i)) for i in range(height)]
        apply_row_diffs(board, row_diffs)
        if no_diffs(row_diffs) and not first:
            break
        print_board(board, True)
        clean_board(board)
        col_diffs = [get_diff(col_regs[i], get_col(board, i)) for i in range(width)]
        apply_col_diffs(board, col_diffs)
        if no_diffs(col_diffs):
            break
        print_board(board, True)
        clean_board(board)
        first = False
    return board


def framed(st, size=None):
    lines = st.splitlines()
    if size is None:
        width = board_size(lines)[1]
    else:
        width = size[1]
    top = chr(9556) + chr(9552) * width + chr(9559)
    middle = '\n'.join(chr(9553) + line + chr(9553) for line in lines)
    bottom = chr(9562) + chr(9552) * width + chr(9565)
    return f'{top}\n{middle}\n{bottom}'


def print_board(board, go_back=None):
    height, width = board_size(board)
    print(framed('\n'.join(''.join(line).replace('w', '.').replace('b', chr(9608)).replace('n', ' ') for line in board), size=(height, width)))
    if go_back is not None:
        print(colorama.Cursor.UP(height + 3))
        time.sleep(0.1)


def clean_board(board):
    for row, col in itertools.product(*map(range, board_size(board))):
        board[row][col] = board[row][col][:6][-1]


def parse_board(board):
    height, width = board_size(board)
    rows = tuple(tuple(len(bs) for bs in re.findall('b+', row)) for row in board)
    cols = tuple(tuple(len(bs) for bs in re.findall('b+', get_col(board, i))) for i in range(len(board[0])))
    return (rows, cols)


def parse_puzzles(path):
    with open(path) as f:
        inputs = [[]]
        for line in f:
            line = line.strip()
            if line:
                inputs[-1].append(line)
            else:
                inputs.append([])
    if inputs[-1] == []:
        del inputs[-1]
    return [parse_board(board) for board in inputs]

def main():
    puzzles = parse_puzzles(Path(__file__).parent / 'nonogram-input.txt')
    for puzzle in puzzles:
        board = solve(puzzle)
        print_board(board)

if __name__ == '__main__':
    main()
