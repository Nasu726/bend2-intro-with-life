# N x N mine truth as U32 words. Valid sizes: 2..100.
# Storage only: never pass mine truth to a public-information solver.
# Array capacity is rounded up to a power of two; logical word count
# is ceil(n*n/32). Reject invalid cells before Array.get/set.
import Base
import ./nxn_geometry.bend as Geo

type MineWords is Type:
  MineWords{n: U32, words: Array<U32>}

# Array is a resource-like Type, so it cannot be stored in Maybe<Data>.
type Creation is Type:
  Created{board: MineWords}
  InvalidSize{}

def word_count(+n: U32) -> U32:
  U32.div((n * n + 31 : U32), 32)

# Structural fuel bound: 313 logical words need at most depth 9.
def depth_loop(fuel: Nat, small: Bool, +capacity: U32, +depth: Nat, +need: U32) -> Nat:
  match fuel:
    case 0n:
      depth
    case 1n+k:
      match small:
        case True{}:
          depth_loop(k, U32.is_lt((capacity + capacity : U32), need), (capacity + capacity : U32), (1n + depth : Nat), need)
        case False{}:
          depth

# PRECONDITION: Geo.valid_size(n). Call new_checked for untrusted sizes.
def new(+n: U32) -> MineWords:
  MineWords{n, Array.new(U32, depth_loop(10n, U32.is_lt(1, word_count(n)), 1, 0n, word_count(n)), 0)}

def new_if_valid(valid: Bool, n: U32) -> Creation:
  match valid:
    case True{}:
      Created{new(n)}
    case False{}:
      InvalidSize{}

def new_checked(+n: U32) -> Creation:
  new_if_valid(Geo.valid_size(n), n)

def bit(+index: U32) -> U32:
  U32.shln(1, U32.to_nat(U32.mod(index, 32)))

def from_read(n: U32, index: U32, pair: Array<U32> & U32) -> MineWords & Bool:
  (words, value) = pair
  (MineWords{n, words}, U32.is_ne(U32.and(value, bit(index)), 0))

def has_if_valid(valid: Bool, n: U32, words: Array<U32>, +index: U32) -> MineWords & Bool:
  match valid:
    case True{}:
      from_read(n, index, Array.get(U32, words, U32.div(index, 32)))
    case False{}:
      (MineWords{n, words}, False{})

def has(board: MineWords, +index: U32) -> MineWords & Bool:
  match board:
    case MineWords{n, words}:
      has_if_valid(Geo.valid_index(n, index), n, words, index)

def update_word(old: U32, index: U32, value: Bool) -> U32:
  match value:
    case True{}:
      U32.or(old, bit(index))
    case False{}:
      U32.and(old, U32.not(bit(index)))

def from_update(+index: U32, value: Bool, pair: Array<U32> & U32) -> Array<U32>:
  (words, old) = pair
  Array.set(U32, words, U32.div(index, 32), update_word(old, index, value))

def set_if_valid(valid: Bool, n: U32, words: Array<U32>, +index: U32, value: Bool) -> MineWords:
  match valid:
    case True{}:
      MineWords{n, from_update(index, value, Array.get(U32, words, U32.div(index, 32)))}
    case False{}:
      MineWords{n, words}

def set_checked(board: MineWords, +index: U32, +value: Bool) -> MineWords:
  match board:
    case MineWords{n, words}:
      set_if_valid(Geo.valid_index(n, index), n, words, index, value)

def read_bit(pair: MineWords & Bool) -> U32:
  (unused, present) = pair
  match present:
    case True{}:
      1
    case False{}:
      0

def main() -> U32:
  read_bit(has(set_checked(set_checked(new(10), 31, True{}), 32, True{}), 32))
