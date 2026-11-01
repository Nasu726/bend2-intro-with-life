import Base

# Either represents one of two choices, rather than two simultaneous values.
def meaning(choice: Either<&2, &2, U32, String>) -> U32:
  match choice:
    case Inl{number}:
      number
    case Inr{text}:
      U32.from_nat(String.length(text))

def main() -> U32:
  meaning(Inl{7})
