import Base

# WARNING: overwrites life-demo-output.txt in the working directory.
# Close the affine handle even when writing fails.
def finish(result: File & Result<&1, &1, U32 & String, Unit>) -> IO(Unit):
  match result:
    case (file, status):
      do IO<Unit>:
        File.close(file)
        IO.pass(Unit, status)
        IO.print("saved")

def main() -> IO(Unit):
  do IO<Unit>:
    file : File <- IO.try(File, File.open("life-demo-output.txt", "w"))
    result : File & Result<&1, &1, U32 & String, Unit> <- File.write(file, "generation=0")
    finish(result)
