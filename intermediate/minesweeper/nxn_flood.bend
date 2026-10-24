# N x N zero-region expansion for an already placed board (2 <= n <= 100).
# Step.click handles flags, out-of-bounds and mine loss before expansion.
import Base
import ./game.bend as Game
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words
import ./nxn_clues.bend as Clues
import ./nxn_neighbors.bend as Neighbors
import ./nxn_step.bend as Step

type Task is Type:
  Task{board: Words.MineWords, cells: Array<Game.Square>, pending: List<U32>}

def append(front: List<U32>, rest: List<U32>) -> List<U32>:
  match front:
    case Nil{}:
      rest
    case index <> tail:
      index <> append(tail, rest)

def enqueue(zero: Bool, +n: U32, +index: U32, rest: List<U32>) -> List<U32>:
  match zero:
    case False{}:
      rest
    case True{}:
      append(Neighbors.neighbors(n, index), rest)

def opened(+n: U32, +index: U32, rest: List<U32>,
           cells: Array<Game.Square>, pair: Words.MineWords & U32) -> Task:
  (board, clue) = pair
  Task{board, Array.set(Game.Square, cells, index, Game.Open{clue}),
       enqueue(U32.is_eq(clue, 0), n, index, rest)}

# A zero's neighbors cannot be mines; check again for defense in depth.
def if_mined(mined: Bool, +n: U32, +index: U32, rest: List<U32>,
             board: Words.MineWords, cells: Array<Game.Square>) -> Task:
  match mined:
    case True{}:
      Task{board, cells, rest}
    case False{}:
      opened(n, index, rest, cells, Clues.count_inside(n, board, index))

def from_mine(+n: U32, +index: U32, rest: List<U32>,
              cells: Array<Game.Square>, pair: Words.MineWords & Bool) -> Task:
  (board, mined) = pair
  if_mined(mined, n, index, rest, board, cells)

def from_cell(+n: U32, +index: U32, rest: List<U32>,
              board: Words.MineWords, pair: Array<Game.Square> & Game.Square) -> Task:
  (cells, square) = pair
  match square:
    case Game.Hidden{}:
      from_mine(n, index, rest, cells, Words.has(board, index))
    case Game.Flag{}:
      Task{board, cells, rest}
    case Game.Open{clue}:
      Task{board, cells, rest}

def visit(+n: U32, +index: U32, rest: List<U32>,
          board: Words.MineWords, cells: Array<Game.Square>) -> Task:
  from_cell(n, index, rest, board, Array.get(Game.Square, cells, index))

# At most n*n zero cells enqueue eight neighbors each. Nat fuel decreases.
def explore(fuel: Nat, +n: U32, task: Task) -> Task:
  match fuel:
    case 0n:
      task
    case 1n+k:
      match task:
        case Task{board, cells, pending}:
          match pending:
            case Nil{}:
              Task{board, cells, Nil{}}
            case index <> rest:
              explore(k, n, visit(n, index, rest, board, cells))

def finish(+n: U32, task: Task) -> Step.Session:
  match task:
    case Task{board, cells, pending}:
      Step.Session{n, board, cells, Step.Playing{}}

# Bend matches parameters, not computed Bool expressions.
def seed_zero(zero: Bool, +n: U32, +index: U32,
              board: Words.MineWords, cells: Array<Game.Square>) -> Step.Session:
  match zero:
    case False{}:
      Step.Session{n, board, cells, Step.Playing{}}
    case True{}:
      finish(n, explore(U32.to_nat((1 + 8 * n * n : U32)), n,
        Task{board, cells, Neighbors.neighbors(n, index)}))

def from_seed(+n: U32, +index: U32, board: Words.MineWords,
              read: Array<Game.Square> & Game.Square) -> Step.Session:
  (cells, square) = read
  match square:
    case Game.Hidden{}:
      Step.Session{n, board, cells, Step.Playing{}}
    case Game.Flag{}:
      Step.Session{n, board, cells, Step.Playing{}}
    case Game.Open{clue}:
      seed_zero(U32.is_eq(clue, 0), n, index, board, cells)

def seed_if_valid(valid: Bool, +n: U32, +index: U32,
                  board: Words.MineWords, cells: Array<Game.Square>) -> Step.Session:
  match valid:
    case False{}:
      Step.Session{n, board, cells, Step.Playing{}}
    case True{}:
      from_seed(n, index, board, Array.get(Game.Square, cells, index))

def after_click(session: Step.Session, +index: U32) -> Step.Session:
  match session:
    case Step.Session{+n, board, cells, phase}:
      match phase:
        case Step.Lost{}:
          Step.Session{n, board, cells, Step.Lost{}}
        case Step.Playing{}:
          seed_if_valid(Geo.valid_index(n, index), n, index, board, cells)

# This entry point does not yet set Won or handle first-click relocation.
def click(session: Step.Session, +index: U32) -> Step.Session:
  after_click(Step.click(session, index), index)

def main() -> U32:
  Step.snapshot(click(Step.new(Words.set_checked(Words.new(4), 15, True{})), 0), 14)
