import Base

# Print raw clock readings around 0, 20 and 100 ms waits.
# The verifier checks elapsed differences, never an exact duration.
def main() -> IO(Unit):
  do IO<Unit>:
    a: Nat <- IO.now()
    Unit <- IO.sleep(0)
    b: Nat <- IO.now()
    Unit <- IO.print(Nat.show(a))
    Unit <- IO.print(Nat.show(b))
    c: Nat <- IO.now()
    Unit <- IO.sleep(20)
    d: Nat <- IO.now()
    Unit <- IO.print(Nat.show(c))
    Unit <- IO.print(Nat.show(d))
    e: Nat <- IO.now()
    Unit <- IO.sleep(100)
    f: Nat <- IO.now()
    Unit <- IO.print(Nat.show(e))
    IO.print(Nat.show(f))
