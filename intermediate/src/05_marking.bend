import Base

# Keyed squares: Set operations are affine, so the new set is passed on.
def from_membership(r: Set() & Bool, key: String) -> Set():
  (s, present) = r
  match present:
    case True{}:
      Set.del(s, key)
    case False{}:
      Set.add(s, key)

def toggle_mark(s: Set(), +key: String) -> Set():
  from_membership(Set.has(s, key), key)

def main() -> Nat:
  s0 = Set.new()
  s1 = toggle_mark(s0, "2,3")
  s2 = toggle_mark(s1, "2,3")
  Set.size(s2)
