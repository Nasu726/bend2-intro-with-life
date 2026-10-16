import Base
import ./life_core.bend as Life

# GPU dispatch syntax; a single sequential Life.step is NOT a
# cell-parallel GPU Life implementation or speedup guarantee.
def main() -> IO(Unit):
  b = Life.evolve!(4n, Life.glider())
  (_, v) = Life.at(b, 2, 3)
  IO.print(U32.show(v))
