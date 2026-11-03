import Base

# 8x8 example: x=column and y=row (0..7 after pixel bounds check).
def index(x: U32, y: U32) -> U32:
  (y * 8 + x : U32)

# Translate a mouse position to the index of an 8x8 grid of 32-pixel squares.
# Invalid positions return None rather than selecting an unrelated square.

def cell_if_valid(x: U32, y: U32, valid: Bool) -> Maybe<&2, U32>:
  match valid:
    case False{}:
      None{}
    case True{}:
      Some{index(U32.div(x, 32), U32.div(y, 32))}

def pixel_to_cell(+x: U32, +y: U32) -> Maybe<&2, U32>:
  cell_if_valid(x, y, Bool.and(U32.is_lt(x, 256), U32.is_lt(y, 256)))

def cell_or_zero(result: Maybe<&2, U32>) -> U32:
  match result:
    case Some{cell}:
      cell
    case None{}:
      0

def main() -> U32:
  a = cell_or_zero(pixel_to_cell(64, 32))
  b = cell_or_zero(pixel_to_cell(256, 32))
  (a + b : U32)
