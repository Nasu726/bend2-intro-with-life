import Base

# First, test the rule on a board with one bit for each mine and flag.
# The least significant bit is the top-left square on our 4x4 board.
type MiniBoard is Data:
  MiniBoard{mines: U32, flags: U32}

def mines_of(b: MiniBoard) -> U32:
  match b:
    case MiniBoard{mines, flags}:
      mines

def flags_of(b: MiniBoard) -> U32:
  match b:
    case MiniBoard{mines, flags}:
      flags

# Change only the first flag bit. The mines field passes through unchanged.
def toggle_first(b: MiniBoard) -> MiniBoard:
  match b:
    case MiniBoard{mines, flags}:
      MiniBoard{mines, U32.xor(flags, 1)}

law toggle_keeps_mines:
  for mines: U32
  for flags: U32
  {mines_of(toggle_first(MiniBoard{mines, flags})) == mines : U32}

def toggle_keeps_mines(mines, flags):
  {==}

# Mine invariance alone would allow a no-op! Also demand a real flag change.
law toggle_changes_flag:
  for mines: U32
  for flags: U32
  {flags_of(toggle_first(MiniBoard{mines, flags})) == U32.xor(flags, 1) : U32}

def toggle_changes_flag(mines, flags):
  {==}

def main() -> U32:
  flags_of(toggle_first(MiniBoard{5, 0}))
