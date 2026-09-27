import re
from collections import deque
from dataclasses import dataclass

# Face rotation cycles (clockwise 90 degrees)
# Each cycle is a tuple of 4 indices that map to each other: a -> b -> c -> d -> a
# This means the piece at index a goes to b, b goes to c, c goes to d, d goes to a.
ROTATION_CYCLES = {
    'U': [
        # U face corners
        (0, 2, 8, 6),
        # U face edges
        (1, 5, 7, 3),
        # Adjacent top edges: L -> B -> R -> F -> L
        (36, 45, 9, 18),
        (37, 46, 10, 19),
        (38, 47, 11, 20)
    ],
    'D': [
        # D face corners
        (27, 29, 35, 33),
        # D face edges
        (28, 32, 34, 30),
        # Adjacent bottom edges: F -> R -> B -> L -> F
        (24, 15, 51, 42),
        (25, 16, 52, 43),
        (26, 17, 53, 44)
    ],
    'F': [
        # F face corners
        (18, 20, 26, 24),
        # F face edges
        (19, 23, 25, 21),
        # Adjacent edges: U bottom -> R left -> D top -> L right -> U bottom
        (6, 9, 29, 44),
        (7, 12, 28, 41),
        (8, 15, 27, 38)
    ],
    'B': [
        # B face corners
        (45, 47, 53, 51),
        # B face edges
        (46, 50, 52, 48),
        # Adjacent edges: U top -> L left -> D bottom -> R right -> U top
        (2, 36, 33, 17),
        (1, 39, 34, 14),
        (0, 42, 35, 11)
    ],
    'L': [
        # L face corners
        (36, 38, 44, 42),
        # L face edges
        (37, 41, 43, 39),
        # Adjacent edges: U left -> F left -> D left -> B right -> U left
        (0, 18, 27, 53),
        (3, 21, 30, 50),
        (6, 24, 33, 47)
    ],
    'R': [
        # R face corners
        (9, 11, 17, 15),
        # R face edges
        (10, 14, 16, 12),
        # Adjacent edges: U right -> B left -> D right -> F right -> U right
        (8, 45, 35, 26),
        (5, 48, 32, 23),
        (2, 51, 29, 20)
    ],
}

# Middle layer cycles matching U, F, R directions
MIDDLE_CYCLES = {
    'U': [(39, 48, 12, 21), (40, 49, 13, 22), (41, 50, 14, 23)],
    'F': [(3, 10, 32, 43), (4, 13, 31, 40), (5, 16, 30, 37)],
    'R': [(7, 46, 34, 25), (4, 49, 31, 22), (1, 52, 28, 19)]
}

# D, B, L are structurally opposite versions of U, F, R
MIDDLE_CYCLES['D'] = [cycle[::-1] for cycle in MIDDLE_CYCLES['U']]
MIDDLE_CYCLES['B'] = [cycle[::-1] for cycle in MIDDLE_CYCLES['F']]
MIDDLE_CYCLES['L'] = [cycle[::-1] for cycle in MIDDLE_CYCLES['R']]

# Add lower-case moves for wide turns (face + middle layer)
for face in list(ROTATION_CYCLES):
    ROTATION_CYCLES[face.lower()] = ROTATION_CYCLES[face] + MIDDLE_CYCLES[face]

# Add prime and double moves. This has to be done _after_ adding the wide moves.
for face in list(ROTATION_CYCLES):
    ROTATION_CYCLES[face + "'"] = [cycle[::-1] for cycle in ROTATION_CYCLES[face]]
    ROTATION_CYCLES[face + "2"] = [(cycle[0], cycle[2]) for cycle in ROTATION_CYCLES[face]] + \
                                  [(cycle[1], cycle[3]) for cycle in ROTATION_CYCLES[face]]

COLOR_MAP = {
    'W': 'white',
    'R': 'red',
    'G': 'green',
    'Y': 'yellow',
    'O': 'magenta',  # Using magenta as fallback for orange
    'B': 'blue'
}

MOVE_RE = re.compile(r"[a-zA-Z]['2]?")


@dataclass(frozen=True)
class Cube:
    """
    Represents a Rubik's Cube.
    The state is a string of length 54, representing the 6 faces.
    Faces are ordered: Up, Right, Front, Down, Left, Back.
    Each face has 9 squares, ordered row by row from top to bottom, left to right.
    
    Indices:
    U: 0-8
    R: 9-17
    F: 18-26
    D: 27-35
    L: 36-44
    B: 45-53
    """
    # Solved state: U=W(hite), R=R(ed), F=G(reen), D=Y(ellow), L=O(range), B=B(lue)
    state: str = "W"*9 + "R"*9 + "G"*9 + "Y"*9 + "O"*9 + "B"*9

    def __post_init__(self):
        if len(self.state) != 54:
            raise ValueError("State must be exactly 54 characters long.")

    def rotate(self, maneuver):
        """
        Rotates the cube according to the specified maneuver sequence.
        :param maneuver: A string of moves, e.g., "d'DBu'U", where each is a valid move letter
                         possibly followed by an apostrophe.
        :return: A new Cube object with the rotated state.
        """
        maneuver = maneuver.replace('’', "'").replace(" ", "")
        parsed_moves = MOVE_RE.findall(maneuver)

        state = list(self.state)

        for move in parsed_moves:
            if move not in ROTATION_CYCLES:
                raise ValueError(f"Invalid move notation: {move}")

            for cycle in ROTATION_CYCLES[move]:
                if len(cycle) == 4:
                    a, b, c, d = cycle
                    state[a], state[b], state[c], state[d] = state[d], state[a], state[b], state[c]
                elif len(cycle) == 2:
                    a, b = cycle  # (a, b) -> a swaps with b
                    state[a], state[b] = state[b], state[a]

        return Cube("".join(state))

    def solve(self, target) -> str:
        """
        Executes a BFS to find the shortest maneuver sequence from self to the target cube.
        :param target: The target Cube state.
        :return: A string of moves representing the maneuver.
        """
        solved = (lambda cube: cube == target) if isinstance(target, Cube) else target

        if solved(self):
            return ""

        queue = deque([(self, "")])
        visited = {self.state}

        while queue:
            current_cube, path = queue.popleft()

            for move in ROTATION_CYCLES:
                next_cube = current_cube.rotate(move)

                if solved(next_cube):
                    return path + move

                if next_cube.state not in visited:
                    visited.add(next_cube.state)
                    queue.append((next_cube, path + move))

        return None

    def print(self, color=False):
        try:
            from termcolor import colored
        except ImportError:
            colored = lambda text, color=None, on_color=None, attrs=None: text

        s_list = list(self.state)
        if color:
            s_list = [colored('■', COLOR_MAP.get(c, 'white')) for c in s_list]

        U = [s_list[i:i+3] for i in range(0, 9, 3)]
        R = [s_list[i:i+3] for i in range(9, 18, 3)]
        F = [s_list[i:i+3] for i in range(18, 27, 3)]
        D = [s_list[i:i+3] for i in range(27, 36, 3)]
        L = [s_list[i:i+3] for i in range(36, 45, 3)]
        B = [s_list[i:i+3] for i in range(45, 54, 3)]

        res = []
        for i in range(3):
            # 6 spaces of padding aligns U with F
            res.append("      " + " ".join(U[i]))
        for i in range(3):
            res.append(
                " ".join(L[i]) + " " +
                " ".join(F[i]) + " " +
                " ".join(R[i]) + " " +
                " ".join(B[i])
            )
        for i in range(3):
            res.append("      " + " ".join(D[i]))
            
        print("\n".join(res))


def is_zero(side):
    return side[4] != side[0] and side.count(side[0]) == 8


def is_one(side):
    return side[0] == side[1] == side[4] == side[6] == side[7] == side[8] and side[0] != side[2] and side[0] != side[3] and side[0] != side[5]


def is_two(side):
    return side[0] == side[1] == side[4] == side[7] == side[8] and side[0] != side[2] and side[0] != side[3] and side[0] != side[5] and side[0] != side[6]


def is_three(side):
    return side[3] != side[0] and side.count(side[0]) == 8


def is_four(side):
    return side[0] == side[2] == side[3] == side[4] == side[5] == side[8] and side[0] != side[1] and side[0] != side[6] and side[0] != side[7]


def is_five(side):
    return side[1] == side[2] == side[4] == side[6] == side[7] and side[1] != side[0] and side[1] != side[3] and side[1] != side[5] and side[1] != side[8]


def is_six(side):
    return side[0] != side[1] and side[0] != side[2] and side.count(side[0]) == 7


def is_seven(side):
    return side[0] == side[1] == side[2] == side[5] == side[8] and side.count(side[0]) == 5


def is_eight(side):
    return side[0] != side[3] and side[0] != side[5] and side.count(side[0]) == 7


def is_nine(side):
    return side[0] != side[6] and side[0] != side[7] and side.count(side[0]) == 7


def solved1(cube):
    return is_three(cube.state[0:9]) and is_three(cube.state[9:18])


def solved2(cube):
    return is_two(cube.state[0:9]) and is_four(cube.state[9:18])


def solved3(cube):
    return is_one(cube.state[0:9]) and is_five(cube.state[9:18])


def solved4(cube):
    return is_six(cube.state[0:9]) and is_two(cube.state[9:18])


def solved5(cube):
    return is_zero(cube.state[0:9]) and is_eight(cube.state[9:18])


def solved6(cube):
    return is_nine(cube.state[0:9]) and is_zero(cube.state[9:18])


def solved7(cube):
    return is_seven(cube.state[0:9]) and is_two(cube.state[9:18])


if __name__ == "__main__":
    c = Cube()
    for maneuver in [
        "Ubf'r'Uu'",
        "Bd'B'l'f",
        "UFuL'",
        "LU'F2lb",
        "DB'DBD'FRr'F'",
        "F'BL'RUD'R2B2Fb'dr2d2",
        "Ru'R'BD2",
    ]:
        c = c.rotate(maneuver)
        c.print(color=True)
        print('-' * 24)

    # solution = c.solve(solved7)
    # print('Solution:', solution)
    # c.rotate(solution).print(color=True)
