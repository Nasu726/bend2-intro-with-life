import Base

# Unlike a proof for one input, this law covers EVERY Boolean value.
law not_twice:
  for b: Bool
  {Bool.not(Bool.not(b)) == b : Bool}

def not_twice(b):
  match b:
    case True{}:
      {==}
    case False{}:
      {==}

def main() -> U32:
  Bool.to_u32(Bool.not(Bool.not(True{})))
