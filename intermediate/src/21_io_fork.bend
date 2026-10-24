import Base

# fork returns a channel for the result; join waits and closes it.
def main() -> IO(Unit):
  do IO<Unit>:
    chan: Chan(U32) <- IO.fork(U32, IO.pure(U32, 7))
    value: U32 <- IO.join(U32, chan)
    IO.print(U32.show(value))
