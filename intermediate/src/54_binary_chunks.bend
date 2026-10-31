import Base

# This test fixture performs four bounded reads of a regular file.
# Three data reads are followed by a fourth read that must observe EOF
# for every tested regular file of length 0..5.
def after_fourth(result: File & Result<&1, &1, U32 & String, List<&2, U32>>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{bytes}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.print(Nat.show(List.length(&2, U32, bytes)))
    case Fail{error}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.die(Unit, 1, "fourth byte read failed")

def after_third(result: File & Result<&1, &1, U32 & String, List<&2, U32>>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{bytes}:
      do IO<Unit>:
        Unit <- IO.print(Nat.show(List.length(&2, U32, bytes)))
        fourth: File & Result<&1, &1, U32 & String, List<&2, U32>> <-
          File.read_bytes(file, 2)
        after_fourth(fourth)
    case Fail{error}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.die(Unit, 1, "third byte read failed")

def after_second(result: File & Result<&1, &1, U32 & String, List<&2, U32>>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{bytes}:
      do IO<Unit>:
        Unit <- IO.print(Nat.show(List.length(&2, U32, bytes)))
        third: File & Result<&1, &1, U32 & String, List<&2, U32>> <-
          File.read_bytes(file, 2)
        after_third(third)
    case Fail{error}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.die(Unit, 1, "second byte read failed")

def after_first(result: File & Result<&1, &1, U32 & String, List<&2, U32>>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{bytes}:
      do IO<Unit>:
        Unit <- IO.print(Nat.show(List.length(&2, U32, bytes)))
        second: File & Result<&1, &1, U32 & String, List<&2, U32>> <-
          File.read_bytes(file, 2)
        after_second(second)
    case Fail{error}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.die(Unit, 1, "first byte read failed")

def main() -> IO(Unit):
  do IO<Unit>:
    input: File <- IO.try(File, File.open("sample_bytes.bin", "r"))
    first: File & Result<&1, &1, U32 & String, List<&2, U32>> <-
      File.read_bytes(input, 2)
    after_first(first)
