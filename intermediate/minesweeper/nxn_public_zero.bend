# Public-information rule for N x N: every neighbor of an observed zero is safe.
# Input: indices of publicly revealed zero-clue cells ONLY, never mine truth.
# Output: safe neighbors grouped by observation; duplicates are allowed.
# The caller must validate observations and remove opened/flagged/duplicate cells.
# N=2..100; invalid zero indices are ignored. Not a complete CSP solver.
import Base
import ./nxn_neighbors.bend as Neighbors

def append(items: List<U32>, rest: List<U32>) -> List<U32>:
  match items:
    case Nil{}:
      rest
    case x <> xs:
      x <> append(xs, rest)

# Recurse on the first, structurally decreasing List argument.
def collect(zeros: List<U32>, +n: U32) -> List<U32>:
  match zeros:
    case Nil{}:
      Nil{}
    case z <> rest:
      append(Neighbors.neighbors(n, z), collect(rest, n))

def proven_safe(+n: U32, zeros: List<U32>) -> List<U32>:
  collect(zeros, n)

def count(items: List<U32>) -> U32:
  match items:
    case Nil{}:
      0
    case x <> xs:
      (1 + count(xs) : U32)

def main() -> U32:
  count(proven_safe(10, [0, 1]))
