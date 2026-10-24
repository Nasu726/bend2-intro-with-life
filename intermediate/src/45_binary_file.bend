import Base

# A binary file contains four bytes, not four printable characters.
def after_write(result: File & Result<&1, &1, U32 & String, Unit>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{value}:
      File.close(file)
    case Fail{error}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.die(Unit, 1, "Cannot write sample_bytes.bin")

def after_read(result: File & Result<&1, &1, U32 & String, List<&2, U32>>) -> IO(Nat):
  (file, status) = result
  match status:
    case Done{bytes}:
      do IO<Nat>:
        Unit <- File.close(file)
        return List.length(&2, U32, bytes)
    case Fail{error}:
      do IO<Nat>:
        Unit <- File.close(file)
        IO.die(Nat, 1, "Cannot read sample_bytes.bin")

def main() -> IO(Unit):
  do IO<Unit>:
    file: File <- IO.try(File, File.open("sample_bytes.bin", "w"))
    written: File & Result<&1, &1, U32 & String, Unit> <-
      File.write_bytes(file, [0, 10, 13, 255])
    Unit <- after_write(written)
    input: File <- IO.try(File, File.open("sample_bytes.bin", "r"))
    read: File & Result<&1, &1, U32 & String, List<&2, U32>> <-
      File.read_bytes(input, 16)
    count: Nat <- after_read(read)
    IO.print(Nat.show(count))
