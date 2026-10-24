# One-cell N x N actions, before zero expansion and first-click relocation.
# The mine truth never appears in the public observation. Valid n: 2..100.
# A click on a mine ends this limited session; a safe click opens one cell.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words
import ./nxn_clues.bend as Clues

type State is Type:
  State{mines: Words.MineWords, opened: Words.MineWords, flags: Words.MineWords, lost: Bool}

# PRECONDITION: mines was constructed for a valid board size.
def new(mines: Words.MineWords) -> State:
  match mines:
    case Words.MineWords{+n, words}:
      State{Words.MineWords{n, words}, Words.new(n), Words.new(n), False{}}

# Pass the resource through while checking the logical index (not Array capacity).
def checked(state: State, +index: U32) -> State & Bool:
  match state:
    case State{mines, opened, flags, lost}:
      match mines:
        case Words.MineWords{+n, words}:
          (State{Words.MineWords{n, words}, opened, flags, lost}, Geo.valid_index(n, index))

def toggle_flag_read(+index: U32, mines: Words.MineWords, opened: Words.MineWords,
                     pair: Words.MineWords & Bool, lost: Bool) -> State:
  (flags, present) = pair
  State{mines, opened, Words.set_checked(flags, index, Bool.not(present)), lost}

def toggle_closed(open_pair: Words.MineWords & Bool, mines: Words.MineWords,
                  flags: Words.MineWords, lost: Bool, +index: U32) -> State:
  (opened, is_open) = open_pair
  match is_open:
    case True{}:
      State{mines, opened, flags, lost}
    case False{}:
      toggle_flag_read(index, mines, opened, Words.has(flags, index), lost)

def mark_if_allowed(allowed: Bool, state: State, +index: U32) -> State:
  match allowed:
    case False{}:
      state
    case True{}:
      match state:
        case State{mines, opened, flags, lost}:
          toggle_closed(Words.has(opened, index), mines, flags, lost, index)

def mark_from_checked(pair: State & Bool, +index: U32) -> State:
  (state, valid) = pair
  match state:
    case State{mines, opened, flags, +lost}:
      mark_if_allowed(Bool.and(valid, Bool.not(lost)), State{mines, opened, flags, lost}, index)

def mark(state: State, +index: U32) -> State:
  mark_from_checked(checked(state, index), index)

def click_mine_read(+index: U32, pair: Words.MineWords & Bool,
                    opened: Words.MineWords, flags: Words.MineWords) -> State:
  (mines, is_mine) = pair
  match is_mine:
    case True{}:
      State{mines, opened, flags, True{}}
    case False{}:
      State{mines, Words.set_checked(opened, index, True{}), flags, False{}}

def click_open_read(+index: U32, mines: Words.MineWords,
                    pair: Words.MineWords & Bool, flags: Words.MineWords) -> State:
  (opened, is_open) = pair
  match is_open:
    case True{}:
      State{mines, opened, flags, False{}}
    case False{}:
      click_mine_read(index, Words.has(mines, index), opened, flags)

def click_flag_read(+index: U32, mines: Words.MineWords, opened: Words.MineWords,
                    pair: Words.MineWords & Bool) -> State:
  (flags, flagged) = pair
  match flagged:
    case True{}:
      State{mines, opened, flags, False{}}
    case False{}:
      click_open_read(index, mines, Words.has(opened, index), flags)

def click_if_allowed(allowed: Bool, state: State, +index: U32) -> State:
  match allowed:
    case False{}:
      state
    case True{}:
      match state:
        case State{mines, opened, flags, lost}:
          click_flag_read(index, mines, opened, Words.has(flags, index))

def click_from_checked(pair: State & Bool, +index: U32) -> State:
  (state, valid) = pair
  match state:
    case State{mines, opened, flags, +lost}:
      click_if_allowed(Bool.and(valid, Bool.not(lost)), State{mines, opened, flags, lost}, index)

def click(state: State, +index: U32) -> State:
  click_from_checked(checked(state, index), index)

# Public codes: 0..8 = revealed clue, 10 = hidden, 11 = flag, 12 = invalid.
# No mine bitset or unrevealed clue is returned.
def public_flag_read(pair: Words.MineWords & Bool, mines: Words.MineWords,
                     opened: Words.MineWords, lost: Bool) -> State & U32:
  (flags, flagged) = pair
  match flagged:
    case True{}:
      (State{mines, opened, flags, lost}, 11)
    case False{}:
      (State{mines, opened, flags, lost}, 10)

def read_clue(pair: Words.MineWords & Maybe<&2, U32>, opened: Words.MineWords,
              flags: Words.MineWords, lost: Bool) -> State & U32:
  (mines, result) = pair
  (State{mines, opened, flags, lost}, Clues.read_result(result))

def public_open_read(+index: U32, pair: Words.MineWords & Bool,
                     mines: Words.MineWords, flags: Words.MineWords, lost: Bool) -> State & U32:
  (opened, is_open) = pair
  match is_open:
    case True{}:
      read_clue(Clues.count_checked(mines, index), opened, flags, lost)
    case False{}:
      public_flag_read(Words.has(flags, index), mines, opened, lost)

def public_valid(valid: Bool, state: State, +index: U32) -> State & U32:
  match valid:
    case False{}:
      (state, 12)
    case True{}:
      match state:
        case State{mines, opened, flags, lost}:
          public_open_read(index, Words.has(opened, index), mines, flags, lost)

def public_from_checked(pair: State & Bool, +index: U32) -> State & U32:
  (state, valid) = pair
  public_valid(valid, state, index)

def public_at(state: State, +index: U32) -> State & U32:
  public_from_checked(checked(state, index), index)

def public_value(pair: State & U32) -> U32:
  (state, value) = pair
  value

def lost_code(state: State) -> U32:
  match state:
    case State{mines, opened, flags, lost}:
      match lost:
        case True{}:
          1
        case False{}:
          0

def main() -> U32:
  board = Words.set_checked(Words.new(10), 1, True{})
  public_value(public_at(click(new(board), 0), 0))
