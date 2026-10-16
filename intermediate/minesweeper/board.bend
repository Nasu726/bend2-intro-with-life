# Finite, non-wrapping 4x4 board coordinates and a single internal cell.
# This is NOT yet a complete board engine. The proof obligations are LAWS.bend.
import Base
import ./game.bend as Game

# The board model is deliberately explicit about hidden mine truth.
# Never pass Cell to the no-guess solver: it contains privileged information.
type Cell is Data:
  Cell{mine: Bool, square: Game.Square}

def mine_of(c: Cell) -> Bool:
  match c:
    case Cell{mine, square}:
      mine

def visible_of(c: Cell) -> Game.Square:
  match c:
    case Cell{mine, square}:
      square

def toggle(c: Cell) -> Cell:
  match c:
    case Cell{mine, square}:
      Cell{mine, Game.toggle_flag(square)}

# PRECONDITION: the caller has verified that the clicked cell is safe.
# Mine-hit/loss handling will be part of the later full-board engine.
def reveal(c: Cell, clue: U32) -> Cell:
  match c:
    case Cell{mine, square}:
      Cell{mine, Game.reveal_safe(square, clue)}

def in_bounds_checked(inside_x: Bool, y: U32) -> Bool:
  match inside_x:
    case False{}:
      False{}
    case True{}:
      U32.is_lt(y, 4)

def in_bounds(x: U32, y: U32) -> Bool:
  in_bounds_checked(U32.is_lt(x, 4), y)

# Legal coordinates are 0..3; only call this after bounding both endpoints.
def no_more_than_one(+a: U32, +b: U32) -> Bool:
  Bool.or(U32.is_eq(a, b),
    Bool.or(U32.is_eq((a + 1 : U32), b),
            U32.is_eq(a, (b + 1 : U32))))

def neighbor_to(inside_to: Bool, +x: U32, +y: U32, +u: U32, +v: U32) -> Bool:
  match inside_to:
    case False{}:
      False{}
    case True{}:
      Bool.and(
        Bool.and(no_more_than_one(x, u), no_more_than_one(y, v)),
        Bool.not(Bool.and(U32.is_eq(x, u), U32.is_eq(y, v))))

def neighbor_from(inside_from: Bool, +x: U32, +y: U32, +u: U32, +v: U32) -> Bool:
  match inside_from:
    case False{}:
      False{}
    case True{}:
      neighbor_to(in_bounds(u, v), x, y, u, v)

def neighbor(+x: U32, +y: U32, +u: U32, +v: U32) -> Bool:
  neighbor_from(in_bounds(x, y), x, y, u, v)
