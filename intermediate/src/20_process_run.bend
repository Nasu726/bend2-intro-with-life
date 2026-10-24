import Base

# Launch a harmless OS program and examine its exit code.
def exit_status(value: U32 & (String & String)) -> U32:
  (code, outputs) = value
  code

def main() -> IO(Unit):
  do IO<Unit>:
    result: U32 & (String & String) <- IO.try(U32 & (String & String), Process.run("/usr/bin/true", Nil{}, "", 1024, 3000))
    IO.print(U32.show(exit_status(result)))
