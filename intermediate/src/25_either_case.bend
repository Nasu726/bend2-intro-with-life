import Base

# Either represents one of two choices, rather than two simultaneous values.
def meaning(choice: Either<&2, &2, U32, String>) -> U32:
  match choice:
    case Inl{number}:
      number
    case Inr{text}:
      String.length(text) |> Nat.to_u32

def main() -> U32:
  meaning(Inl{7})
