import Base

# File operations return the handle so it can be used or closed exactly once.
# Run in a writable directory. This writes "sample_board.txt".

def close_after_write(r: File & Result<&1, &1, U32 & String, Unit>) -> IO(Unit):
  (file, status) = r
  match status:
    case Done{value}:
      File.close(file)
    case Fail{error}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.die(Unit, 1, "Could not save sample_board.txt")

def main() -> IO(Unit):
  do IO<Unit>:
    file: File <- IO.try(File, File.open("sample_board.txt", "w"))
    written: File & Result<&1, &1, U32 & String, Unit> <- File.write(file, "board-size=4\nmines=1,1\n")
    close_after_write(written)
