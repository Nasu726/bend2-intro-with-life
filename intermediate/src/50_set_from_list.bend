import Base

# Duplicated String keys are stored only once.
def main() -> Nat:
  s0 = Set.from_list(["0,0", "1,1", "0,0"])
  s1 = Set.del(s0, "3,3")
  keys = Set.to_list(s1)
  List.length(&2, String, keys)
