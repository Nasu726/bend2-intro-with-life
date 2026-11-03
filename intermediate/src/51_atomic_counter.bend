import Base

# Array.atomic.add returns the updated array AND the previous value.
# This example is sequential: it does not test parallel contention.
def read_after(r: Array<U32> & U32) -> IO(Unit):
  (unused, after) = r
  IO.print(U32.show(after))

def show_values(r: Array<U32> & U32) -> IO(Unit):
  (array, before) = r
  do IO<Unit>:
    Unit <- IO.print(U32.show(before))
    read_after(Array.get(U32, array, 0))

def main() -> IO(Unit):
  show_values(Array.atomic.add(Array.new(U32, 1n, 5), 0, 3))
