import Base

# A linked list, and its length computed by the Base library.
def main() -> Nat:
  xs = List.replicate(U32, 3n, 7)
  List.length(&2, U32, xs)
