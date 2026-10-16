import Base

# Reads the file written by 12_file_write.bend.
# Every branch closes the affine File handle.

def close_after_read(r: File & Result<&1, &1, U32 & String, String>) -> IO(String):
  (file, status) = r
  match status:
    case Done{contents}:
      do IO<String>:
        Unit <- File.close(file)
        return contents
    case Fail{error}:
      do IO<String>:
        Unit <- File.close(file)
        IO.die(String, 1, "Could not read sample_board.txt")

def main() -> IO(Unit):
  do IO<Unit>:
    file: File <- IO.try(File, File.open("sample_board.txt", "r"))
    result: File & Result<&1, &1, U32 & String, String> <- File.read(file, 4096)
    contents: String <- close_after_read(result)
    IO.print(contents)
