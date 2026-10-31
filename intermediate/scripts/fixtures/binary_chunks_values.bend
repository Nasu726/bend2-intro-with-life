import Base

# This test fixture checks each bounded read's length AND byte order.
# Six bounded reads distinguish EOF from an unobserved suffix.
# The fifth distinguishes 8 from 9 bytes, and the sixth distinguishes
# 10 from 11. Even six reads cannot distinguish 12 from 13 bytes
# when the first twelve bytes are identical.
# A two-byte chunk has an injective base-257 fingerprint when each
# byte is encoded as byte+1. The length is printed separately.
# Maximum value: 256*257+256 = 66048, safely within U32.
def digest_step(acc: U32, byte: U32) -> U32:
  (acc * 257 + byte + 1 : U32)

# A bounded 0..2-byte digest also determines the length:
# empty -> 0, one byte -> 1..256, two bytes -> 258..66048.
# Pass Booleans as arguments so match operates on variables.
def digest_length(is_empty: Bool, is_single: Bool) -> U32:
  match is_empty:
    case True{}:
      0
    case False{}:
      match is_single:
        case True{}:
          1
        case False{}:
          2

# The affine list is consumed ONCE by foldl. The U32 result is shared,
# rather than consuming the File.read_bytes list twice.
def report_chunk(bytes: List<&2, U32>) -> IO(Unit):
  +digest = List.foldl(~&2, ~U32, ~U32, ~digest_step, bytes, 0)
  +length = digest_length(U32.is_lt(digest, 1), U32.is_lt(digest, 257))
  do IO<Unit>:
    Unit <- IO.print(U32.show(length))
    IO.print(U32.show(digest))

def after_sixth(result: File & Result<&1, &1, U32 & String, List<&2, U32>>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{bytes}:
      do IO<Unit>:
        Unit <- File.close(file)
        report_chunk(bytes)
    case Fail{error}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.die(Unit, 1, "sixth byte read failed")

def after_fifth(result: File & Result<&1, &1, U32 & String, List<&2, U32>>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{bytes}:
      do IO<Unit>:
        Unit <- report_chunk(bytes)
        sixth: File & Result<&1, &1, U32 & String, List<&2, U32>> <-
          File.read_bytes(file, 2)
        after_sixth(sixth)
    case Fail{error}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.die(Unit, 1, "fifth byte read failed")

def after_fourth(result: File & Result<&1, &1, U32 & String, List<&2, U32>>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{bytes}:
      do IO<Unit>:
        Unit <- report_chunk(bytes)
        fifth: File & Result<&1, &1, U32 & String, List<&2, U32>> <-
          File.read_bytes(file, 2)
        after_fifth(fifth)
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
