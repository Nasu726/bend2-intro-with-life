# Bounded N x N victory predicate for an already active game.
# A result is true only when EVERY safe square is Open and at least one
# safe square exists. Flags on mines are optional; flags on safe cells block
# victory. This inspector does NOT change Step's Playing/Lost phase.
# No flood or automatic transition to Won is implemented here.
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

def visit(+index: U32, board: Words.MineWords, cells: Array<Game.Square>,
          correct: Bool, saw_safe: Bool) -> Scan:
  (board, mined) = Words.has(board, index)
  (cells, square) = Array.get(Game.Square, cells, index)
  Scan{board, cells,
       Bool.and(correct, square_ok(square, mined)),
       Bool.or(saw_safe, Bool.not(mined))}

# Structural Nat fuel bounds visits to n*n logical cells, never Array padding.
# Stop early on a hidden/flagged safe cell to avoid unnecessary work.
def scan(fuel: Nat, +index: U32, board: Words.MineWords,
         cells: Array<Game.Square>, correct: Bool, saw_safe: Bool) -> Scan:
  match fuel:
    case 0n:
      Scan{board, cells, correct, saw_safe}
    case 1n+k:
      match correct:
        case False{}:
          Scan{board, cells, False{}, saw_safe}
        case True{}:
          match visit(index, board, cells, True{}, saw_safe):
            case Scan{board, cells, correct, saw_safe}:
              scan(k, (index + 1 : U32), board, cells, correct, saw_safe)

# Preserve the resource-like Session. A Lost session cannot win.
def inspect(session: Step.Session) -> Check:
  match session:
    case Step.Session{+n, mines, cells, phase}:
      match phase:
        case Step.Lost{}:
          Check{Step.Session{n, mines, cells, Step.Lost{}}, False{}}
        case Step.Playing{}:
          match scan(U32.to_nat((n * n : U32)), 0, mines, cells, True{}, False{}):
            case Scan{board, cells, correct, saw_safe}:
              Check{Step.Session{n, board, cells, Step.Playing{}},
                    Bool.and(correct, saw_safe)}

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
