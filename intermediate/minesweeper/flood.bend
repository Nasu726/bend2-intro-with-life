# G-04: zero cascade for the fixed 4x4 board, without unsafe recursion.
# A Nat fuel argument guarantees termination even when the work list grows.
# At most 16 zero squares enqueue 8 neighbors each: 1+16*8 = 129 jobs.
import Base
import ./board.bend as Board
import ./board4.bend as Board4
import ./game.bend as Game

type Task is Type:
  Task{board: Board4.State, mines: U32, work: List<U32>, seen: U32}

def include(yes: Bool, i: U32, rest: List<U32>) -> List<U32>:
  match yes:
    case True{}:
      i <> rest
    case False{}:
      rest

def maybe_neighbor(x: U32, y: U32, +i: U32, rest: List<U32>) -> List<U32>:
  include(Board.neighbor(x, y, U32.mod(i, 4), U32.div(i, 4)), i, rest)

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

def choose_queue(zero: Bool, index: U32, rest: List<U32>) -> List<U32>:
  match zero:
    case True{}:
      enqueue_neighbors(index, rest)
    case False{}:
      rest

def open_hidden(+mines: U32, +index: U32, +clue: U32,
                cells: Array<Game.Square>, work: List<U32>, seen: U32) -> Task:
  updated = Array.set(Game.Square, cells, index, Game.Open{clue})
  Task{Board4.State{mines, updated}, mines,
       choose_queue(U32.is_eq(clue, 0), index, work), seen}

def read_one(+mines: U32, +index: U32, work: List<U32>,
             seen: U32, pair: Array<Game.Square> & Game.Square) -> Task:
  (cells, square) = pair
  match square:
    case Game.Hidden{}:
      open_hidden(mines, index,
        Board4.clue(mines, U32.mod(index, 4), U32.div(index, 4)),
        cells, work, seen)
    case Game.Flag{}:
      Task{Board4.State{mines, cells}, mines, work, seen}
    case Game.Open{clue}:
      Task{Board4.State{mines, cells}, mines, work, seen}

def visit_unmined(board: Board4.State, +mines: U32, +index: U32,
                  rest: List<U32>, seen: U32) -> Task:
  match board:
    case Board4.State{internal_mines, cells}:
      read_one(mines, index, rest, seen, Array.get(Game.Square, cells, index))

def visit_if_safe(is_mine: Bool, board: Board4.State, +mines: U32,
                  index: U32, rest: List<U32>, seen: U32) -> Task:
  match is_mine:
    case True{}:
      Task{board, mines, rest, seen}
    case False{}:
      visit_unmined(board, mines, index, rest, seen)

def visit_if_new(valid: Bool, board: Board4.State, +mines: U32,
                 +index: U32, rest: List<U32>, seen: U32) -> Task:
  match valid:
    case False{}:
      Task{board, mines, rest, seen}
    case True{}:
      visit_if_safe(Board4.bit_is_set(mines, U32.shln(1, U32.to_nat(index))),
                    board, mines, index, rest,
                    U32.or(seen, U32.shln(1, U32.to_nat(index))))

def step(board: Board4.State, +mines: U32, +index: U32,
         rest: List<U32>, +seen: U32) -> Task:
  visit_if_new(
    Bool.and(U32.is_lt(index, 16),
             Bool.not(Board4.bit_is_set(seen, U32.shln(1, U32.to_nat(index))))),
    board, mines, index, rest, seen)

# One recursive function only; the first argument strictly decreases.
# All other helpers are nonrecursive task transformations.
def explore(fuel: Nat, task: Task) -> Board4.State:
  match fuel:
    case 0n:
      match task:
        case Task{board, mines, work, seen}:
          board
    case 1n+remaining:
      match task:
        case Task{board, mines, work, seen}:
          match work:
            case Nil{}:
              board
            case index <> rest:
              explore(remaining, step(board, mines, index, rest, seen))

def reveal(board: Board4.State, mines: U32, index: U32) -> Board4.State:
  explore(129n, Task{board, mines, [index], 0})
