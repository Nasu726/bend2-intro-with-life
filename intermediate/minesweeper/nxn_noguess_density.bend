# Quarter-density, public-audited no-guess N x N family (N=10..100).
# All 0 <= count <= floor(N*N/4), with any valid first click.
# Candidate truth is not given to a solver; see independent public-only tests.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words
import ./nxn_full_game.bend as Full

type Construction is Type:
  Candidate{board: Words.MineWords, first: U32, last: U32}
  Unsupported{}

def column_at(right: Bool, +n: U32, +offset: U32) -> U32:
  match right:
    case True{}:
      (n - 1 - offset : U32)
    case False{}:
      offset

def fill_rows(fuel: Nat, +n: U32, +column: U32, +row: U32,
              board: Words.MineWords) -> Words.MineWords:
  match fuel:
    case 0n:
      board
    case 1n+k:
      fill_rows(k, n, column, (row + 1 : U32),
                Words.set_checked(board, (row*n + column : U32), True{}))

def fill_columns(fuel: Nat, +n: U32, +right: Bool, +offset: U32,
                 board: Words.MineWords) -> Words.MineWords:
  match fuel:
    case 0n:
      board
    case 1n+k:
      fill_columns(k, n, right, (offset + 1 : U32),
                   fill_rows(U32.to_nat(n), n, column_at(right, n, offset),
                             0, board))

def build(+n: U32, +count: U32, +first: U32, +right: Bool) -> Construction:
  +whole = U32.div(count, n)
  +remainder = U32.mod(count, n)
  board = fill_columns(U32.to_nat(whole), n, right, 0, Words.new(n))
  partial = fill_rows(U32.to_nat(remainder), n,
                      column_at(right, n, whole), (n - remainder : U32), board)
  Candidate{partial, first, column_at(right, n, whole)}

def choose(+n: U32, +count: U32, +first: U32) -> Construction:
  build(n, count, first, U32.is_lt(U32.mod(first, n), U32.div(n, 2)))

def accept(valid: Bool, +n: U32, +count: U32, +first: U32) -> Construction:
  match valid:
    case True{}:
      choose(n, count, first)
    case False{}:
      Unsupported{}

def generate(+n: U32, +count: U32, +first: U32) -> Construction:
  accept(Bool.and(U32.is_lt(9, n),
         Bool.and(Geo.valid_index(n, first),
                  U32.is_lt(count, (U32.div((n*n : U32), 4) + 1 : U32)))),
         n, count, first)

# Truth-aware game demonstration only: not a solver certificate.
def demonstration(candidate: Construction) -> U32:
  match candidate:
    case Candidate{board, first, +last}:
      Full.snapshot(Full.click(Full.click(Full.new(board), first), last), last)
    case Unsupported{}:
      400

def main() -> U32:
  demonstration(generate(10, 25, 0))
