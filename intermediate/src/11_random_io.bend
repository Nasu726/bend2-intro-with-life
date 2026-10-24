import Base

# The random-number effect may fail, hence the Result inside IO.
def main() -> IO(Unit):
  do IO<Unit>:
    random_value: U32 <- IO.try(U32, IO.random_u32())
    IO.print(U32.show(random_value))
