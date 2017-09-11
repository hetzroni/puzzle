import copy
from colorama import init, Fore

init(autoreset=True)


BOARD_SIZE = 8
BOARD_AREA = BOARD_SIZE ** 2
COORDS = tuple((i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE))


def get_size(orient):
    return (len(orient), len(orient[0]))


def transpose(orient):
    return tuple(''.join(line) for line in zip(*orient))


class Piece:
    def __init__(self, template, symbol, color):
        orientations = {template, template[::-1]}
        non_mirrored = {template}
        for i in range(3):
            template = tuple(''.join(line) for line in zip(*template[::-1]))
            orientations.update({template, template[::-1]})
            if transpose(template) not in non_mirrored:
                non_mirrored.add(template)
        self.orientations = tuple(orientations)
        self.non_mirrored = tuple(non_mirrored)
        self.symbol = symbol
        self.color = color

    def get_options(self, board, coord, mirrored=True):
        options = []
        coord_y, coord_x = coord
        orientations = self.orientations if mirrored else self.non_mirrored
        for orient in orientations:
            size_y, size_x = get_size(orient)
            for y in range(max(coord_y - size_y + 1, 0), min(coord_y, BOARD_SIZE - size_y) + 1):
                for x in range(max(coord_x - size_x + 1, 0), min(coord_x, BOARD_SIZE - size_x) + 1):
                    if orient[coord_y - y][coord_x - x] == '@':  # covers requested square
                        if all(orient[sq_y][sq_x] == ' ' or board[y + sq_y][x + sq_x] == ' '
                               for sq_y in range(size_y) for sq_x in range(size_x)):
                            options.append(((y, x), orient))
        return options

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.symbol}>'


PIECES = (
    Piece(('@@',
           '@@'), 'O', Fore.CYAN),

    Piece(('@@@@@',), 'I', Fore.GREEN),

    Piece(('@@@@',
           '@   '), 'L', Fore.LIGHTBLACK_EX),

    Piece(('@@  ',
           ' @@@'), 'N', Fore.LIGHTCYAN_EX),

    Piece(('  @ ',
           '@@@@'), 'Y', Fore.LIGHTBLUE_EX),

    Piece(('@@@',
           ' @@'), 'P', Fore.LIGHTGREEN_EX),

    Piece(('@ @',
           '@@@'), 'U', Fore.LIGHTMAGENTA_EX),

    Piece((' @@',
           '@@ ',
           ' @ '), 'F', Fore.LIGHTYELLOW_EX),

    Piece(('@@@',
           ' @ ',
           ' @ '), 'T', Fore.LIGHTWHITE_EX),

    Piece(('@  ',
           '@  ',
           '@@@'), 'V', Fore.LIGHTRED_EX),

    Piece(('@  ',
           '@@ ',
           ' @@'), 'W', Fore.YELLOW),

    Piece((' @ ',
           '@@@',
           ' @ '), 'X', Fore.RED),

    Piece(('@@ ',
           ' @ ',
           ' @@'), 'Z', Fore.MAGENTA),
)


def place_piece(board, option, piece):
    (coord_y, coord_x), orient = option
    size_y, size_x = get_size(orient)
    for y in range(size_y):
        for x in range(size_x):
            if orient[y][x] == '@':
                board[coord_y + y][coord_x + x] = piece.color + chr(9608)


def remove_piece(board, option):
    (coord_y, coord_x), orient = option
    size_y, size_x = get_size(orient)
    for y in range(size_y):
        for x in range(size_x):
            if orient[y][x] == '@':
                board[coord_y + y][coord_x + x] = ' '


def new_board():
    return [[' '] * BOARD_SIZE for _ in range(BOARD_SIZE)]


def print_board(board):
    print('\n'.join(map(''.join, board)))


def backtrace(board, pieces, coord_id=0):
    #  step 1: find next empty square to fill
    while coord_id < BOARD_AREA:
        y, x = COORDS[coord_id]
        if board[y][x] == ' ':
            break
        coord_id += 1

    #  no empty square, meaning board is solved
    if coord_id == BOARD_AREA:
        import pdb; pdb.set_trace()
        return [copy.deepcopy(board)]

    solutions = []
    #  step 2: find piece to fill it
    for piece in pieces:
        options = piece.get_options(board, (y, x), mirrored=(coord_id != 0))
        if options:
            pieces.remove(piece)
            for option in options:
                place_piece(board, option, piece)
                solutions.extend(backtrace(board, pieces, coord_id + 1))
                remove_piece(board, option)
            pieces.add(piece)

    #  step 3: option 2: this configuration is unsolvable
    return solutions

def main():
    board = new_board()
    pieces = set(PIECES)
    square = next(piece for piece in PIECES if piece.symbol == 'O')
    plus = next(piece for piece in PIECES if piece.symbol == 'X')

    pieces -= {square}
    place_piece(board, ((3, 3), square.orientations[0]), square)

    backtrace(board, pieces)

    solutions = []
    import pdb; pdb.set_trace()
    for coord in ((0, 1), (0, 2), (1, 1)):
        place_piece(board, (coord, plus.orientations[0]), plus)
        solutions.extend(backtrace(board, pieces))
        remove_piece(board, (coord, plus.orientations[0]))

    import pdb; pdb.set_trace()
    pass


if __name__ == '__main__':
    main()
