import Base

# General-purpose conditional choice; no Life-specific rules.
def choose(flag: Bool, first: U32, second: U32) -> U32:
  match flag:
    case True{}:
      first
    case False{}:
      second

def main() -> U32:
  choose(True{}, 10, 20)
