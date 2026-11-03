import Base

# Demonstrates connection success/failure, not a working echo server.
def handle(r: Result<&1, &1, U32 & String, Socket>) -> IO(Unit):
  match r:
    case Done{socket}:
      Socket.close(socket)
    case Fail{reason}:
      IO.print("No TCP listener at this address")

def main() -> IO(Unit):
  do IO<Unit>:
    outcome: Result<&1, &1, U32 & String, Socket> <- TCP.connect("127.0.0.1", 1)
    handle(outcome)
