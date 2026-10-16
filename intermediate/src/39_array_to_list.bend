import Base

# Convert the whole array to a list only when a list operation is useful.
def add(acc: U32, x: U32) -> U32:
  (acc + x : U32)

def main() -> U32:
  xs = Array.new(U32, 2n, 1)
  ys = Array.set(U32, xs, 0, 7)
  items = Array.to_list(~U32, ys)
  List.foldl(~&1, ~U32, ~U32, ~add, items, 0)
