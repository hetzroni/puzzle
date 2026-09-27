import heapq

SIZE = 9


class TopSpin:
    """Represents the TopSpin game state and solver.

    The game consists of numbers 1 to 20 on a circular strip. The only action
    is 'spin', which reverses a window of 4 consecutive numbers.
    """

    def __init__(self, state=None):
        """Initializes the game state.

        Args:
            state: A tuple of 20 integers representing the current state. If
              None, the game starts in the solved state (1, 2, ..., 20).
        """
        if state is None:
            self.state = tuple(range(1, SIZE + 1))
        else:
            assert len(state) == SIZE, f"State must contain exactly {SIZE} elements."
            self.state = tuple(state)
        self.n = SIZE
        self.k = 4

    def __lt__(self, other):
        return self.state < other.state

    def spin(self, index):
        """Returns a new TopSpin instance with the 4 numbers starting at index reversed.

        Args:
            index: The starting index of the window to reverse (0-19).
        """
        lst = list(self.state)
        idx = [(index + i) % self.n for i in range(self.k)]
        vals = [lst[i] for i in idx]
        for i, val in zip(idx, reversed(vals)):
            lst[i] = val
        return TopSpin(lst)

    def is_solved(self, state):
        """Checks if the state is ordered (any cyclic shift of 1..20)."""
        idx = state.index(1)
        for i in range(self.n):
            if state[(idx + i) % self.n] != i + 1:
                return False
        return True

    @staticmethod
    def _is_even(state):
        """Checks if the state is an even permutation."""
        inv = 0
        for i in range(len(state)):
            for j in range(i + 1, len(state)):
                if state[i] > state[j]:
                    inv += 1
        return inv % 2 == 0

    def h_score(self):
        """Heuristic: min circular distance to any ordered state, divided by 8."""
        min_total_dist = float("inf")
        for shift in range(self.n):
            dist = 0
            for i, val in enumerate(self.state):
                target_pos = (val - 1 + shift) % self.n
                d = abs(i - target_pos)
                d = min(d, self.n - d)
                dist += d
            min_total_dist = min(min_total_dist, dist)
        return min_total_dist / 8.0

    def solve(self):
        """Finds a sequence of spin moves to reach a solved state.

        Returns:
            A list of indices representing the sequence of moves.
        """
        if self.is_solved(self.state):
            return []

        # Parity optimization for odd N
        if self.n % 2 != 0 and not self._is_even(self.state):
            return None

        # A* Search
        pq = []
        h = self.h_score()
        heapq.heappush(pq, (h, self, []))

        visited = {self.state: 0}

        while pq:
            f, current, path = heapq.heappop(pq)

            if self.is_solved(current.state):
                return path

            g = len(path)
            if g > visited.get(current.state, float("inf")):
                continue

            for i in range(self.n):
                # Apply spin using the spin method
                next_instance = current.spin(i)
                next_state = next_instance.state

                next_g = g + 1
                if next_g < visited.get(next_state, float("inf")):
                    visited[next_state] = next_g
                    h_score = next_instance.h_score()
                    heapq.heappush(
                        pq,
                        (
                            next_g + h_score,
                            next_instance,
                            path + [current.state[i]],
                        ),
                    )

        return None


if __name__ == "__main__":
    # Example usage
    game = TopSpin(list(range(1, SIZE - 1)) + [SIZE, SIZE - 1])
    
    print("Initial state:", game.state)

    # Scramble with some moves
    # scrambled = game.spin(2).spin(5).spin(10)
    # print("Scrambled state:", scrambled.state)

    print("Solving...")
    moves = game.solve()
    print("Moves to solve:", moves)

    # Verify
    if moves is not None:
        curr = game
        for m in moves:
            curr = curr.spin(curr.state.index(m))
        print("Final state:", curr.state)
        print("Is solved?", curr.is_solved(curr.state))
    else:
        print("No solution found!")
