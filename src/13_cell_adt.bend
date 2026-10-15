import Base

# An ADT forbids invalid cell values by construction.
type Cell is Data:
  Dead{}
  Alive{}

def to_u32(c: Cell) -> U32:
  match c:
    case Dead{}:
      0
    case Alive{}:
      1

def main() -> U32:
  to_u32(Alive{})
