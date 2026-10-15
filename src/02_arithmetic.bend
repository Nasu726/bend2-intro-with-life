import Base

# A cell index in an 8x8 row-major board.
def index(+x: U32, y: U32) -> U32:
  (y * 8 + x : U32)

def main() -> U32:
  index(2, 3)
