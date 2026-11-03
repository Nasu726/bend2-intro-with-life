# Constructive N x N no-guess witness, N=10..100, any first cell.
# Exactly N-1 mines occupy an edge row except its rightmost corner.
# This is a guaranteed-solvable FAMILY, not arbitrary mine-count generation.
# Truth stays in the game engine. An independent public-only inference audit
# must certify the second click; knowing the layout is not itself inference.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words
import ./nxn_full_game.bend as Full

type Construction is Type:
  Candidate{board: Words.MineWords, first: U32, last: U32}
  Unsupported{}

# The fuel decreases at each step; only the N-1 cells at columns 0..N-2
# of the designated border row are mined.
def fill(fuel: Nat, +n: U32, +row: U32, +column: U32,
         board: Words.MineWords) -> Words.MineWords:
  match fuel:
    case 0n:
      board
    case 1n+k:
      fill(k, n, row, (column + 1 : U32),
           Words.set_checked(board, (row*n + column : U32), True{}))

def border(+n: U32, +row: U32) -> Words.MineWords:
  fill(U32.to_nat((n - 1 : U32)), n, row, 0, Words.new(n))

# Put the mined row on the side farthest from the selected first click.
# N>=10 ensures the first click is at least four rows from that edge.
def choose(bottom: Bool, +n: U32, +first: U32) -> Construction:
  match bottom:
    case True{}:
      Candidate{border(n, (n - 1 : U32)), first, (n*n - 1 : U32)}
    case False{}:
      Candidate{border(n, 0), first, (n - 1 : U32)}

def accepted(valid: Bool, +n: U32, +first: U32) -> Construction:
  match valid:
    case True{}:
      choose(U32.is_lt(U32.div(first, n), U32.div(n, 2)), n, first)
    case False{}:
      Unsupported{}

def generate(+n: U32, +first: U32) -> Construction:
  accepted(Bool.and(U32.is_lt(9, n), Geo.valid_index(n, first)), n, first)

# Demonstration only: generator-known last is clicked after the first zero
# flood. The public-only proof of last's safety is independently checked in
# test_nxn_noguess_constructive.py, not by this truth-aware routine.
def demonstration(candidate: Construction) -> U32:
  match candidate:
    case Candidate{board, first, +last}:
      Full.snapshot(Full.click(Full.click(Full.new(board), first), last), last)
    case Unsupported{}:
      400

def main() -> U32:
  demonstration(generate(10, 0))
