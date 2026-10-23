# Publicly known information for an N x N game with M mines, N=2..100.
# This is NOT the mine board, a zero-flood algorithm, or a complete game.
# The MineWords module is reused only as a checked U32 bitset implementation:
# the freshly allocated `opened` value never contains hidden mine truth.
# A read returns 9 for a hidden/invalid cell; displayed clues are 0..8.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Bits

type PublicState is Type:
  PublicState{n: U32, m: U32, opened: Bits.MineWords, clues: Array<U32>}

# Only valid configurations may be allocated: N=2..100 and 0<=M<N*N.
def valid_config(+n: U32, +m: U32) -> Bool:
  Bool.and(Geo.valid_size(n), U32.is_lt(m, (n * n : U32)))

# PRECONDITION for new: valid_config(n, m). Reject untrusted inputs.
def new(+n: U32, +m: U32) -> PublicState:
  PublicState{n, m, Bits.new(n),
    Array.new(U32,
      Bits.depth_loop(15n, U32.is_lt(1, (n * n : U32)), 1, 0n, (n * n : U32)), 0)}

# Keep the first published clue: repeated reveals must not rewrite history.
def reveal_unopened(pair: Bits.MineWords & Bool, +n: U32, +m: U32,
                    clues: Array<U32>, +i: U32, +value: U32) -> PublicState:
  (opened, already) = pair
  match already:
    case True{}:
      PublicState{n, m, opened, clues}
    case False{}:
      PublicState{n, m, Bits.set_checked(opened, i, True{}),
                  Array.set(U32, clues, i, value)}

def reveal_if_valid(valid: Bool, +n: U32, +m: U32, opened: Bits.MineWords,
                    clues: Array<U32>, +i: U32, +value: U32) -> PublicState:
  match valid:
    case True{}:
      reveal_unopened(Bits.has(opened, i), n, m, clues, i, value)
    case False{}:
      PublicState{n, m, opened, clues}

# Matching a resource gives an affine n. Pass it to a helper with
# reusable +n before using it for both checking and rebuilding the state.
def reveal_parts(+n: U32, m: U32, opened: Bits.MineWords,
                 clues: Array<U32>, +i: U32, +value: U32) -> PublicState:
  reveal_if_valid(Bool.and(Geo.valid_index(n, i), U32.is_lt(value, 9)),
                  n, m, opened, clues, i, value)

def reveal(board: PublicState, +i: U32, +value: U32) -> PublicState:
  match board:
    case PublicState{n, m, opened, clues}:
      reveal_parts(n, m, opened, clues, i, value)

def read_known(pair: Array<U32> & U32, +n: U32, +m: U32,
               opened: Bits.MineWords) -> PublicState & U32:
  (clues, value) = pair
  (PublicState{n, m, opened, clues}, value)

def read_opened(pair: Bits.MineWords & Bool, +n: U32, +m: U32,
                clues: Array<U32>, +i: U32) -> PublicState & U32:
  (opened, present) = pair
  match present:
    case True{}:
      read_known(Array.get(U32, clues, i), n, m, opened)
    case False{}:
      (PublicState{n, m, opened, clues}, 9)

def read_if_valid(valid: Bool, +n: U32, +m: U32, opened: Bits.MineWords,
                  clues: Array<U32>, +i: U32) -> PublicState & U32:
  match valid:
    case True{}:
      read_opened(Bits.has(opened, i), n, m, clues, i)
    case False{}:
      (PublicState{n, m, opened, clues}, 9)

def read_parts(+n: U32, m: U32, opened: Bits.MineWords,
               clues: Array<U32>, +i: U32) -> PublicState & U32:
  read_if_valid(Geo.valid_index(n, i), n, m, opened, clues, i)

def read(board: PublicState, +i: U32) -> PublicState & U32:
  match board:
    case PublicState{n, m, opened, clues}:
      read_parts(n, m, opened, clues, i)

# Return M with the state, preserving resource ownership.
# Unlike a mine bitset, this total is legitimate public information.
def total_parts(+n: U32, +m: U32, opened: Bits.MineWords,
                clues: Array<U32>) -> PublicState & U32:
  (PublicState{n, m, opened, clues}, m)

def total_mines(board: PublicState) -> PublicState & U32:
  match board:
    case PublicState{n, m, opened, clues}:
      total_parts(n, m, opened, clues)

def read_value(pair: PublicState & U32) -> U32:
  (unused, value) = pair
  value

def main() -> U32:
  read_value(read(reveal(reveal(new(10, 10), 31, 2), 32, 3), 32))
