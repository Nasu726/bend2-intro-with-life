import Base

# Mapping changes each value; folding combines all mapped values.
def plus_one(x: U32) -> U32:
  (x + 1 : U32)

def add(acc: U32, x: U32) -> U32:
  (acc + x : U32)

def main() -> U32:
  xs = {[1, 2, 3] : List<U32>}
  ys = List.map(~U32, ~U32, ~plus_one, xs)
  List.foldl(~&1, ~U32, ~U32, ~add, ys, 0)
