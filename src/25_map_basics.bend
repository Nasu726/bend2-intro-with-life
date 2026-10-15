import Base

# A Map is a string-keyed associative structure with one owner.
def take_value(result: Map<&2, U32> & U32) -> U32:
  (dictionary, number) = result
  number

def main() -> U32:
  m = Map.new(&2, U32)
  m = Map.set(&2, U32, m, "glider-cells", 5)
  take_value(Map.get(U32, 0, m, "glider-cells"))
