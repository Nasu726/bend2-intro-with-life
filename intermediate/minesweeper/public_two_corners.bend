import Base
import ./public_solver.bend as Solver

def show(result: Maybe<&2, U32>) -> U32:
  match result:
    case Some{bits}:
      bits
    case None{}:
      65536

def main() -> U32:
  show(Solver.provably_safe(Solver.Public{[
    Solver.Number{0, 0}, Solver.Number{15, 0}
  ]}))
