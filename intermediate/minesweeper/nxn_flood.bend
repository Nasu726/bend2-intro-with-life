# N x N zero flood for an active Step.Session (2 <= n <= 100).
# This is a game-internal operation, never a public-information solver.
# A zero square enqueues its non-wrapping neighbors. Each zero square
# enqueues at most once because only previously Hidden squares expand.
import Base
import ./game.bend as Game
import ./nxn_step.bend as Step
import ./nxn_geometry.bend as Geo
import ./nxn_neighbors.bend as Neighbors
import ./nxn_mine_words.bend as Words
import ./nxn_clues.bend as Clues

type Queue is Type:
  Queue{session: Step.Session, pending: List<U32>}

# Prepend the eight-or-fewer neighbors without copying the Session.
def prepend(items: List<U32>, rest: List<U32>) -> List<U32>:
  match items:
    case Nil{}:
      rest
    case x <> xs:
      x <> prepend(xs, rest)

def next_pending(zero: Bool, +n: U32, +index: U32, rest: List<U32>) -> List<U32>:
  match zero:
    case True{}:
      prepend(Neighbors.neighbors(n, index), rest)
    case False{}:
      rest

# Clue is used both in the visible square and in the zero predicate.
# The + parameter explicitly permits this duplication of a U32 value.
def with_clue(+n: U32, +index: U32, cells: Array<Game.Square>,
              rest: List<U32>, mines: Words.MineWords, +clue: U32) -> Queue:
  updated = Array.set(Game.Square, cells, index, Game.Open{clue})
  Queue{Step.Session{n, mines, updated, Step.Playing{}},
        next_pending(U32.is_eq(clue, 0), n, index, rest)}

def open_count(+n: U32, +index: U32, cells: Array<Game.Square>,
               rest: List<U32>, pair: Words.MineWords & U32) -> Queue:
  (mines, clue) = pair
  with_clue(n, index, cells, rest, mines, clue)

# Defensive mine check: even a malformed queue must never reveal a mine.
def open_if_safe(+n: U32, +index: U32, cells: Array<Game.Square>,
                 rest: List<U32>, pair: Words.MineWords & Bool) -> Queue:
  (mines, mined) = pair
  match mined:
    case True{}:
      Queue{Step.Session{n, mines, cells, Step.Playing{}}, rest}
    case False{}:
      open_count(n, index, cells, rest, Clues.count_inside(n, mines, index))

def visit_read(+n: U32, mines: Words.MineWords, +index: U32,
               rest: List<U32>, pair: Array<Game.Square> & Game.Square) -> Queue:
  (cells, square) = pair
  match square:
    case Game.Hidden{}:
      open_if_safe(n, index, cells, rest, Words.has(mines, index))
    case Game.Flag{}:
      Queue{Step.Session{n, mines, cells, Step.Playing{}}, rest}
    case Game.Open{clue}:
      Queue{Step.Session{n, mines, cells, Step.Playing{}}, rest}

def visit_valid(valid: Bool, n: U32, mines: Words.MineWords,
                cells: Array<Game.Square>, +index: U32, rest: List<U32>) -> Queue:
  match valid:
    case False{}:
      Queue{Step.Session{n, mines, cells, Step.Playing{}}, rest}
    case True{}:
      visit_read(n, mines, index, rest, Array.get(Game.Square, cells, index))

def visit(session: Step.Session, +index: U32, rest: List<U32>) -> Queue:
  match session:
    case Step.Session{+n, mines, cells, phase}:
      match phase:
        case Step.Lost{}:
          Queue{Step.Session{n, mines, cells, Step.Lost{}}, Nil{}}
        case Step.Playing{}:
          visit_valid(Geo.valid_index(n, index), n, mines, cells, index, rest)

# Structural descent on Nat: each newly opened zero enqueues <= 8 jobs.
# At most n*n squares can first become Open, so 8*n*n+1 jobs suffice.
# The bound is valid, not a claim about runtime on 100x100 empty boards.
def explore(fuel: Nat, queue: Queue) -> Step.Session:
  match fuel:
    case 0n:
      match queue:
        case Queue{session, pending}:
          session
    case 1n+k:
      match queue:
        case Queue{session, pending}:
          match pending:
            case Nil{}:
              session
            case index <> rest:
              explore(k, visit(session, index, rest))

def cascade_if_zero(zero: Bool, +n: U32, mines: Words.MineWords,
                    cells: Array<Game.Square>, +index: U32) -> Step.Session:
  match zero:
    case True{}:
      explore(U32.to_nat((8 * n * n + 1 : U32)),
        Queue{Step.Session{n, mines, cells, Step.Playing{}},
              Neighbors.neighbors(n, index)})
    case False{}:
      Step.Session{n, mines, cells, Step.Playing{}}

def inspect_read(+n: U32, mines: Words.MineWords, +index: U32,
                 pair: Array<Game.Square> & Game.Square) -> Step.Session:
  (cells, square) = pair
  match square:
    case Game.Hidden{}:
      Step.Session{n, mines, cells, Step.Playing{}}
    case Game.Flag{}:
      Step.Session{n, mines, cells, Step.Playing{}}
    case Game.Open{clue}:
      cascade_if_zero(U32.is_eq(clue, 0), n, mines, cells, index)

def inspect_valid(valid: Bool, n: U32, mines: Words.MineWords,
                  cells: Array<Game.Square>, +index: U32) -> Step.Session:
  match valid:
    case False{}:
      Step.Session{n, mines, cells, Step.Playing{}}
    case True{}:
      inspect_read(n, mines, index, Array.get(Game.Square, cells, index))

# A mined first click is handled by Step.click; only safe zeroes expand.
# The caller is responsible for first-click relocation and Won transition.
def after_click(after: Step.Session, +index: U32) -> Step.Session:
  match after:
    case Step.Session{+n, mines, cells, phase}:
      match phase:
        case Step.Lost{}:
          Step.Session{n, mines, cells, Step.Lost{}}
        case Step.Playing{}:
          inspect_valid(Geo.valid_index(n, index), n, mines, cells, index)

def main() -> U32:
  board = Words.set_checked(Words.new(4), 15, True{})
  Step.snapshot(click(Step.new(board), 0), 14)

# Keep the result of Step.click as a parameter scrutinee, not a local binder.
def click(session: Step.Session, +index: U32) -> Step.Session:
  after_click(Step.click(session, index), index)
