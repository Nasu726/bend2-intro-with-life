import Base

# A stored zero and a missing key can both give Map.get's default zero.
# Map.has distinguishes the two cases.
def as_number(b: Bool) -> U32:
  match b:
    case True{}:
      1
    case False{}:
      0

def main() -> U32:
  m0 = Map.new(&2, U32)
  m1 = Map.set(&2, U32, m0, "wins", 0)
  (m2, has_wins) = Map.has(&2, U32, m1, "wins")
  (m3, has_losses) = Map.has(&2, U32, m2, "losses")
  (m4, wins) = Map.get(U32, 0, m3, "wins")
  (m5, losses) = Map.get(U32, 0, m4, "losses")
  (as_number(has_wins) + as_number(has_losses) + wins + losses : U32)
