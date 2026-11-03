# Enumerate non-toroidal neighbors for a future N x N zero flood.
# Valid sizes: 2..100. Invalid sizes/indices produce Nil, not Array padding.
# This is only a frontier primitive; it does NOT open squares or decide victory.
import Base
import ./nxn_geometry.bend as Geo

def include(valid: Bool, +n: U32, +u: U32, +v: U32, rest: List<U32>) -> List<U32>:
  match valid:
    case True{}:
      Geo.index(n, u, v) <> rest
    case False{}:
      rest

def add_offset(+n: U32, +x: U32, +y: U32, +pos: U32, rest: List<U32>) -> List<U32>:
  +dx = U32.mod(pos, 3)
  +dy = U32.div(pos, 3)
  +u = (x + dx - 1 : U32)
  +v = (y + dy - 1 : U32)
  include(Geo.neighbor(n, x, y, u, v), n, u, v, rest)

# Scan offsets 8 down to 0; prepend so the result is in ascending index order.
# Nat fuel makes the nine-position traversal structurally terminating.
def offsets(fuel: Nat, +n: U32, +x: U32, +y: U32, +pos: U32, rest: List<U32>) -> List<U32>:
  match fuel:
    case 0n:
      rest
    case 1n+k:
      offsets(k, n, x, y, (pos - 1 : U32), add_offset(n, x, y, pos, rest))

def if_valid(valid: Bool, +n: U32, +index: U32) -> List<U32>:
  match valid:
    case False{}:
      Nil{}
    case True{}:
      offsets(9n, n, U32.mod(index, n), U32.div(index, n), 8, Nil{})

def neighbors(+n: U32, +index: U32) -> List<U32>:
  if_valid(Geo.valid_index(n, index), n, index)

def count(items: List<U32>) -> U32:
  match items:
    case Nil{}:
      0
    case x <> xs:
      (1 + count(xs) : U32)

def main() -> U32:
  count(neighbors(10, 0))
