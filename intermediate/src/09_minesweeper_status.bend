import Base

# The local rules are pure. A later chapter attaches them to a full board.
type Square is Data:
  Hidden{}
  Flag{}
  Revealed{nearby: U32}

def flip_flag(s: Square) -> Square:
  match s:
    case Hidden{}:
      Flag{}
    case Flag{}:
      Hidden{}
    case Revealed{count}:
      Revealed{count}

def is_flag(s: Square) -> U32:
  match s:
    case Flag{}:
      1
    case Hidden{}:
      0
    case Revealed{count}:
      0

def main() -> U32:
  is_flag(flip_flag(Hidden{}))
