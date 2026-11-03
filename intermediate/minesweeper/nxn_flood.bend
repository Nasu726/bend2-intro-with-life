# Bounded zero-cascade for an active N x N session (2 <= n <= 100).
# This module deliberately does not relocate first clicks or decide victory.
# A hidden zero enqueues its real non-wrapping neighbors. Flags and mines
# are never opened by the cascade. Existing Open squares are not re-expanded.
import Base
import ./game.bend as Game
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words
import ./nxn_neighbors.bend as Neighbors
import ./nxn_step.bend as Step

type Task is Type:
  Task{session: Step.Session, pending: List<U32>}

def prepend(items: List<U32>, rest: List<U32>) -> List<U32>:
  match items:
    case Nil{}:
      rest
    case index <> tail:
      index <> prepend(tail, rest)

def enqueue_if_zero(zero: Bool, +n: U32, +index: U32, rest: List<U32>) -> List<U32>:
  match zero:
    case True{}:
      prepend(Neighbors.neighbors(n, index), rest)
    case False{}:
      rest

def queue_after_open(square: Game.Square, +n: U32, +index: U32, rest: List<U32>) -> List<U32>:
  match square:
    case Game.Open{clue}:
      enqueue_if_zero(U32.is_eq(clue, 0), n, index, rest)
    case Game.Hidden{}:
      rest
    case Game.Flag{}:
      rest

# Only called immediately after opening a previously Hidden square.
def after_read(+n: U32, mines: Words.MineWords, phase: Step.Phase,
               +index: U32, rest: List<U32>,
               read: Array<Game.Square> & Game.Square) -> Task:
  (cells, square) = read
  Task{Step.Session{n, mines, cells, phase},
       queue_after_open(square, n, index, rest)}

def after_click(session: Step.Session, +index: U32, rest: List<U32>) -> Task:
  match session:
    case Step.Session{+n, mines, cells, phase}:
      after_read(n, mines, phase, index, rest,
                 Array.get(Game.Square, cells, index))

def before_read(+n: U32, mines: Words.MineWords, +index: U32,
                rest: List<U32>,
                read: Array<Game.Square> & Game.Square) -> Task:
  (cells, square) = read
  match square:
    case Game.Hidden{}:
      after_click(Step.click(Step.Session{n, mines, cells, Step.Playing{}},
                             index), index, rest)
    case Game.Flag{}:
      Task{Step.Session{n, mines, cells, Step.Playing{}}, rest}
    case Game.Open{clue}:
      Task{Step.Session{n, mines, cells, Step.Playing{}}, rest}

def active_if_valid(valid: Bool, +n: U32, mines: Words.MineWords,
                    cells: Array<Game.Square>, +index: U32,
                    rest: List<U32>) -> Task:
  match valid:
    case False{}:
      Task{Step.Session{n, mines, cells, Step.Playing{}}, rest}
    case True{}:
      before_read(n, mines, index, rest,
                  Array.get(Game.Square, cells, index))

def process(session: Step.Session, +index: U32, rest: List<U32>) -> Task:
  match session:
    case Step.Session{+n, mines, cells, phase}:
      match phase:
        case Step.Lost{}:
          Task{Step.Session{n, mines, cells, Step.Lost{}}, Nil{}}
        case Step.Playing{}:
          active_if_valid(Geo.valid_index(n, index), n, mines, cells,
                          index, rest)

# Every Hidden zero is opened at most once, and enqueues at most eight
# neighbors. Therefore at most 1 + 8*n*n jobs can be generated.
# The Nat fuel strictly decreases, even if duplicate jobs are enqueued.
def explore(fuel: Nat, task: Task) -> Step.Session:
  match fuel:
    case 0n:
      match task:
        case Task{session, pending}:
          session
    case 1n+k:
      match task:
        case Task{session, pending}:
          match pending:
            case Nil{}:
              session
            case index <> rest:
              explore(k, process(session, index, rest))

def reveal(session: Step.Session, +index: U32) -> Step.Session:
  match session:
    case Step.Session{+n, mines, cells, phase}:
      explore(U32.to_nat((8 * n * n + 1 : U32)),
              Task{Step.Session{n, mines, cells, phase}, [index]})

def main() -> U32:
  session = reveal(Step.new(Words.new(3)), 0)
  Step.snapshot(session, 8)
