import Base

# Concurrent effects are different from pure parallel CPU calls.
def delayed_message(number: U32) -> IO(String):
  do IO<String>:
    IO.sleep(10)
    return "result = " ++ U32.show(number)

def main() -> IO(Unit):
  do IO<Unit>:
    channel : Chan(String) <- IO.fork(String, delayed_message(42))
    IO.print("waiting for another computation")
    message : String <- IO.join(String, channel)
    IO.print(message)
