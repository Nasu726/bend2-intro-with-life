# Full 4x4 internal state; see LAWS.bend before changing behavior.
# Mine truth is a 16-bit U32 mask. Every visible square is in a dense Array.
# This internal state MUST NOT be exposed to a no-guess solver.
import Base
import ./game.bend as Game
import ./board.bend as Board

type State is Type:
  State{mines: U32, cells: Array<Game.Square>}

# Exactly 2^4=16 visible entries. Caller must restrict mines to 16 bits.
def new_state(mines: U32) -> State:
  State{mines, Array.new(Game.Square, 4n, Game.Hidden{})}

def mine_mask(s: State) -> U32:
  match s:
    case State{mines, cells}:
      mines

# Array.get wraps invalid indices, so the UI/game-controller must validate
# index <16 before using these low-level functions.
def square_from_read(read: Array<Game.Square> & Game.Square) -> Game.Square:
  (cells, square) = read
  square

def visible_at(s: State, index: U32) -> Game.Square:
  match s:
    case State{mines, cells}:
      square_from_read(Array.get(Game.Square, cells, index))

def toggle_from_read(index: U32, read: Array<Game.Square> & Game.Square) -> Array<Game.Square>:
  (cells, square) = read
  Array.set(Game.Square, cells, index, Game.toggle_flag(square))

def toggle_at(s: State, +index: U32) -> State:
  match s:
    case State{mines, cells}:
      State{mines, toggle_from_read(index, Array.get(Game.Square, cells, index))}

# PRECONDITION: caller has already checked mine_mask and in-bounds index.
def reveal_from_read(index: U32, clue: U32, read: Array<Game.Square> & Game.Square) -> Array<Game.Square>:
  (cells, square) = read
  Array.set(Game.Square, cells, index, Game.reveal_safe(square, clue))

def reveal_at(s: State, +index: U32, clue: U32) -> State:
  match s:
    case State{mines, cells}:
      State{mines, reveal_from_read(index, clue, Array.get(Game.Square, cells, index))}

def bit_is_set(mines: U32, flag: U32) -> Bool:
  U32.is_ne(U32.and(mines, flag), 0)

def one_if_true(b: Bool) -> U32:
  match b:
    case True{}:
      1
    case False{}:
      0

# A cell contributes one only when it contains a mine AND is adjacent.
def contribution(+mines: U32, +x: U32, +y: U32, u: U32, v: U32, bit: U32) -> U32:
  one_if_true(Bool.and(bit_is_set(mines, bit), Board.neighbor(x, y, u, v)))

# Count the mines at neighbors of (x,y); Board.neighbor excludes the
# current cell and positions beyond any edge. Never toroidal-wrap.
def clue(+mines: U32, +x: U32, +y: U32) -> U32:
  (
    contribution(mines, x, y, 0, 0, 1) +
    contribution(mines, x, y, 1, 0, 2) +
    contribution(mines, x, y, 2, 0, 4) +
    contribution(mines, x, y, 3, 0, 8) +
    contribution(mines, x, y, 0, 1, 16) +
    contribution(mines, x, y, 1, 1, 32) +
    contribution(mines, x, y, 2, 1, 64) +
    contribution(mines, x, y, 3, 1, 128) +
    contribution(mines, x, y, 0, 2, 256) +
    contribution(mines, x, y, 1, 2, 512) +
    contribution(mines, x, y, 2, 2, 1024) +
    contribution(mines, x, y, 3, 2, 2048) +
    contribution(mines, x, y, 0, 3, 4096) +
    contribution(mines, x, y, 1, 3, 8192) +
    contribution(mines, x, y, 2, 3, 16384) +
    contribution(mines, x, y, 3, 3, 32768) : U32
  )

def main() -> U32:
  clue(33, 1, 0)

# Public entry points: do not allow Array.get's index wraparound.
def toggle_if_valid(valid: Bool, state: State, index: U32) -> State:
  match valid:
    case False{}:
      state
    case True{}:
      toggle_at(state, index)

def toggle_checked(state: State, +index: U32) -> State:
  toggle_if_valid(U32.is_lt(index, 16), state, index)

def reveal_if_valid(valid: Bool, state: State, index: U32, clue: U32) -> State:
  match valid:
    case False{}:
      state
    case True{}:
      reveal_at(state, index, clue)

def reveal_checked(state: State, +index: U32, clue: U32) -> State:
  reveal_if_valid(U32.is_lt(index, 16), state, index, clue)

# A win means every non-mine cell is Open; flags alone never count.
# Standard Array.clone is appropriate: we inspect the same cells while
# retaining them in the returned State, without duplicating the game logic.
def counts_as_cleared(square: Game.Square, mine: Bool) -> Bool:
  match square mine:
    case Game.Open{clue} _:
      True{}
    case _ True{}:
      True{}
    case _ False{}:
      False{}

def all_safe_open(squares: List<Game.Square>, +mines: U32, +bit: U32) -> Bool:
  match squares:
    case Nil{}:
      True{}
    case square <> rest:
      Bool.and(
        counts_as_cleared(square, bit_is_set(mines, bit)),
        all_safe_open(rest, mines, (bit + bit : U32)))

def checked_from_clone(+mines: U32, pair: Array<Game.Square> & Array<Game.Square>) -> State & Bool:
  (keep, inspect) = pair
  (State{mines, keep}, all_safe_open(Array.to_list(Game.Square, inspect), mines, 1))

def check_won(board: State) -> State & Bool:
  match board:
    case State{mines, cells}:
      checked_from_clone(mines, Array.clone(Game.Square, cells))
