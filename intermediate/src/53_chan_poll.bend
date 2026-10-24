import Base

# A zero-millisecond poll on an empty channel does not mean end-of-stream.
# Once a value is buffered, the next poll can return it immediately.
def poll_number(p: Poll<&1, &1, Maybe<&1, U32>, Unit>) -> U32:
  match p:
    case Wait{rest}:
      0
    case Ready{value}:
      match value:
        case Some{number}:
          number
        case None{}:
          100

def demonstrate(+chan: Chan(U32)) -> IO(Unit):
  do IO<Unit>:
    empty: Poll<&1, &1, Maybe<&1, U32>, Unit> <- Chan.try_recv(U32, chan, 0)
    Unit <- IO.print(U32.show(poll_number(empty)))
    sent: Result<&1, &1, U32, Unit> <- Chan.send(U32, chan, 9)
    full: Poll<&1, &1, Maybe<&1, U32>, Unit> <- Chan.try_recv(U32, chan, 0)
    Unit <- IO.print(U32.show(poll_number(full)))
    Chan.close(U32, chan)

def main() -> IO(Unit):
  do IO<Unit>:
    chan: Chan(U32) <- Chan.new(U32, 1)
    demonstrate(chan)
