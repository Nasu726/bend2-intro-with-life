import Base

# The same IO main will run via Bend, native C, and generated JavaScript.
# No GPU or platform-specific operations are needed for this demonstration.
def main() -> IO(Unit):
  IO.print(U32.show((6 * 7 : U32)))
