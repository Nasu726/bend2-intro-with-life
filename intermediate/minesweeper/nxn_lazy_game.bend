# First-click-generated N x N ordinary game (not no-guess certified).
# Fresh stores configuration, never mine truth. Fixed-board full_game is test-only.
import Base
import ./nxn_geometry.bend as Geo
import ./nxn_mine_words.bend as Words
import ./nxn_step.bend as Step
import ./nxn_flood.bend as Flood
import ./nxn_victory.bend as Victory
import ./nxn_terminal.bend as Terminal

type Game is Type:
  Fresh{n: U32, count: U32, seed: U32}
  Active{state: Terminal.State}
  Invalid{}

def new_if_valid(valid: Bool, +n: U32, +count: U32, +seed: U32) -> Game:
  match valid:
    case True{}:
      Fresh{n, count, seed}
    case False{}:
      Invalid{}

def new(+n: U32, +count: U32, +seed: U32) -> Game:
  new_if_valid(Bool.and(Geo.valid_size(n), U32.is_lt(count, (n*n : U32))), n, count, seed)

# Valid inputs: 2 <= n <= 100, 0 <= count < n*n, clicked < n*n.
# Euclidean gcd has <= 20 steps for inputs <= 9999.
def gcd(fuel: Nat, +a: U32, +b: U32, done: Bool) -> U32:
  match fuel:
    case 0n:
      a
    case 1n+k:
      match done:
        case True{}:
          a
        case False{}:
          +r = U32.mod(a, b)
          gcd(k, b, r, U32.is_eq(r, 0))

# A relatively prime step visits all positions in [0,m) without repetition.
def choose_step(fuel: Nat, +candidate: U32, +m: U32, good: Bool) -> U32:
  match fuel:
    case 0n:
      1
    case 1n+k:
      match good:
        case True{}:
          candidate
        case False{}:
          +next = (U32.mod(candidate, (m - 1 : U32)) + 1 : U32)
          choose_step(k, next, m,
                      U32.is_eq(gcd(20n, next, m, False{}), 1))

def skip_clicked(before: Bool, +item: U32) -> U32:
  match before:
    case True{}:
      item
    case False{}:
      (item + 1 : U32)

# All indices exclude the first clicked square. The board is allocated here,
# never in Fresh. Exactly count distinct mines are placed.
def scatter(fuel: Nat, +i: U32, +m: U32, +stride: U32,
            +offset: U32, +clicked: U32, board: Words.MineWords) -> Words.MineWords:
  match fuel:
    case 0n:
      board
    case 1n+k:
      +compressed = U32.mod((offset + i*stride : U32), m)
      cell = skip_clicked(U32.is_lt(compressed, clicked), compressed)
      scatter(k, (i + 1 : U32), m, stride, offset, clicked,
              Words.set_checked(board, cell, True{}))

# Reproducible permutation for teaching, not uniform RNG or no-guess proof.
def generate(+n: U32, +count: U32, +seed: U32, +clicked: U32) -> Words.MineWords:
  +m = (n*n - 1 : U32)
  +first_step = (1 + U32.mod(U32.xor(seed, 2654435769), (m - 1 : U32)) : U32)
  stride = choose_step(64n, first_step, m,
                       U32.is_eq(gcd(20n, first_step, m, False{}), 1))
  offset = U32.mod(U32.xor(seed, 2246822507), m)
  scatter(U32.to_nat(count), 0, m, stride, offset, clicked, Words.new(n))

def begin_if_valid(valid: Bool, +n: U32, +count: U32, +seed: U32,
                   +clicked: U32) -> Game:
  match valid:
    case False{}:
      Fresh{n, count, seed}
    case True{}:
      board = generate(n, count, seed, clicked)
      Active{Terminal.from_check(Victory.inspect(Flood.reveal(Step.new(board), clicked)))}

def active_click(state: Terminal.State, +index: U32) -> Game:
  match state:
    case Terminal.Playing{session}:
      Active{Terminal.from_check(Victory.inspect(Flood.reveal(session, index)))}
    case Terminal.Won{session}:
      Active{Terminal.Won{session}}
    case Terminal.Lost{session}:
      Active{Terminal.Lost{session}}

def click(game: Game, +index: U32) -> Game:
  match game:
    case Fresh{+n, count, seed}:
      begin_if_valid(Geo.valid_index(n, index), n, count, seed, index)
    case Active{state}:
      active_click(state, index)
    case Invalid{}:
      Invalid{}

def mark(game: Game, +index: U32) -> Game:
  match game:
    case Fresh{n, count, seed}:
      Fresh{n, count, seed}
    case Active{state}:
      Active{Terminal.mark(state, index)}
    case Invalid{}:
      Invalid{}

# 300=Fresh, 400=Invalid, 0xx=Playing, 1xx=Won, 2xx=Lost.
def snapshot(game: Game, +index: U32) -> U32:
  match game:
    case Fresh{n, count, seed}:
      300
    case Active{state}:
      Terminal.snapshot(state, index)
    case Invalid{}:
      400

def main() -> U32:
  snapshot(click(new(10, 10, 20261028), 0), 0)
