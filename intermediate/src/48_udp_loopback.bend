import Base

# A UDP datagram has a boundary. All traffic stays on localhost.
def received(pair: Socket & Result<&1, &1, U32 & String, String & U32 & String>)
             -> IO(Unit):
  (socket, result) = pair
  match result:
    case Done{(host, port, text)}:
      do IO<Unit>:
        Unit <- Socket.close(socket)
        IO.print(text)
    case Fail{(code, reason)}:
      do IO<Unit>:
        Unit <- Socket.close(socket)
        IO.die(Unit, code, reason)

def sent(pair: Socket & Result<&1, &1, (U32 & String) & String, Unit>)
         -> IO(Unit):
  (socket, result) = pair
  match result:
    case Done{value}:
      do IO<Unit>:
        incoming: Socket & Result<&1, &1, U32 & String, String & U32 & String> <-
          UDP.recv_from(socket, 64)
        received(incoming)
    case Fail{((code, reason), remaining)}:
      do IO<Unit>:
        Unit <- Socket.close(socket)
        IO.die(Unit, code, reason)

def run(bound: Socket & U32) -> IO(Unit):
  (socket, port) = bound
  do IO<Unit>:
    result: Socket & Result<&1, &1, (U32 & String) & String, Unit> <-
      UDP.send_to(socket, "127.0.0.1", port, "BEND-UDP")
    sent(result)

def choose(port: U32, result: Result<&1, &1, U32 & String, Socket>,
           fallback: IO(Socket & U32)) -> IO(Socket & U32):
  match result:
    case Done{socket}:
      IO.pure(Socket & U32, (socket, port))
    case Fail{reason}:
      fallback

def bind_any(tries: Nat, +port: U32) -> IO(Socket & U32):
  match tries:
    case 0n:
      IO.die(Socket & U32, 1, "No free localhost UDP port")
    case 1n+rest:
      fallback = bind_any(rest, (port + 1 : U32))
      do IO<Socket & U32>:
        result: Result<&1, &1, U32 & String, Socket> <-
          UDP.bind("127.0.0.1", port)
        choose(port, result, fallback)

def main() -> IO(Unit):
  do IO<Unit>:
    bound: Socket & U32 <- bind_any(24n, 22111)
    run(bound)
