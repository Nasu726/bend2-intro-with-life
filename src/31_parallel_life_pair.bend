import Base
import ./life_core.bend as Life

# Deconstruct only function parameters, not locally computed expressions.
def add_cells(a: Array<U32> & U32, b: Array<U32> & U32) -> U32:
  (a_board, a_value) = a
  (b_board, b_value) = b
  (a_value + b_value : U32)

# Independent simulations can run at the same time.
# This is batch parallelism, not cell-level parallelization.
def main() -> U32:
  left right = Life.evolve(4n, Life.glider()) Life.evolve(4n, Life.glider())
  add_cells(Life.at(left, 2, 3), Life.at(right, 2, 3))
