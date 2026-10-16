import Base
import ./board_index.bend as Board

# The helper lives in a different file but works like a normal function.
def main() -> U32:
  Board.index(2, 3)
