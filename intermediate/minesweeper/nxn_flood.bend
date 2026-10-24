# Bounded zero cascade for an already active N x N session (2 <= N <= 100).
# Reuses the checked mine words, non-wrapping neighbors and clue calculator.
# A Hidden safe square is opened once; only clue 0 adds its neighbors.
# Flagged and already Open squares are never changed; mine hits lose.
# This module does NOT implement Fresh relocation or a Won phase.
import Base
import ./game.bend as Game
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words
import ./nxn_clues.bend as Clues
import ./nxn_neighbors.bend as Neighbors
import ./nxn_step.bend as Step

type Task is Type:
  Task{session: Step.Session, work: List<U32>}

# Keep the frontier in neighbor-index order. Each zero square can enqueue
# at most eight indices, so 1 + 8*n*n is a safe bound on queue removals.
def prepend_all(front: List<U32>, back: List<U32>) -> List<U32>:
  match front:
    case Nil{}:
      back
    case x <> xs:
      x <> prepend_all(xs, back)

def next_work(zero: Bool, +n: U32, +index: U32, rest: List<U32>) -> List<U32>:
  match zero:
    case True{}:
      prepend_all(Neighbors.neighbors(n, index), rest)
    case False{}:
      rest

# The clue is read twice (to display it and to test for zero).
# A + parameter makes that duplication explicit in Bend's affine checker.
def store_open(+n: U32, +index: U32, +clue: U32,
               board: Words.MineWords, cells: Array<Game.Square>,
               rest: List<U32>) -> Task:
  Task{Step.Session{n, board,
                    Array.set(Game.Square, cells, index, Game.Open{clue}),
                    Step.Playing{}},
       next_work(U32.is_eq(clue, 0), n, index, rest)}

def opened(+n: U32, +index: U32, cells: Array<Game.Square>,
           rest: List<U32>, pair: Words.MineWords & U32) -> Task:
  (board, clue) = pair
  store_open(n, index, clue, board, cells, rest)

def checked_mine(+n: U32, +index: U32, cells: Array<Game.Square>,
                 rest: List<U32>, pair: Words.MineWords & Bool) -> Task:
  (board, mined) = pair
  match mined:
    case True{}:
      Task{Step.Session{n, board, cells, Step.Lost{}}, Nil{}}
    case False{}:
      opened(n, index, cells, rest, Clues.count_inside(n, board, index))

def from_read(+n: U32, board: Words.MineWords, +index: U32,
              rest: List<U32>, read: Array<Game.Square> & Game.Square) -> Task:
  (cells, square) = read
  match square:
    case Game.Hidden{}:
      checked_mine(n, index, cells, rest, Words.has(board, index))
    case Game.Flag{}:
      Task{Step.Session{n, board, cells, Step.Playing{}}, rest}
    case Game.Open{clue}:
      Task{Step.Session{n, board, cells, Step.Playing{}}, rest}

def valid_visit(valid: Bool, +n: U32, board: Words.MineWords,
                cells: Array<Game.Square>, +index: U32,
                rest: List<U32>) -> Task:
  match valid:
    case False{}:
      Task{Step.Session{n, board, cells, Step.Playing{}}, rest}
    case True{}:
      from_read(n, board, index, rest, Array.get(Game.Square, cells, index))

def visit(session: Step.Session, +index: U32, rest: List<U32>) -> Task:
  match session:
    case Step.Session{+n, board, cells, phase}:
      match phase:
        case Step.Lost{}:
          Task{Step.Session{n, board, cells, Step.Lost{}}, Nil{}}
        case Step.Playing{}:
          valid_visit(Geo.valid_index(n, index), n, board, cells, index, rest)

# The Nat argument decreases even if the frontier grows. Because each
# zero square is opened once, at most n*n such squares enqueue neighbors.
def explore(fuel: Nat, task: Task) -> Step.Session:
  match fuel:
    case 0n:
      match task:
        case Task{session, work}:
          session
    case 1n+k:
      match task:
        case Task{session, work}:
          match work:
            case Nil{}:
              session
            case index <> rest:
              explore(k, visit(session, index, rest))

# PRECONDITION: the Session was created with a valid checked board.
# Invalid logical indices, including Array padding, are ignored.
def click(session: Step.Session, +index: U32) -> Step.Session:
  match session:
    case Step.Session{+n, board, cells, phase}:
      explore(U32.to_nat((1 + 8 * n * n : U32)),
              Task{Step.Session{n, board, cells, phase}, index <> Nil{}})

def main() -> U32:
  Step.snapshot(click(Step.new(Words.new(2)), 0), 3)
