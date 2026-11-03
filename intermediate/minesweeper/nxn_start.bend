# Fresh -> active first-click controller for N x N (2 <= N <= 100).
# Deliberately one-cell only: no zero flood, victory, GUI or no-guess solver.
# Mine truth stays inside this controller and the game engine.
import Base
import ./nxn_mine_words.bend as Words
import ./nxn_relocate.bend as Relocate
import ./nxn_step.bend as Step

type Stage is Type:
  Fresh{board: Words.MineWords}
  Active{session: Step.Session}

def new(board: Words.MineWords) -> Stage:
  Fresh{board}

# A rejected first click does not consume the chance to start.
# Successful relocation is followed by exactly one active-board click.
def after_relocation(result: Relocate.Relocation, +index: U32) -> Stage:
  match result:
    case Relocate.FirstClickRejected{board}:
      Fresh{board}
    case Relocate.FirstClickSafe{board}:
      Active{Step.click(Step.new(board), index)}

def click(stage: Stage, +index: U32) -> Stage:
  match stage:
    case Fresh{board}:
      after_relocation(Relocate.relocate(board, index), index)
    case Active{session}:
      Active{Step.click(session, index)}

# The first LEFT click starts the game; pre-start flags are not retained.
def mark(stage: Stage, +index: U32) -> Stage:
  match stage:
    case Fresh{board}:
      Fresh{board}
    case Active{session}:
      Active{Step.mark(session, index)}

# Inspection for finite tests, not a public-information solver interface.
# 300=Fresh, 0xx=Playing, 2xx=Lost; xx is Step's visible cell code.
def snapshot(stage: Stage, +index: U32) -> U32:
  match stage:
    case Fresh{board}:
      300
    case Active{session}:
      Step.snapshot(session, index)

def main() -> U32:
  snapshot(click(new(Words.set_checked(Words.new(10), 0, True{})), 0), 0)
