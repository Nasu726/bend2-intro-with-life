import Base

# IO.args returns a list including the executable or source path.
def main() -> IO(Unit):
  do IO<Unit>:
    xs: List<String> <- IO.args()
    IO.print(Nat.show(List.length(&1, String, xs)))
