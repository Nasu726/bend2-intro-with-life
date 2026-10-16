import Base
import ./life_core.bend as Life

# Two independent simulations may run at the same time.
# This is batch parallelism; each Life.step remains sequential.
def main() -> U32:
  a b = Life.evolve(4n, Life.glider()) Life.evolve(4n, Life.glider())
  ra = Life.at(a, 2, 3)
  rb = Life.at(b, 2, 3)
  (a2, va) = ra
  (b2, vb) = rb
  (va + vb : U32)
