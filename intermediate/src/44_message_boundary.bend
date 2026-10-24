import Base

# A message delimiter is different from a TCP recv boundary.
# This example receives an already complete string: it does not
# open a socket or buffer partial messages.
# Chr{124} is '|', the delimiter between two messages.

def main() -> Nat:
  messages = String.split("ABC|DEF", Chr{124})
  List.length(&2, String, messages)
