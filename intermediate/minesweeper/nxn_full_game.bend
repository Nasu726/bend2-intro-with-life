# N x N playable core: first-click relocation, zero cascade and terminal state.
# N=2..100. GUI and public-information solver are separate tasks.
# Keep mine truth inside the engine, not in a public solver.
import Base
import ./nxn_mine_words.bend as Words
import ./nxn_relocate.bend as Relocate
import ./nxn_step.bend as Step
import ./nxn_flood.bend as Flood
import ./nxn_victory.bend as Victory
import ./nxn_terminal.bend as Terminal

type Game is Type:
  Fresh{board: Words.MineWords}
  Active{state: Terminal.State}

def new(board: Words.MineWords) -> Game:
  Fresh{board}

# Inspect victory only after the entire zero region is revealed.
def finish(session: Step.Session) -> Terminal.State:
  Terminal.from_check(Victory.inspect(session))

def after_relocation(result: Relocate.Relocation, +index: U32) -> Game:
  match result:
    case Relocate.FirstClickRejected{board}:
      Fresh{board}
    case Relocate.FirstClickSafe{board}:
      Active{finish(Flood.reveal(Step.new(board), index))}

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
    case Fresh{board}:
      after_relocation(Relocate.relocate(board, index), index)
    case Active{state}:
      active_click(state, index)

# Flags are disabled before the first click and after game over.
def mark(game: Game, +index: U32) -> Game:
  match game:
    case Fresh{board}:
      Fresh{board}
    case Active{state}:
      Active{Terminal.mark(state, index)}

# 300=Fresh; 0xx=Playing, 1xx=Won, 2xx=Lost.
# xx is a square code; 99 means an invalid probe. Consumes game.
def snapshot(game: Game, +index: U32) -> U32:
  match game:
    case Fresh{board}:
      300
    case Active{state}:
      Terminal.snapshot(state, index)

def main() -> U32:
  game = click(new(Words.new(2)), 0)
  snapshot(game, 3)
