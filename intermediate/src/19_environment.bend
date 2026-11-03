import Base

# The environment may not contain the requested name.
def env_length(value: Result<&1, &1, U32 & String, String>) -> Nat:
  match value:
    case Done{s}:
      String.length(s)
    case Fail{problem}:
      0n

def main() -> IO(Unit):
  do IO<Unit>:
    result: Result<&1, &1, U32 & String, String> <- IO.get_env("PATH")
    IO.print(Nat.show(env_length(result)))
