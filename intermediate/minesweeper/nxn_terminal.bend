# N x N terminal-state controller for the active one-cell engine (2 <= n <= 100).
# This is deliberately not a zero flood or a first-click-safe controller.
# The engine retains mine truth; public solvers must not import this module.
import Base
import ./nxn_mine_words.bend as Words
import ./nxn_step.bend as Step
import ./nxn_victory.bend as Victory

type State is Type:
  Playing{session: Step.Session}
  Won{session: Step.Session}
  Lost{session: Step.Session}

def new(board: Words.MineWords) -> State:
  Playing{Step.new(board)}

# Preserve the session resource while converting the low-level loss phase.
def from_step(session: Step.Session) -> State:
  match session:
    case Step.Session{n, mines, cells, phase}:
      match phase:
        case Step.Playing{}:
          Playing{Step.Session{n, mines, cells, Step.Playing{}}}
        case Step.Lost{}:
          Lost{Step.Session{n, mines, cells, Step.Lost{}}}

# A safe click can complete the game; a mined click has already become Lost.
# Inspect only the game-internal state, never the public-information solver.
def from_check(check: Victory.Check) -> State:
  match check:
    case Victory.Check{session, complete}:
      match complete:
        case True{}:
          Won{session}
        case False{}:
          from_step(session)

def click(state: State, +index: U32) -> State:
  match state:
    case Playing{session}:
      from_check(Victory.inspect(Step.click(session, index)))
    case Won{session}:
      Won{session}
    case Lost{session}:
      Lost{session}

# Flags do not open safe cells. A terminal state ignores every later input.
def mark(state: State, +index: U32) -> State:
  match state:
    case Playing{session}:
      from_step(Step.mark(session, index))
    case Won{session}:
      Won{session}
    case Lost{session}:
      Lost{session}

# 0xx=Playing, 1xx=Won, 2xx=Lost; xx is the visible square code.
# Inspection consumes the state, so use it only at the end of a test trace.
def snapshot(state: State, +index: U32) -> U32:
  match state:
    case Playing{session}:
      Step.snapshot(session, index)
    case Won{session}:
      (100 + Step.snapshot(session, index) : U32)
    case Lost{session}:
      Step.snapshot(session, index)

def main() -> U32:
  board = Words.set_checked(Words.new(2), 3, True{})
  game = click(click(click(new(board), 0), 1), 2)
  snapshot(game, 2)
