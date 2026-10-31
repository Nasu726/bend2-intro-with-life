import Base

# Reject flagging an already revealed square.
# This is a pure game-rule failure, not an IO error.
type Cell is Data:
  Hidden{}
  Flag{}
  Open{}

def flag(s: Cell) -> Result<&2, &2, String, Cell>:
  match s:
    case Hidden{}:
      Done{Flag{}}
    case Flag{}:
      Done{Flag{}}
    case Open{}:
      Fail{"an open square cannot be flagged"}

def success(r: Result<&2, &2, String, Cell>) -> U32:
  match r:
    case Done{cell}:
      1
    case Fail{reason}:
      0

law hidden_can_be_flagged:
  {flag(Hidden{}) == Done{Flag{}} : Result<&2, &2, String, Cell>}

def hidden_can_be_flagged():
  {==}

def main() -> U32:
  a = success(flag(Hidden{}))
  b = success(flag(Open{}))
  (a + b : U32)
