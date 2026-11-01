import Base

# Split a configuration field into its key and value.
# Chr{61} is the '=' character.
def main() -> Nat:
  fields = String.split("board-size=4", Chr{61})
  List.length(&2, String, fields)
