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
def inspect_board(board: Board4.State) -> Board4.State & Solver.Public:
  match board:
    case Board4.State{mines, cells}:
      (keep, seen) = Array.clone(Game.Square, cells)
      (Board4.State{mines, keep},
       Solver.Public{opened_numbers(Array.to_list(Game.Square, seen), 0)})

def safe_move_or_stop(bits: U32, session: Session.Session,
                      trace: List<&2, U32>, fuel: Nat) ->
                      Maybe<&2, List<&2, U32>>:
  match U32.is_eq(bits, 0):
    case True{}:
      None{}
    case False{}:
      # Index of lowest set bit, i.e., the first proven-safe hidden cell.
      move = first_bit(16n, bits, 0)
      continue_play(fuel, Session.click(session, move), move <> trace)

def first_bit(fuel: Nat, +bits: U32, +index: U32) -> U32:
  match fuel:
    case 0n:
      16
    case 1n+k:
      match Board4.bit_is_set(bits, U32.shln(1, U32.to_nat(index))):
        case True{}:
          index
        case False{}:
          first_bit(k, bits, (index + 1 : U32))

def choose_public(next: Maybe<&2, U32>, session: Session.Session,
                  trace: List<&2, U32>, fuel: Nat) ->
                  Maybe<&2, List<&2, U32>>:
  match next:
    case None{}:
      None{}
    case Some{safe}:
      safe_move_or_stop(safe, session, trace, fuel)

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
              (keep, visible) = inspect_board(board)
              choose_public(Solver.provably_safe(visible),
                Session.Session{keep, Session.Playing{}}, trace, k)

def enough_moves(trace: List<&2, U32>, +mask: U32) -> Maybe<&2, Certified>:
  match trace:
    case first <> second <> rest:
      Some{Certified{mask, trace}}
    case _:
      None{}

def verified_mask(+mask: U32) -> Maybe<&2, Certified>:
  # Zero opening at index 0 is guaranteed by excluding 0,1,4,5.
  # The game engine, not the solver, uses the actual mine locations.
  stage = Session.click(Session.new(mask), 0)
  match continue_play(16n, stage, [0]):
    case None{}:
      None{}
    case Some{trace}:
      enough_moves(trace, mask)

def choose_if_valid(valid: Bool, mask: U32) -> Maybe<&2, Certified>:
  match valid:
    case True{}:
      verified_mask(mask)
    case False{}:
      None{}

def consider(+i: U32, +j: U32) -> Maybe<&2, Certified>:
  mask = U32.or(U32.shln(1, U32.to_nat(i)),
                U32.shln(1, U32.to_nat(j)))
  allowed = Bool.and(U32.is_lt(i, j),
    U32.is_eq(U32.and(mask, 51), 0))
  choose_if_valid(allowed, mask)

def search_columns(fuel: Nat, +i: U32) -> Maybe<&2, Certified>:
  match fuel:
    case 0n:
      None{}
    case 1n+k:
      +j = U32.from_nat(k)
      match consider(i, j):
        case Some{certificate}:
          Some{certificate}
        case None{}:
          search_columns(k, i)

def search_rows(fuel: Nat) -> Maybe<&2, Certified>:
  match fuel:
    case 0n:
      None{}
    case 1n+k:
      match search_columns(16n, U32.from_nat(k)):
        case Some{certificate}:
          Some{certificate}
        case None{}:
          search_rows(k)

def generate() -> Maybe<&2, Certified>:
  search_rows(16n)

def result_text(certificate: Maybe<&2, Certified>) -> String:
  match certificate:
    case None{}:
      "NO VERIFIED BOARD"
    case Some{Certified{mines, trace}}:
      "mines=" ++ U32.show(mines) ++ ";moves=" ++
      String.join(List.map(&2, U32, String,
        i => U32.show(i), trace), ",")

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(result_text(generate()))
