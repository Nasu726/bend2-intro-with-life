import Base

# Launch a process, inspect the exit status, and handle startup errors.
# This example intentionally invokes a harmless program with no arguments.
def main() -> IO(Unit):
  do IO<Unit>:
    result: U32 & (String & String) <- IO.try(U32 & (String & String),
      Process.run("/usr/bin/true", Nil{}, "", 1024, 3000))
    (code, outputs) = result
    IO.print(U32.show(code))
