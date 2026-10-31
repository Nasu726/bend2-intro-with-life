# First-click-safe N x N game with terminal states (2 <= n <= 100).
# Zero flood is NOT implemented: each click opens at most one square.
# Keep mine truth inside the engine, never in a public-information solver.
import Base
import ./nxn_mine_words.bend as Words
import ./nxn_relocate.bend as Relocate
import ./nxn_terminal.bend as Terminal

type Game is Type:
  Fresh{board: Words.MineWords}
  Active{state: Terminal.State}

def new(board: Words.MineWords) -> Game:
  Fresh{board}

# Relocation can reject an invalid first click or a completely mined board.
# Otherwise the first click is evaluated by the same terminal controller as
# later clicks, so a one-safe-cell board can win on its very first move.
def after_relocation(result: Relocate.Relocation, +index: U32) -> Game:
  match result:
    case Relocate.FirstClickRejected{board}:
      Fresh{board}
    case Relocate.FirstClickSafe{board}:
      Active{Terminal.click(Terminal.new(board), index)}

def click(game: Game, +index: U32) -> Game:
  match game:
    case Fresh{board}:
      after_relocation(Relocate.relocate(board, index), index)
    case Active{state}:
      Active{Terminal.click(state, index)}

# A flag before the first click is ignored; after starting, terminal states
# already reject every further mark/click operation.
def mark(game: Game, +index: U32) -> Game:
  match game:
    case Fresh{board}:
      Fresh{board}
    case Active{state}:
      Active{Terminal.mark(state, index)}

# 300=Fresh; 0xx=Playing, 1xx=Won, 2xx=Lost.
# The two-digit suffix is the square code; 99 means invalid probe.
# This consumes the game and is only a finite-test inspection interface.
def snapshot(game: Game, +index: U32) -> U32:
  match game:
    case Fresh{board}:
      300
    case Active{state}:
      Terminal.snapshot(state, index)

def main() -> U32:
  board = Words.set_checked(Words.new(2), 3, True{})
  game = click(click(click(new(board), 0), 1), 2)
  snapshot(game, 2)
