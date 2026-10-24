# First implementation milestone: pure visible state of ONE Minesweeper cell.
# Requirements live in LAWS.bend and are intentionally separate from this file.
# A full board, mine placement, click coordinates and zero expansion come later.
import Base

type Square is Data:
  Hidden{}
  Flag{}
  Open{clue: U32}

def toggle_flag(square: Square) -> Square:
  match square:
    case Hidden{}:
      Flag{}
    case Flag{}:
      Hidden{}
    case Open{clue}:
      Open{clue}

# Called only after the board engine has determined the clicked cell is safe.
# It must NOT be used to implement "reveal a mine".
def reveal_safe(square: Square, clue: U32) -> Square:
  match square:
    case Hidden{}:
      Open{clue}
    case Flag{}:
      Flag{}
    case Open{old_clue}:
      Open{old_clue}

def flagged(square: Square) -> U32:
  match square:
    case Hidden{}:
      0
    case Flag{}:
      1
    case Open{clue}:
      0

def main() -> U32:
  flagged(toggle_flag(Hidden{}))
