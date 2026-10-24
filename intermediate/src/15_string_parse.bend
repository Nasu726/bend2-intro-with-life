import Base

# String.read-like conversion can fail. Whitespace is removed first.
def parsed_number(value: Maybe<&2, U32>) -> U32:
  match value:
    case Some{n}:
      n
    case None{}:
      0

def main() -> U32:
  cleaned = String.trim(" 42 ")
  parsed_number(U32.read(cleaned))
