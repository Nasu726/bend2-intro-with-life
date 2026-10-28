# Player-facing Fresh has NO precomputed mine board.
# The prebuilt-board nxn_full_game.bend remains a low-level fixture.
import Base
import ./nxn_lazy_placement.bend as Placement
import ./nxn_step.bend as Step
import ./nxn_flood.bend as Flood
import ./nxn_victory.bend as Victory
import ./nxn_terminal.bend as Terminal

type Game is Type:
  Fresh{n: U32, mine_count: U32, seed: U32}
  Active{state: Terminal.State}

def new(+n: U32, +mine_count: U32, +seed: U32) -> Game:
  Fresh{n, mine_count, seed}

def finish(session: Step.Session) -> Terminal.State:
  Terminal.from_check(Victory.inspect(session))

def begin(result: Placement.Placement, +n: U32, +mine_count: U32,
          +seed: U32, +clicked: U32) -> Game:
  match result:
    case Placement.Invalid{}:
      Fresh{n, mine_count, seed}
    case Placement.Ready{board}:
      Active{finish(Flood.reveal(Step.new(board), clicked))}

def active_click(state: Terminal.State, +index: U32) -> Game:
  match state:
    case Terminal.Playing{session}:
      Active{finish(Flood.reveal(session, index))}
    case Terminal.Won{session}:
      Active{Terminal.Won{session}}
    case Terminal.Lost{session}:
      Active{Terminal.Lost{session}}

def click(game: Game, +index: U32) -> Game:
  match game:
    case Fresh{n, mine_count, seed}:
      begin(Placement.place(n, mine_count, seed, index),
            n, mine_count, seed, index)
    case Active{state}:
      active_click(state, index)

# Pre-start flags are ignored; they do not trigger placement.
def mark(game: Game, +index: U32) -> Game:
  match game:
    case Fresh{n, mine_count, seed}:
      Fresh{n, mine_count, seed}
    case Active{state}:
      Active{Terminal.mark(state, index)}

# 300=Fresh; 0xx=Playing; 1xx=Won; 2xx=Lost.
def snapshot(game: Game, +index: U32) -> U32:
  match game:
    case Fresh{n, mine_count, seed}:
      300
    case Active{state}:
      Terminal.snapshot(state, index)

def main() -> U32:
  snapshot(click(new(2, 3, 0), 0), 0)
