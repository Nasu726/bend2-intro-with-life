# Public-only observation of the N x N game after any operation.
# No MineWords or hidden truth appears in Observation or Seen.
# This is a data boundary for a future solver, NOT a solver itself.
import Base
import ./game.bend as Cell
import ./nxn_mine_words.bend as Words
import ./nxn_step.bend as Step
import ./nxn_terminal.bend as Terminal
import ./nxn_full_game.bend as Full

type Seen is Data:
  Open{index: U32, clue: U32}
  Flag{index: U32}

# Status 3=Fresh, 0=Playing, 1=Won, 2=Lost.
# Flags express player claims, not confirmed mines.
type Observation is Data:
  Observation{n: U32, status: U32, seen: List<&2, Seen>}

type Gather is Type:
  Gather{cells: Array<Cell.Square>, seen: List<&2, Seen>}

def add(+index: U32, square: Cell.Square, rest: List<&2, Seen>) -> List<&2, Seen>:
  match square:
    case Cell.Hidden{}:
      rest
    case Cell.Flag{}:
      Flag{index} <> rest
    case Cell.Open{clue}:
      Open{index, clue} <> rest

def after_read(+index: U32, rest: List<&2, Seen>,
               read: Array<Cell.Square> & Cell.Square) -> Gather:
  (cells, square) = read
  Gather{cells, add(index, square, rest)}

# Scan logical cells from last to first; prepend yields ascending indices.
# The Nat fuel decreases once per logical cell, never entering Array padding.
def collect(fuel: Nat, +index: U32, gathered: Gather) -> Gather:
  match fuel:
    case 0n:
      gathered
    case 1n+k:
      match gathered:
        case Gather{cells, seen}:
          collect(k, (index - 1 : U32),
                  after_read(index, seen, Array.get(Cell.Square, cells, index)))

# Bend matches a parameter, not a computed expression. Keep the result
# in a separate helper so the linear Array can be consumed exactly once.
def from_gather(+n: U32, +status: U32, gathered: Gather) -> Observation:
  match gathered:
    case Gather{cells, seen}:
      Observation{n, status, seen}

def build(+n: U32, +status: U32, cells: Array<Cell.Square>) -> Observation:
  from_gather(n, status,
              collect(U32.to_nat((n * n : U32)), (n * n - 1 : U32),
                      Gather{cells, Nil{}}))

# The internal mine words and Step phase are deliberately discarded.
def from_session(session: Step.Session, +status: U32) -> Observation:
  match session:
    case Step.Session{+n, mines, cells, phase}:
      build(n, status, cells)

def active(state: Terminal.State) -> Observation:
  match state:
    case Terminal.Playing{session}:
      from_session(session, 0)
    case Terminal.Won{session}:
      from_session(session, 1)
    case Terminal.Lost{session}:
      from_session(session, 2)

# Consumes the game: never exposes its internal mine words to the caller.
def observe(game: Full.Game) -> Observation:
  match game:
    case Full.Fresh{board}:
      match board:
        case Words.MineWords{n, words}:
          Observation{n, 3, Nil{}}
    case Full.Active{state}:
      active(state)

def count_seen(items: List<&2, Seen>) -> U32:
  match items:
    case Nil{}:
      0
    case item <> rest:
      (1 + count_seen(rest) : U32)

def count(observation: Observation) -> U32:
  match observation:
    case Observation{n, status, seen}:
      count_seen(seen)

def main() -> U32:
  board = Words.set_checked(Words.new(3), 8, True{})
  count(observe(Full.click(Full.new(board), 0)))
