# A deliberately bounded N x N active-game step (n=2..100).
# Not a complete game: first-click relocation, zero flood and victory are
# intentionally left to later milestones. Never expose mine truth to a solver.
import Base
import ./game.bend as Game
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words
import ./nxn_clues.bend as Clues

type Phase is Data:
  Playing{}
  Lost{}

type Session is Type:
  Session{n: U32, mines: Words.MineWords, cells: Array<Game.Square>, phase: Phase}

# PRECONDITION: mines was created with Words.new for a valid n.
# A visible Array is sized by the logical CELL count, not word count.
def new(mines: Words.MineWords) -> Session:
  match mines:
    case Words.MineWords{n, words}:
      size = (n * n : U32)
      depth = Words.depth_loop(15n, U32.is_lt(1, size), 1, 0n, size)
      Session{n, Words.MineWords{n, words}, Array.new(Game.Square, depth, Game.Hidden{}), Playing{}}

def mark_read(n: U32, mines: Words.MineWords, index: U32, read: Array<Game.Square> & Game.Square) -> Session:
  (cells, square) = read
  Session{n, mines, Array.set(Game.Square, cells, index, Game.toggle_flag(square)), Playing{}}

def mark_valid(valid: Bool, n: U32, mines: Words.MineWords, cells: Array<Game.Square>, index: U32) -> Session:
  match valid:
    case False{}:
      Session{n, mines, cells, Playing{}}
    case True{}:
      mark_read(n, mines, index, Array.get(Game.Square, cells, index))

def mark(session: Session, +index: U32) -> Session:
  match session:
    case Session{n, mines, cells, phase}:
      match phase:
        case Lost{}:
          Session{n, mines, cells, Lost{}}
        case Playing{}:
          mark_valid(Geo.valid_index(n, index), n, mines, cells, index)

def open_with_count(n: U32, index: U32, cells: Array<Game.Square>, pair: Words.MineWords & U32) -> Session:
  (mines, clue) = pair
  Session{n, mines, Array.set(Game.Square, cells, index, Game.Open{clue}), Playing{}}

def click_mine_result(n: U32, index: U32, cells: Array<Game.Square>, pair: Words.MineWords & Bool) -> Session:
  (mines, mined) = pair
  match mined:
    case True{}:
      Session{n, mines, cells, Lost{}}
    case False{}:
      open_with_count(n, index, cells, Clues.count_inside(n, mines, index))

def click_read(n: U32, mines: Words.MineWords, index: U32, read: Array<Game.Square> & Game.Square) -> Session:
  (cells, square) = read
  match square:
    case Game.Hidden{}:
      click_mine_result(n, index, cells, Words.has(mines, index))
    case Game.Flag{}:
      Session{n, mines, cells, Playing{}}
    case Game.Open{clue}:
      Session{n, mines, cells, Playing{}}

def click_valid(valid: Bool, n: U32, mines: Words.MineWords, cells: Array<Game.Square>, index: U32) -> Session:
  match valid:
    case False{}:
      Session{n, mines, cells, Playing{}}
    case True{}:
      click_read(n, mines, index, Array.get(Game.Square, cells, index))

def click(session: Session, +index: U32) -> Session:
  match session:
    case Session{n, mines, cells, phase}:
      match phase:
        case Lost{}:
          Session{n, mines, cells, Lost{}}
        case Playing{}:
          click_valid(Geo.valid_index(n, index), n, mines, cells, index)

# One-use inspection helper for the finite differential test.
# Invalid logical cells are NOT read from Array padding.
def phase_code(phase: Phase) -> U32:
  match phase:
    case Playing{}:
      0
    case Lost{}:
      2

def square_code(square: Game.Square) -> U32:
  match square:
    case Game.Hidden{}:
      0
    case Game.Flag{}:
      1
    case Game.Open{clue}:
      (10 + clue : U32)

def visible_code(valid: Bool, cells: Array<Game.Square>, index: U32) -> U32:
  match valid:
    case False{}:
      99
    case True{}:
      (cells, square) = Array.get(Game.Square, cells, index)
      square_code(square)

def snapshot(session: Session, +index: U32) -> U32:
  match session:
    case Session{n, mines, cells, phase}:
      (100 * phase_code(phase) + visible_code(Geo.valid_index(n, index), cells, index) : U32)

def main() -> U32:
  snapshot(click(new(Words.set_checked(Words.new(10), 1, True{})), 0), 0)
