# Bounded N x N zero cascade on an already active, mine-internal session.
# N=2..100. This primitive preserves Playing/Lost and does not decide Won.
# It never exposes mine truth to the public-information solver.
import Base
import ./game.bend as Game
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words
import ./nxn_clues.bend as Clues
import ./nxn_neighbors.bend as Neighbors
import ./nxn_step.bend as Step

type Task is Type:
  Task{n: U32, mines: Words.MineWords, cells: Array<Game.Square>, work: List<U32>}

# Each zero square is opened only once, and enqueues at most eight neighbors.
# Prepending is sufficient: flood membership does not depend on visit order.
def prepend_all(items: List<U32>, rest: List<U32>) -> List<U32>:
  match items:
    case Nil{}:
      rest
    case x <> xs:
      x <> prepend_all(xs, rest)

def next_work(zero: Bool, +n: U32, +index: U32, rest: List<U32>) -> List<U32>:
  match zero:
    case True{}:
      prepend_all(Neighbors.neighbors(n, index), rest)
    case False{}:
      rest

def make_open(+n: U32, +index: U32, cells: Array<Game.Square>,
              rest: List<U32>, mines: Words.MineWords, +clue: U32) -> Task:
  Task{n, mines, Array.set(Game.Square, cells, index, Game.Open{clue}),
       next_work(U32.is_eq(clue, 0), n, index, rest)}

def from_clue(+n: U32, +index: U32, cells: Array<Game.Square>,
              rest: List<U32>, pair: Words.MineWords & U32) -> Task:
  (mines, clue) = pair
  make_open(n, index, cells, rest, mines, clue)

def from_cell(+n: U32, +index: U32, mines: Words.MineWords,
              rest: List<U32>, pair: Array<Game.Square> & Game.Square) -> Task:
  (cells, square) = pair
  match square:
    case Game.Hidden{}:
      from_clue(n, index, cells, rest, Clues.count_inside(n, mines, index))
    case Game.Flag{}:
      Task{n, mines, cells, rest}
    case Game.Open{clue}:
      Task{n, mines, cells, rest}

def from_mine(+n: U32, +index: U32, cells: Array<Game.Square>,
              rest: List<U32>, pair: Words.MineWords & Bool) -> Task:
  (mines, mined) = pair
  match mined:
    case True{}:
      Task{n, mines, cells, rest}
    case False{}:
      from_cell(n, index, mines, rest, Array.get(Game.Square, cells, index))

def visit(task: Task, +index: U32) -> Task:
  match task:
    case Task{+n, mines, cells, work}:
      from_mine(n, index, cells, work, Words.has(mines, index))

# Fuel 1+8*n*n bounds the initial click and all jobs from zero squares.
# Early Nil termination avoids iterating unused fuel. Repeated jobs are
# harmless because opened/flagged cells are never expanded again.
def explore(fuel: Nat, task: Task) -> Task:
  match fuel:
    case 0n:
      task
    case 1n+k:
      match task:
        case Task{n, mines, cells, work}:
          match work:
            case Nil{}:
              Task{n, mines, cells, Nil{}}
            case index <> rest:
              explore(k, visit(Task{n, mines, cells, rest}, index))

def finish(task: Task) -> Step.Session:
  match task:
    case Task{n, mines, cells, work}:
      Step.Session{n, mines, cells, Step.Playing{}}

def valid_start(valid: Bool, +n: U32, mines: Words.MineWords,
                cells: Array<Game.Square>, +index: U32) -> Step.Session:
  match valid:
    case False{}:
      Step.Session{n, mines, cells, Step.Playing{}}
    case True{}:
      finish(explore(U32.to_nat((8 * n * n + 1 : U32)),
                     Task{n, mines, cells, [index]}))

# Call for a safe click in a placed game. A mine is deliberately NOT a loss
# here: Step.click remains responsible for loss, and Victory for completion.
def reveal(session: Step.Session, +index: U32) -> Step.Session:
  match session:
    case Step.Session{+n, mines, cells, phase}:
      match phase:
        case Step.Lost{}:
          Step.Session{n, mines, cells, Step.Lost{}}
        case Step.Playing{}:
          valid_start(Geo.valid_index(n, index), n, mines, cells, index)

def main() -> U32:
  board = Words.set_checked(Words.new(3), 8, True{})
  Step.snapshot(reveal(Step.new(board), 0), 7)
