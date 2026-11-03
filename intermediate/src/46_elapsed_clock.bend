import Base

# For elapsed time, not calendar dates.
def elapsed(first: Nat, last: Nat) -> Nat:
  Nat.sub(last, first)

def main() -> IO(Unit):
  do IO<Unit>:
    start: Nat <- IO.now()
    Unit <- IO.sleep(20)
    finish: Nat <- IO.now()
    IO.print(Nat.show(elapsed(start, finish)))
