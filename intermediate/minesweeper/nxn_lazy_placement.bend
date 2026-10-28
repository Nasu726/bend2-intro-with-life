# Lazy mine placement: only called AFTER the first valid left click.
# Fresh must hold n, mine_count and seed, never MineWords.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words

type Placement is Type:
  LazyReady{board: Words.MineWords}
  LazyRejected{}

# Reproducible 32-bit LCG; not cryptographically secure.
def advance(+state: U32) -> U32:
  (1664525 * state + 1013904223 : U32)

def select(chosen: Bool, board: Words.MineWords, +pos: U32,
           +left: U32) -> Words.MineWords & U32:
  match chosen:
    case True{}:
      (Words.set_checked(board, pos, True{}), (left - 1 : U32))
    case False{}:
      (board, left)

# Sample exactly mine_count out of n*n-1 cells without replacement.
# The clicked cell is skipped before any RNG advance or mine assignment.
def fill(fuel: Nat, pair: Words.MineWords & U32, +clicked: U32,
         +pos: U32, +slots: U32, +rng: U32, skip: Bool) -> Words.MineWords:
  (board, left) = pair
  match fuel:
    case 0n:
      board
    case 1n+k:
      match skip:
        case True{}:
          fill(k, (board, left), clicked, (pos + 1 : U32),
               slots, rng, U32.is_eq((pos + 1 : U32), clicked))
        case False{}:
          fill(k, select(U32.is_lt(U32.mod(advance(rng), slots), left),
                         board, pos, left),
               clicked, (pos + 1 : U32), (slots - 1 : U32),
               advance(rng), U32.is_eq((pos + 1 : U32), clicked))

def if_valid(valid: Bool, +n: U32, +mine_count: U32,
             +seed: U32, +clicked: U32) -> Placement:
  match valid:
    case False{}:
      LazyRejected{}
    case True{}:
      LazyLazyReady{fill(U32.to_nat((n * n : U32)), (Words.new(n), mine_count),
                     clicked, 0, (n * n - 1 : U32), seed, U32.is_eq(0, clicked))}

def place(+n: U32, +mine_count: U32, +seed: U32,
          +clicked: U32) -> Placement:
  if_valid(Bool.and(Geo.valid_index(n, clicked),
                    U32.is_lt(mine_count, (n * n : U32))),
           n, mine_count, seed, clicked)

# Internal finite-test inspection only. Never pass mine truth to a solver.
def bit_code(present: Bool) -> U32:
  match present:
    case True{}:
      1
    case False{}:
      0

def inspect(result: Placement, +probe: U32) -> U32:
  match result:
    case LazyRejected{}:
      2
    case LazyReady{board}:
      (unused, present) = Words.has(board, probe)
      bit_code(present)

def main() -> U32:
  inspect(place(2, 3, 0, 0), 0)
