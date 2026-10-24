import Base

# Send and receive ONE byte on localhost, then close every acquired handle.
# It is intentionally not a complete message-framing protocol.
def received(listener: Listener, client: Socket,
             pair: Socket & Result<&1, &1, U32 & String, Maybe<&1, String>>)
             -> IO(Unit):
  (server, result) = pair
  match result:
    case Done{message}:
      do IO<Unit>:
        Unit <- Socket.close(server)
        Unit <- Socket.close(client)
        Unit <- Listener.close(listener)
        IO.print(Maybe.default(&1, String, message, "Peer closed"))
    case Fail{(code, reason)}:
      do IO<Unit>:
        Unit <- Socket.close(server)
        Unit <- Socket.close(client)
        Unit <- Listener.close(listener)
        IO.die(Unit, code, reason)

def sent(listener: Listener, server: Socket,
         pair: Socket & Result<&1, &1, (U32 & String) & List<&2, U32>, Unit>)
         -> IO(Unit):
  (client, result) = pair
  match result:
    case Done{value}:
      do IO<Unit>:
        incoming: Socket & Result<&1, &1, U32 & String, Maybe<&1, String>> <-
          TCP.recv(server, 1)
        received(listener, client, incoming)
    case Fail{((code, reason), remaining)}:
      do IO<Unit>:
        Unit <- Socket.close(server)
        Unit <- Socket.close(client)
        Unit <- Listener.close(listener)
        IO.die(Unit, code, reason)

def handle_accept(client: Socket,
             pair: Listener & Result<&1, &1, U32 & String, Socket>)
             -> IO(Unit):
  (listener, result) = pair
  match result:
    case Done{server}:
      do IO<Unit>:
        result: Socket & Result<&1, &1, (U32 & String) & List<&2, U32>, Unit> <-
          TCP.send(client, "B")
        sent(listener, server, result)
    case Fail{(code, reason)}:
      do IO<Unit>:
        Unit <- Socket.close(client)
        Unit <- Listener.close(listener)
        IO.die(Unit, code, reason)

def connected(listener: Listener,
              result: Result<&1, &1, U32 & String, Socket>) -> IO(Unit):
  match result:
    case Done{client}:
      do IO<Unit>:
        accepted: Listener & Result<&1, &1, U32 & String, Socket> <-
          TCP.accept(listener)
        handle_accept(client, accepted)
    case Fail{(code, reason)}:
      do IO<Unit>:
        Unit <- Listener.close(listener)
        IO.die(Unit, code, reason)

def run(bound: Listener & U32) -> IO(Unit):
  (listener, port) = bound
  do IO<Unit>:
    result: Result<&1, &1, U32 & String, Socket> <-
      TCP.connect("127.0.0.1", port)
    connected(listener, result)

# Retry several loopback ports rather than rely on one being free.
def choose(port: U32,
           outcome: Result<&1, &1, U32 & String, Listener>,
           next: IO(Listener & U32)) -> IO(Listener & U32):
  match outcome:
    case Done{listener}:
      IO.pure(Listener & U32, (listener, port))
    case Fail{reason}:
      next

def listen_any(tries: Nat, +port: U32) -> IO(Listener & U32):
  match tries:
    case 0n:
      IO.die(Listener & U32, 1, "No free localhost TCP port")
    case 1n+rest:
      fallback = listen_any(rest, (port + 1 : U32))
      do IO<Listener & U32>:
        result: Result<&1, &1, U32 & String, Listener> <-
          TCP.listen("127.0.0.1", port)
        choose(port, result, fallback)

def main() -> IO(Unit):
  do IO<Unit>:
    bound: Listener & U32 <- listen_any(24n, 22071)
    run(bound)
