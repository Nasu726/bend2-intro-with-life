# First-click mine relocation for N x N boards (2 <= N <= 100).
# This is a board-only primitive, not a full Fresh/Active game controller.
# Never expose the returned mine positions to a public-information solver.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words

type Relocation is Type:
  FirstClickSafe{board: Words.MineWords}
  FirstClickRejected{board: Words.MineWords}

# Scan exactly the logical cells in ascending index order.
# The Nat fuel proves termination, including on a completely mined board.
def first_free(fuel: Nat, +pos: U32, pair: Words.MineWords & Bool) -> Words.MineWords & Maybe<&2, U32>:
  match fuel:
    case 0n:
      (board, mined) = pair
      match mined:
        case False{}:
          (board, Some{pos})
        case True{}:
          (board, None{})
    case 1n+k:
      (board, mined) = pair
      match mined:
        case False{}:
          (board, Some{pos})
        case True{}:
          first_free(k, (pos + 1 : U32), Words.has(board, (pos + 1 : U32)))

def finish_move(+clicked: U32, pair: Words.MineWords & Maybe<&2, U32>) -> Relocation:
  (board, destination) = pair
  match destination:
    case None{}:
      FirstClickRejected{board}
    case Some{index}:
      cleared = Words.set_checked(board, clicked, False{})
      FirstClickSafe{Words.set_checked(cleared, index, True{})}

def if_mined(mined: Bool, board: Words.MineWords, +n: U32, +clicked: U32) -> Relocation:
  match mined:
    case False{}:
      FirstClickSafe{board}
    case True{}:
      finish_move(clicked, first_free(U32.to_nat((n * n - 1 : U32)), 0, Words.has(board, 0)))

def from_probe(+n: U32, +clicked: U32, pair: Words.MineWords & Bool) -> Relocation:
  (board, mined) = pair
  if_mined(mined, board, n, clicked)

def if_valid(valid: Bool, board: Words.MineWords, +n: U32, +clicked: U32) -> Relocation:
  match valid:
    case False{}:
      FirstClickRejected{board}
    case True{}:
      from_probe(n, clicked, Words.has(board, clicked))

# Invalid logical indices (including Array padding) are rejected.
# The caller must use a checked Words.new_checked result for untrusted N.
def relocate(board: Words.MineWords, +clicked: U32) -> Relocation:
  match board:
    case Words.MineWords{+n, words}:
      if_valid(Geo.valid_index(n, clicked), Words.MineWords{n, words}, n, clicked)

# Inspection for finite differential tests; 0/1 = Ready and 2/3 = Rejected.
def bit_code(pair: Words.MineWords & Bool) -> U32:
  (board, present) = pair
  match present:
    case True{}:
      1
    case False{}:
      0

def inspect(result: Relocation, +probe: U32) -> U32:
  match result:
    case FirstClickSafe{board}:
      bit_code(Words.has(board, probe))
    case FirstClickRejected{board}:
      (2 + bit_code(Words.has(board, probe)) : U32)

def main() -> U32:
  inspect(relocate(Words.set_checked(Words.new(10), 0, True{}), 0), 1)
