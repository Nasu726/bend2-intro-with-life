import Base

# A one-slot channel: send, receive and close.
# The channel handle is shared by these operations using +chan.

def received_value(result: Maybe<&1, U32>) -> U32:
  match result:
    case Some{value}:
      value
    case None{}:
      0

def exchange(+chan: Chan(U32)) -> IO(Unit):
  do IO<Unit>:
    outcome: Result<&1, &1, U32, Unit> <- Chan.send(U32, chan, 9)
    value: Maybe<&1, U32> <- Chan.recv(U32, chan)
    Unit <- Chan.close(U32, chan)
    IO.print(U32.show(received_value(value)))

def main() -> IO(Unit):
  do IO<Unit>:
    chan: Chan(U32) <- Chan.new(U32, 1)
    exchange(chan)
