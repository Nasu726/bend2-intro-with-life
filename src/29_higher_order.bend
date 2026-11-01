import Base

# Passing a function as an input.
def apply(f: U32 -> U32, x: U32) -> U32:
  f(x)

def main() -> U32:
  apply(x => (x + 2 : U32), 40)
