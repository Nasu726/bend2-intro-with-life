# Variable-size square board storage for N=2..32.
# This is the bounded N x N board CORE; no win/flood/GUI controller yet.
# The 4x4 implementation remains as a separately verified regression oracle.
import Base
import ./game.bend as Game

type State is Type:
  State{n: U32, mines: Array<Bool>, cells: Array<Game.Square>}

type Creation is Type:
  Invalid{}
  Created{board: State}

# No attempt to allocate for N=0, N=1 or unbounded attacker input.
# A board above 32x32 needs a separately reviewed memory/overflow contract.
def valid_size(+n: U32) -> Bool:
  Bool.and(U32.is_ge(n, 2), U32.is_le(n, 32))

# Column x first, row y second, with row-major storage.
# Contract: call index ONLY after an in_bounds check.
def index(n: U32, x: U32, y: U32) -> U32:
  (y * n + x : U32)

def in_bounds(+n: U32, +x: U32, +y: U32) -> Bool:
  Bool.and(valid_size(n),
    Bool.and(U32.is_lt(x, n), U32.is_lt(y, n)))

def valid_index(+n: U32, +i: U32) -> Bool:
  Bool.and(valid_size(n), U32.is_lt(i, (n * n : U32)))

# For 10x10, depth=7; the physical array has 128 entries.
# The extra entries are NEVER logical game cells.
def depth_loop(fuel: Nat, +count: U32, +capacity: U32, depth: Nat) -> Nat:
  match fuel:
    case 0n:
      depth
    case 1n+more:
      match U32.is_le(count, capacity):
        case True{}:
          depth
        case False{}:
          depth_loop(more, count, (capacity + capacity : U32), 1n+depth)

def storage_depth(n: U32) -> Nat:
  depth_loop(11n, (n * n : U32), 1, 0n)

def new_valid(n: U32) -> State:
  +d = storage_depth(n)
  State{n, Array.new(Bool, d, False{}),
           Array.new(Game.Square, d, Game.Hidden{})}

# Public constructor: validated N; avoids mismatched user-supplied depth.
def new_checked(+n: U32) -> Creation:
  match valid_size(n):
    case False{}:
      Invalid{}
    case True{}:
      Created{new_valid(n)}

# Read logical length without losing the cells array.
def capacity_from_read(n: U32, mines: Array<Bool>,
                       r: Array<Game.Square> & U32) -> State & U32:
  (cells, size) = r
  (State{n, mines, cells}, size)

def capacity(state: State) -> State & U32:
  match state:
    case State{n, mines, cells}:
      capacity_from_read(n, mines, Array.size(Game.Square, cells))

# Flag toggling is limited to logical positions 0..N*N-1.
def mark_from_read(n: U32, mines: Array<Bool>, i: U32,
                   r: Array<Game.Square> & Game.Square) -> State:
  (cells, square) = r
  State{n, mines, Array.set(Game.Square, cells, i, Game.toggle_flag(square))}

def mark_valid(valid: Bool, n: U32, mines: Array<Bool>,
               cells: Array<Game.Square>, i: U32) -> State:
  match valid:
    case False{}:
      State{n, mines, cells}
    case True{}:
      mark_from_read(n, mines, i, Array.get(Game.Square, cells, i))

def mark_checked(state: State, +i: U32) -> State:
  match state:
    case State{n, mines, cells}:
      mark_valid(valid_index(n, i), n, mines, cells, i)

# A read outside the logical N*N cells returns None, never a wrapped cell.
# The board is returned because Array is affine.
def read_from_array(n: U32, mines: Array<Bool>,
                    r: Array<Game.Square> & Game.Square) ->
  State & Maybe<&2, Game.Square>:
  (cells, square) = r
  (State{n, mines, cells}, Some{square})

def read_valid(valid: Bool, n: U32, mines: Array<Bool>,
               cells: Array<Game.Square>, i: U32) ->
  State & Maybe<&2, Game.Square>:
  match valid:
    case False{}:
      (State{n, mines, cells}, None{})
    case True{}:
      read_from_array(n, mines, Array.get(Game.Square, cells, i))

def read_checked(state: State, +i: U32) ->
  State & Maybe<&2, Game.Square>:
  match state:
    case State{n, mines, cells}:
      read_valid(valid_index(n, i), n, mines, cells, i)

# The true mine array is owned only by the game setup/controller.
# Do not pass State or this setter to the public-information solver.
def mine_valid(valid: Bool, n: U32, mines: Array<Bool>,
               cells: Array<Game.Square>, i: U32) -> State:
  match valid:
    case False{}:
      State{n, mines, cells}
    case True{}:
      State{n, Array.set(Bool, mines, i, True{}), cells}

def set_mine_for_setup(state: State, +i: U32) -> State:
  match state:
    case State{n, mines, cells}:
      mine_valid(valid_index(n, i), n, mines, cells, i)

# Printable codes are only for the small layout demo, not game serialization.
def square_code(m: Maybe<&2, Game.Square>) -> U32:
  match m:
    case None{}:
      9
    case Some{square}:
      match square:
        case Game.Hidden{}:
          0
        case Game.Flag{}:
          1
        case Game.Open{clue}:
          (10 + clue : U32)
