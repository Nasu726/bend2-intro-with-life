import Base

# A completed result is Some; an expired wait is None.
# The delayed work may continue after the timeout.
def explain(result: Maybe<&1, U32>) -> IO(Unit):
  match result:
    case Some{value}:
      IO.print(U32.show(value))
    case None{}:
      IO.print("Timed out")

def main() -> IO(Unit):
  do IO<Unit>:
    result: Maybe<&1, U32> <- IO.within(U32, 1000, IO.pure(U32, 7))
    explain(result)
