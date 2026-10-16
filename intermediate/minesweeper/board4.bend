# Full 4x4 internal state; see LAWS.bend before changing behavior.
# Mine truth is a 16-bit U32 mask. Every visible square is in a dense Array.
# This internal state MUST NOT be exposed to a no-guess solver.
import Base
import ./game.bend as Game
import ./board.bend as Board

type State is Data:
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
def visible_at(s: State, index: U32) -> Game.Square:
  match s:
    case State{mines, cells}:
      (cells, square) = Array.get(Game.Square, cells, index)
      square

def toggle_cells(cells: Array<Game.Square>, index: U32) -> Array<Game.Square>:
  (cells, square) = Array.get(Game.Square, cells, index)
  Array.set(Game.Square, cells, index, Game.toggle_flag(square))

def toggle_at(s: State, index: U32) -> State:
  match s:
    case State{mines, cells}:
      State{mines, toggle_cells(cells, index)}

# PRECONDITION: caller has already checked mine_mask and in-bounds index.
def reveal_cells(cells: Array<Game.Square>, index: U32, clue: U32) -> Array<Game.Square>:
  (cells, square) = Array.get(Game.Square, cells, index)
  Array.set(Game.Square, cells, index, Game.reveal_safe(square, clue))

def reveal_at(s: State, index: U32, clue: U32) -> State:
  match s:
    case State{mines, cells}:
      State{mines, reveal_cells(cells, index, clue)}

def bit_is_set(mines: U32, flag: U32) -> Bool:
  U32.is_ne(U32.and(mines, flag), 0)

def one_if_neighbor(neighbor: Bool) -> U32:
  match neighbor:
    case True{}:
      1
    case False{}:
      0

# Test the mine BEFORE testing adjacency: with no mines, the answer is
# definitionally zero even for symbolic x,y (B-04's universal empty law).
def count_if_mined(has_mine: Bool, neighbor: Bool) -> U32:
  match has_mine:
    case False{}:
      0
    case True{}:
      one_if_neighbor(neighbor)

def contribution(+mines: U32, +x: U32, +y: U32, u: U32, v: U32, bit: U32) -> U32:
  count_if_mined(bit_is_set(mines, bit), Board.neighbor(x, y, u, v))

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
