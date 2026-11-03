import Base

# Two sequential atomic additions. This is not a concurrency or GPU test.
# The four lines are: old cell 0, old target cell, final cell 0, final cell 1.
def show_second_cell(r: Array<U32> & U32) -> IO(Unit):
  (unused, value) = r
  IO.print(U32.show(value))

def show_first_cell(r: Array<U32> & U32) -> IO(Unit):
  (array, value) = r
  do IO<Unit>:
    Unit <- IO.print(U32.show(value))
    show_second_cell(Array.get(U32, array, 1))

def show_second_old(r: Array<U32> & U32) -> IO(Unit):
  (array, before) = r
  do IO<Unit>:
    Unit <- IO.print(U32.show(before))
    show_first_cell(Array.get(U32, array, 0))

def show_first_old(r: Array<U32> & U32) -> IO(Unit):
  (array, before) = r
  do IO<Unit>:
    Unit <- IO.print(U32.show(before))
    show_second_old(Array.atomic.add(array, 1, 7))

def main() -> IO(Unit):
  show_first_old(Array.atomic.add(Array.new(U32, 1n, 5), 0, 3))
