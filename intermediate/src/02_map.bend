import Base

# Map.get returns a rebuilt map and its value.
def take_value(r: Map<&2, U32> & U32) -> U32:
  (again, value) = r
  value

def main() -> U32:
  m0 = Map.new(&2, U32)
  m1 = Map.set(&2, U32, m0, "wins", 7)
  take_value(Map.get(U32, 0, m1, "wins"))
