import Base

# This test fixture checks each bounded read's length AND byte order.
# Three data reads are followed by a fourth read that must observe EOF
# for every tested regular file of length 0..5.
# A two-byte chunk has an injective base-257 fingerprint when each
# byte is encoded as byte+1. The length is printed separately.
# Maximum value: 256*257+256 = 66048, safely within U32.
def digest_step(acc: U32, byte: U32) -> U32:
  (acc * 257 + byte + 1 : U32)

def report_chunk(bytes: List<&2, U32>) -> IO(Unit):
  do IO<Unit>:
    Unit <- IO.print(Nat.show(List.length(&2, U32, bytes)))
    IO.print(U32.show(List.foldl(~&2, ~U32, ~U32, ~digest_step, bytes, 0)))

def after_fourth(result: File & Result<&1, &1, U32 & String, List<&2, U32>>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{bytes}:
      do IO<Unit>:
        Unit <- File.close(file)
        report_chunk(bytes)
    case Fail{error}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.die(Unit, 1, "fourth byte read failed")

def after_third(result: File & Result<&1, &1, U32 & String, List<&2, U32>>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{bytes}:
      do IO<Unit>:
        Unit <- report_chunk(bytes)
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
        Unit <- report_chunk(bytes)
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
        Unit <- report_chunk(bytes)
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
