import Base

# Set.add discards duplicates; Map.keys returns a list of String keys.
def main() -> Nat:
  s0 = Set.new()
  s1 = Set.add(s0, "0,0")
  s2 = Set.add(s1, "0,0")
  s3 = Set.add(s2, "1,1")
  s4 = Set.del(s3, "0,0")
  m0 = Map.new(&2, U32)
  m1 = Map.set(&2, U32, m0, "wins", 3)
  m2 = Map.set(&2, U32, m1, "games", 7)
  keys = Map.keys(&2, U32, m2)
  a = Set.size(s4)
  b = List.length(&2, String, keys)
  Nat.add(a, b)
