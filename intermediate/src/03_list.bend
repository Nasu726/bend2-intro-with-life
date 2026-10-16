import Base

# A linked list, and its length computed by the Base library.
def main() -> Nat:
  xs = 1 <> 2 <> 3 <> Nil{}
  List.length(&2, U32, xs)
