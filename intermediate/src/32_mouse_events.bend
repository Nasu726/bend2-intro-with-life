import Base
import ./23_cell_hit_test.bend as Grid

# Turn a mouse press into an 8x8 board index.
# This example intentionally does not assign meanings to button numbers.
def cell_on_press(down: Bool, x: U32, y: U32) -> Maybe<&2, U32>:
  match down:
    case True{}:
      Grid.pixel_to_cell(x, y)
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
