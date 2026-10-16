import Base

# ~f is a compile-time function argument, unlike a closure.
def twice(~f: U32 -> U32, x: U32) -> U32:
  f(f(x))

def main() -> U32:
  twice(~(x => (x + 1 : U32)), 40)
