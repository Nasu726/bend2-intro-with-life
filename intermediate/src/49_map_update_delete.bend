import Base

# Updating the same key replaces its value; deleting another key removes it.
def after_has(r: Map<&2, U32> & Bool) -> U32:
  (m, exists) = r
  match exists:
    case True{}:
      (U32.from_nat(Map.size(&2, U32, m)) + 1 : U32)
    case False{}:
      U32.from_nat(Map.size(&2, U32, m))

def after_get(r: Map<&2, U32> & U32) -> U32:
  (m, wins) = r
  (wins + after_has(Map.has(&2, U32, m, "games")) : U32)

def main() -> U32:
  m0 = Map.new(&2, U32)
  m1 = Map.set(&2, U32, m0, "wins", 7)
  m2 = Map.set(&2, U32, m1, "games", 10)
  m3 = Map.set(&2, U32, m2, "wins", 8)
  m4 = Map.del(&2, U32, m3, "games")
  after_get(Map.get(U32, 0, m4, "wins"))
