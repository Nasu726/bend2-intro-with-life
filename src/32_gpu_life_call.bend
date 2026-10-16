import Base
import ./life_core.bend as Life

# The helper matches its parameter, not the result of a nested call.
def cell_from_result(r: Array<U32> & U32) -> U32:
  (board, value) = r
  value

# GPU dispatch syntax; a sequential Life.step is NOT a
# cell-parallel GPU Life implementation or a speedup guarantee.
def main() -> IO(Unit):
  board = Life.evolve!(4n, Life.glider())
  IO.print(U32.show(cell_from_result(Life.at(board, 2, 3))))
