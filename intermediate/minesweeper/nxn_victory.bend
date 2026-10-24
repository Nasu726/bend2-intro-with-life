# Bounded N x N victory predicate for an already active game.
# True only when every safe square is Open and at least one safe square exists.
# Flags on mines are optional; flags on safe cells block victory.
# This inspector does NOT change Step's Playing/Lost phase or implement flood.
import Base
import ./game.bend as Game
import ./nxn_mine_words.bend as Words
import ./nxn_step.bend as Step

type Scan is Type:
  Scan{board: Words.MineWords, cells: Array<Game.Square>, correct: Bool, saw_safe: Bool}

type Check is Type:
  Check{session: Step.Session, complete: Bool}

def square_ok(square: Game.Square, mined: Bool) -> Bool:
  match square:
    case Game.Hidden{}:
      mined
    case Game.Flag{}:
      mined
    case Game.Open{clue}:
      Bool.not(mined)

# In Bend 2, destructure a pair in a function parameter, not a computed
# value. This also keeps Array and mine words threaded linearly.
def from_cell(board: Words.MineWords, mined: Bool, correct: Bool,
              saw_safe: Bool, read: Array<Game.Square> & Game.Square) -> Scan:
  (cells, square) = read
  Scan{board, cells,
       Bool.and(correct, square_ok(square, mined)),
       Bool.or(saw_safe, Bool.not(mined))}

def from_mine(+index: U32, cells: Array<Game.Square>, correct: Bool,
              saw_safe: Bool, pair: Words.MineWords & Bool) -> Scan:
  (board, mined) = pair
  from_cell(board, mined, correct, saw_safe,
            Array.get(Game.Square, cells, index))

def visit(+index: U32, board: Words.MineWords, cells: Array<Game.Square>,
          correct: Bool, saw_safe: Bool) -> Scan:
  from_mine(index, cells, correct, saw_safe, Words.has(board, index))

# The only recursive function decreases Nat fuel; at most n*n logical
# cells are visited. Computed Scan values are passed as parameters.
def scan(fuel: Nat, +index: U32, state: Scan) -> Scan:
  match fuel:
    case 0n:
      state
    case 1n+k:
      match state:
        case Scan{board, cells, correct, saw_safe}:
          match correct:
            case False{}:
              Scan{board, cells, False{}, saw_safe}
            case True{}:
              scan(k, (index + 1 : U32),
                   visit(index, board, cells, True{}, saw_safe))

def finish(+n: U32, state: Scan) -> Check:
  match state:
    case Scan{board, cells, correct, saw_safe}:
      Check{Step.Session{n, board, cells, Step.Playing{}},
            Bool.and(correct, saw_safe)}

# Preserve the resource-like Session. A Lost session cannot win.
def inspect(session: Step.Session) -> Check:
  match session:
    case Step.Session{+n, mines, cells, phase}:
      match phase:
        case Step.Lost{}:
          Check{Step.Session{n, mines, cells, Step.Lost{}}, False{}}
        case Step.Playing{}:
          finish(n, scan(U32.to_nat((n * n : U32)), 0,
                         Scan{mines, cells, True{}, False{}}))

def verdict(check: Check) -> U32:
  match check:
    case Check{session, complete}:
      match complete:
        case True{}:
          1
        case False{}:
          0

def main() -> U32:
  board = Words.set_checked(Words.new(2), 3, True{})
  game = Step.click(Step.click(Step.click(Step.new(board), 0), 1), 2)
  verdict(inspect(game))
