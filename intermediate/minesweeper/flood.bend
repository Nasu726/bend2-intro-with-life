# G-04: zero-connected safe reveal on the finite 4x4 board.
# This is a pure work-list traversal; every index is processed at most once.
# The work list may contain duplicates, but the seen bitset bounds processing.
import Base
import ./board.bend as Board
import ./board4.bend as Board4
import ./game.bend as Game

def include(yes: Bool, i: U32, rest: List<U32>) -> List<U32>:
  match yes:
    case True{}:
      i <> rest
    case False{}:
      rest

def maybe_neighbor(x: U32, y: U32, i: U32, rest: List<U32>) -> List<U32>:
  include(Board.neighbor(x, y, U32.mod(i, 4), U32.div(i, 4)), i, rest)

# The 16 explicit positions are intentional: the book's board is 4x4,
# and a standard list serves as the queue. No custom collection is needed.
def enqueue_all(+x: U32, +y: U32, rest: List<U32>) -> List<U32>:
  w0 = maybe_neighbor(x, y, 0, rest)
  w1 = maybe_neighbor(x, y, 1, w0)
  w2 = maybe_neighbor(x, y, 2, w1)
  w3 = maybe_neighbor(x, y, 3, w2)
  w4 = maybe_neighbor(x, y, 4, w3)
  w5 = maybe_neighbor(x, y, 5, w4)
  w6 = maybe_neighbor(x, y, 6, w5)
  w7 = maybe_neighbor(x, y, 7, w6)
  w8 = maybe_neighbor(x, y, 8, w7)
  w9 = maybe_neighbor(x, y, 9, w8)
  w10 = maybe_neighbor(x, y, 10, w9)
  w11 = maybe_neighbor(x, y, 11, w10)
  w12 = maybe_neighbor(x, y, 12, w11)
  w13 = maybe_neighbor(x, y, 13, w12)
  w14 = maybe_neighbor(x, y, 14, w13)
  w15 = maybe_neighbor(x, y, 15, w14)
  w15

def enqueue_neighbors(+index: U32, rest: List<U32>) -> List<U32>:
  enqueue_all(U32.mod(index, 4), U32.div(index, 4), rest)

# A zero cell adds all its valid neighbors. A numbered boundary does not.
def continue_after_reveal(zero: Bool, board: Board4.State, +mines: U32,
                          index: U32, work: List<U32>, seen: U32) -> Board4.State:
  match zero:
    case True{}:
      explore(board, mines, enqueue_neighbors(index, work), seen)
    case False{}:
      explore(board, mines, work, seen)

def read_and_reveal(+mines: U32, +index: U32, work: List<U32>,
                    seen: U32, read: Array<Game.Square> & Game.Square) -> Board4.State:
  (cells, square) = read
  match square:
    case Game.Hidden{}:
      clue = Board4.clue(mines, U32.mod(index, 4), U32.div(index, 4))
      updated = Array.set(Game.Square, cells, index, Game.Open{clue})
      continue_after_reveal(U32.is_eq(clue, 0),
        Board4.State{mines, updated}, mines, index, work, seen)
    case Game.Flag{}:
      explore(Board4.State{mines, cells}, mines, work, seen)
    case Game.Open{clue}:
      explore(Board4.State{mines, cells}, mines, work, seen)

def visit_unmined(board: Board4.State, +mines: U32, +index: U32,
                  work: List<U32>, seen: U32) -> Board4.State:
  match board:
    case Board4.State{internal_mines, cells}:
      read_and_reveal(mines, index, work, seen,
        Array.get(Game.Square, cells, index))

def visit_if_safe(mine: Bool, board: Board4.State, +mines: U32, index: U32,
                  work: List<U32>, seen: U32) -> Board4.State:
  match mine:
    case True{}:
      explore(board, mines, work, seen)
    case False{}:
      visit_unmined(board, mines, index, work, seen)

def visit_if_new(eligible: Bool, board: Board4.State, +mines: U32,
                 +index: U32, work: List<U32>, seen: U32) -> Board4.State:
  match eligible:
    case False{}:
      explore(board, mines, work, seen)
    case True{}:
      bit = U32.shln(1, U32.to_nat(index))
      visit_if_safe(Board4.bit_is_set(mines, bit), board, mines, index,
        work, U32.or(seen, bit))

def explore(board: Board4.State, +mines: U32, work: List<U32>,
            +seen: U32) -> Board4.State:
  match work:
    case Nil{}:
      board
    case index <> rest:
      bit = U32.shln(1, U32.to_nat(index))
      visit_if_new(Bool.and(U32.is_lt(index, 16),
                          Bool.not(Board4.bit_is_set(seen, bit))),
                   board, mines, index, rest, seen)

# The active Session verifies that the initial click was on a hidden safe
# square. This function independently skips mines and flags for safety.
def reveal(board: Board4.State, +mines: U32, index: U32) -> Board4.State:
  explore(board, mines, [index], 0)
