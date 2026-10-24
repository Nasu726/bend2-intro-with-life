import Base

# Sort three numbers in increasing order with the standard algorithm.
def or_zero(first: Maybe<&2, U32>) -> U32:
  match first:
    case Some{value}:
      value
    case None{}:
      0

def main() -> U32:
  sorted = List.sort(~U32, ~U32.is_le, [7, 2, 4])
  or_zero(List.head(&2, U32, sorted))
