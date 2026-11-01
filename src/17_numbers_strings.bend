import Base

# Parenthesized operators carry a type annotation.
def next_index(+i: U32) -> U32:
  ((i + 1 : U32) % 64 : U32)

def main() -> String:
  "next index = " ++ U32.show(next_index(63))
