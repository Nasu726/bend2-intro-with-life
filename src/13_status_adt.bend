import Base

# A custom type restricts the set of valid values.
type Status is Data:
  Idle{}
  Busy{}

def to_u32(status: Status) -> U32:
  match status:
    case Idle{}:
      0
    case Busy{}:
      1

def main() -> U32:
  to_u32(Busy{})
