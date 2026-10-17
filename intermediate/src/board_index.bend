import Base

# A 4x4 board's row and column become a one-dimensional index.
def index(row: U32, col: U32) -> U32:
  (row * 4 + col : U32)
