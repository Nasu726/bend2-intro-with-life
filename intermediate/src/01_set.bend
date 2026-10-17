import Base

# Set contains String keys; membership returns the set as well.
def membership(r: Set() & Bool) -> U32:
  (again, exists) = r
  match exists:
    case True{}:
      1
    case False{}:
      0

def main() -> U32:
  s0 = Set.new()
  s1 = Set.add(s0, "2,3")
  membership(Set.has(s1, "2,3"))
