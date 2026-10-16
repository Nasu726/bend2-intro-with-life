import Base

# A 4x4 Minesweeper board; mine positions are String keys "x,y".
# Out-of-bounds neighbor coordinates must NOT wrap around the board.

def member_bit(r: Set() & Bool) -> U32:
  (s, found) = r
  match found:
    case True{}:
      1
    case False{}:
      0

def mine_at(mines: Set(), x: U32, y: U32) -> U32:
  member_bit(Set.has(mines, U32.show(x) ++ "," ++ U32.show(y)))

def guarded(+mines: Set(), x: U32, y: U32, inside_x: Bool, inside_y: Bool) -> U32:
  match inside_x inside_y:
    case True{} True{}:
      mine_at(mines, x, y)
    case _ _:
      0

def adjacent(+mines: Set(), +x: U32, +y: U32) -> U32:
  +left = (x - 1 : U32)
  +right = (x + 1 : U32)
  +up = (y - 1 : U32)
  +down = (y + 1 : U32)
  a = guarded(mines, left, up, U32.is_lt(left, 4), U32.is_lt(up, 4))
  b = guarded(mines, x, up, U32.is_lt(x, 4), U32.is_lt(up, 4))
  c = guarded(mines, right, up, U32.is_lt(right, 4), U32.is_lt(up, 4))
  d = guarded(mines, left, y, U32.is_lt(left, 4), U32.is_lt(y, 4))
  e = guarded(mines, right, y, U32.is_lt(right, 4), U32.is_lt(y, 4))
  f = guarded(mines, left, down, U32.is_lt(left, 4), U32.is_lt(down, 4))
  g = guarded(mines, x, down, U32.is_lt(x, 4), U32.is_lt(down, 4))
  h = guarded(mines, right, down, U32.is_lt(right, 4), U32.is_lt(down, 4))
  (a + b + c + d + e + f + g + h : U32)

def main() -> U32:
  +mines = Set.add(Set.new(), "1,1")
  a = adjacent(mines, 0, 0)
  b = adjacent(mines, 2, 2)
  (a + b : U32)
