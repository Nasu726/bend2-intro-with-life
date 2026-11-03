import Base

# Map.has returns both the map and the membership bit.
# Two small helpers thread the affine map through successive lookups.
def as_number(b: Bool) -> U32:
  match b:
    case True{}:
      1
    case False{}:
      0

def count_second(r: Map<&2, U32> & Bool, first: Bool) -> U32:
  (m, second) = r
  (as_number(first) + as_number(second) : U32)

def count_first(r: Map<&2, U32> & Bool) -> U32:
  (m, first) = r
  count_second(Map.has(&2, U32, m, "losses"), first)

def main() -> U32:
  m0 = Map.new(&2, U32)
  m1 = Map.set(&2, U32, m0, "wins", 0)
  count_first(Map.has(&2, U32, m1, "wins"))
