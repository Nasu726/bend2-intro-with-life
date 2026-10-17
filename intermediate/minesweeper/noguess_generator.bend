# Fully checked no-guess generator for a *fixed* 4x4 board with exactly
# two mines. Deterministically searches candidate pairs, skipping all masks
# touching the 0-corner or its neighbors; only successful games are returned.
#
# Crucially, PublicSolver receives opened clues ONLY; it never sees the true
# mine mask. The generator is allowed to know it, to simulate the board.
# A certificate is an actual sequence of safe clicks ending with Session.Won.
#
# The bounded search (<= 120 two-mine masks, <= 16 safe moves per mask)
# terminates even when no accepted board exists.
import Base
import ./game.bend as Game
import ./board4.bend as Board4
import ./session.bend as Session
import ./public_solver.bend as Solver

type Certified is Data:
  Certified{mines: U32, trace: List<&2, U32>}

# Convert ONLY visible squares to the public information type.
def opened_numbers(cells: List<Game.Square>, +index: U32) ->
  List<&2, Solver.Number>:
  match cells:
    case Nil{}:
      Nil{}
    case square <> rest:
      match square:
        case Game.Open{clue}:
          Solver.Number{index, clue} <> opened_numbers(rest, (index + 1 : U32))
        case _:
          opened_numbers(rest, (index + 1 : U32))

# Array.clone keeps the live board, while extracting its public projection.
def from_clone(mines: U32, pair: Array<Game.Square> & Array<Game.Square>) ->
  Board4.State & Solver.Public:
  (keep, seen) = pair
  (Board4.State{mines, keep},
   Solver.Public{opened_numbers(Array.to_list(Game.Square, seen), 0)})

def inspect_board(board: Board4.State) -> Board4.State & Solver.Public:
  match board:
    case Board4.State{mines, cells}:
      from_clone(mines, Array.clone(Game.Square, cells))

# log2 of a nonzero isolated lowest bit gives its 0-based index.
def first_bit(+bits: U32) -> U32:
  U32.from_nat(U32.log2(U32.and(bits, U32.sub(0, bits))))

def index_if_nonzero(zero: Bool, bits: U32) -> Maybe<&2, U32>:
  match zero:
    case True{}:
      None{}
    case False{}:
      Some{first_bit(bits)}

def candidate_index(safe: Maybe<&2, U32>) -> Maybe<&2, U32>:
  match safe:
    case None{}:
      None{}
    case Some{bits}:
      index_if_nonzero(U32.is_eq(bits, 0), bits)

# Continuation avoids destructuring an expression: only parameter
# pairs are destructured by Bend's structural checker.
def step_from_public(pair: Board4.State & Solver.Public,
                     trace: List<&2, U32>,
                     resume: Session.Session -> List<&2, U32> ->
                       Maybe<&2, List<&2, U32>>) -> Maybe<&2, List<&2, U32>>:
  (keep, visible) = pair
  Maybe.bind(&2, U32, List<&2, U32>,
    candidate_index(Solver.provably_safe(visible)),
    move => resume(
      Session.click(Session.Session{keep, Session.Playing{}}, move),
      move <> trace))

# Every recursive call strictly decreases fuel, while the live
# Session/trace are permitted to change.
def continue_play(fuel: Nat, session: Session.Session,
                  trace: List<&2, U32>) -> Maybe<&2, List<&2, U32>>:
  match fuel:
    case 0n:
      None{}
    case 1n+k:
      match session:
        case Session.Session{board, phase}:
          match phase:
            case Session.Won{}:
              Some{List.reverse(&2, U32, trace)}
            case Session.Lost{}:
              None{}
            case Session.Playing{}:
              step_from_public(inspect_board(board), trace,
                next_session => next_trace =>
                  continue_play(k, next_session, next_trace))

def enough_moves(trace: List<&2, U32>, +mask: U32) -> Maybe<&2, Certified>:
  match trace:
    case first <> second <> rest:
      Some{Certified{mask, first <> second <> rest}}
    case _:
      None{}

def result_if_solved(result: Maybe<&2, List<&2, U32>>, mask: U32) ->
  Maybe<&2, Certified>:
  match result:
    case None{}:
      None{}
    case Some{trace}:
      enough_moves(trace, mask)

def verified_mask(+mask: U32) -> Maybe<&2, Certified>:
  # Zero opening at index 0 is guaranteed by excluding 0,1,4,5.
  # The game engine, not the solver, uses the actual mine locations.
  stage = Session.click(Session.new(mask), 0)
  result_if_solved(continue_play(16n, stage, [0]), mask)

def choose_if_valid(valid: Bool, mask: U32) -> Maybe<&2, Certified>:
  match valid:
    case True{}:
      verified_mask(mask)
    case False{}:
      None{}

def consider(+i: U32, +j: U32) -> Maybe<&2, Certified>:
  +mask = U32.or(U32.shln(1, U32.to_nat(i)),
                U32.shln(1, U32.to_nat(j)))
  allowed = Bool.and(U32.is_lt(i, j),
    U32.is_eq(U32.and(mask, 51), 0))
  choose_if_valid(allowed, mask)

def prefer(current: Maybe<&2, Certified>, fallback: Unit -> Maybe<&2, Certified>) ->
  Maybe<&2, Certified>:
  match current:
    case Some{certificate}:
      Some{certificate}
    case None{}:
      fallback(Unit{})

def search_columns(fuel: Nat, +i: U32) -> Maybe<&2, Certified>:
  match fuel:
    case 0n:
      None{}
    case 1n+k:
      +j = U32.from_nat(k)
      prefer(consider(i, j), unused => search_columns(k, i))

def search_rows(fuel: Nat) -> Maybe<&2, Certified>:
  match fuel:
    case 0n:
      None{}
    case 1n+k:
      prefer(search_columns(16n, U32.from_nat(k)), unused => search_rows(k))

def generate() -> Maybe<&2, Certified>:
  search_rows(16n)

def result_text(certificate: Maybe<&2, Certified>) -> String:
  match certificate:
    case None{}:
      "NO VERIFIED BOARD"
    case Some{Certified{mines, trace}}:
      "mines=" ++ U32.show(mines) ++ ";moves=" ++
      String.join(List.map(~U32, ~String, i => U32.show(i), trace), ",")

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(result_text(generate()))
