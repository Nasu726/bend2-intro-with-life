import Base

# 8x8 example: x=column and y=row (0..7 after pixel bounds check).
def index(x: U32, y: U32) -> U32:
  (y * 8 + x : U32)

# This example is self-contained. We reuse the same 8x8 coordinate rule
# introduced in 23_cell_hit_test.bend without requiring a numbered import.
def cell_if_valid(valid: Bool, x: U32, y: U32) -> Maybe<&2, U32>:
  match valid:
    case True{}:
      Some{index(U32.div(x, 32), U32.div(y, 32))}
    case False{}:
      None{}

def pixel_to_cell(+x: U32, +y: U32) -> Maybe<&2, U32>:
  cell_if_valid(Bool.and(U32.is_lt(x, 256), U32.is_lt(y, 256)), x, y)

# Turn a mouse press into an 8x8 board index.
# We deliberately leave button-number interpretation for the GUI chapter.
def cell_on_press(down: Bool, x: U32, y: U32) -> Maybe<&2, U32>:
  match down:
    case True{}:
      pixel_to_cell(x, y)
    case False{}:
      None{}

def event_cell(event: Event) -> Maybe<&2, U32>:
  match event:
    case Mouse{x, y, button, down}:
      cell_on_press(down, x, y)
    case _:
      None{}

def index_or_zero(r: Maybe<&2, U32>) -> U32:
  match r:
    case Some{index}:
      index
    case None{}:
      0

def main() -> U32:
  inside = index_or_zero(event_cell(Mouse{64, 32, 0, True{}}))
  outside = index_or_zero(event_cell(Mouse{256, 0, 0, True{}}))
  (inside + outside : U32)
