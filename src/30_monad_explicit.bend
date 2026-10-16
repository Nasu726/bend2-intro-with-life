import Base

# Expanded form of the do-notation example.
def add_strs_explicit(a: String, b: String) -> Maybe<&2, U32>:
  Maybe.bind(&2, U32, U32, U32.read(a), x =>
    Maybe.bind(&2, U32, U32, U32.read(b), y =>
      Maybe.pure(&2, U32, (x + y : U32))))

def main() -> Maybe<&2, U32>:
  add_strs_explicit("40", "2")
