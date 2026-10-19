import Base
import ./board_index.bend as Board

# The helper lives in a different file but works like a normal function.
def main() -> U32:
  Board.index(3, 2)  # column 3, row 2: position 11
