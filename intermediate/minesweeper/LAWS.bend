# Requirements are maintained independently of the engine and its proofs.
# The first milestone specifies only the public state of one cell.
# Do not weaken these statements merely to make an implementation pass.
import Base
import ./game.bend as Game
import ./board.bend as Board

# C-01: A hidden cell acquires a flag.
law hidden_is_flagged:
  {Game.toggle_flag(Game.Hidden{}) == Game.Flag{} : Game.Square}

# C-02: Clicking an existing flag removes it.
law flagged_is_hidden:
  {Game.toggle_flag(Game.Flag{}) == Game.Hidden{} : Game.Square}

# C-03: An opened cell remains opened with its original clue.
law opened_ignores_flag:
  for clue: U32
  {Game.toggle_flag(Game.Open{clue}) == Game.Open{clue} : Game.Square}

# C-04: Two flag toggles restore any visible cell, even an open cell.
# This is a useful consequence, but insufficient without C-01 and C-02.
law flag_toggle_involution:
  for s: Game.Square
  {Game.toggle_flag(Game.toggle_flag(s)) == s : Game.Square}

# C-05: Revealing an unflagged hidden safe square displays its clue.
law reveal_hidden:
  for clue: U32
  {Game.reveal_safe(Game.Hidden{}, clue) == Game.Open{clue} : Game.Square}

# C-06: Revealing a flagged square does not silently remove the flag.
law reveal_flagged:
  for clue: U32
  {Game.reveal_safe(Game.Flag{}, clue) == Game.Flag{} : Game.Square}

# C-07: Re-revealing an open square must preserve the OLD clue.
law reveal_opened:
  for old_clue: U32
  for new_clue: U32
  {Game.reveal_safe(Game.Open{old_clue}, new_clue) == Game.Open{old_clue} : Game.Square}

# B-01: This is a finite 4x4 board, NOT the toroidal Life board.
# A cell immediately to the right (or diagonally next to a cell) is adjacent.
# Opposite corners are NOT adjacent, nor are out-of-board coordinates.
law board_top_edge_adjacent:
  {Board.neighbor(0, 0, 1, 0) == True{} : Bool}

law board_corner_diagonal:
  {Board.neighbor(0, 0, 1, 1) == True{} : Bool}

law board_no_wrap:
  {Board.neighbor(0, 0, 3, 3) == False{} : Bool}

law board_no_self_neighbor:
  {Board.neighbor(2, 2, 2, 2) == False{} : Bool}

law board_outside_x:
  for y: U32
  {Board.in_bounds(4, y) == False{} : Bool}

# B-02: Mine truth must survive both allowed single-cell operations.
law board_toggle_keeps_mine:
  for mine: Bool
  for s: Game.Square
  {Board.mine_of(Board.toggle(Board.Cell{mine, s})) == mine : Bool}

law board_safe_reveal_keeps_mine:
  for mine: Bool
  for s: Game.Square
  for clue: U32
  {Board.mine_of(Board.reveal(Board.Cell{mine, s}, clue)) == mine : Bool}

# B-03: For one cell, an already revealed clue is never withdrawn or changed.
# The stronger whole-board subset invariant is still outstanding.
law board_reveal_monotone_on_open:
  for mine: Bool
  for old_clue: U32
  for new_clue: U32
  {Board.visible_of(Board.reveal(Board.Cell{mine, Game.Open{old_clue}}, new_clue)) == Game.Open{old_clue} : Game.Square}

# B-05 (single cell): Flagged cells are not opened by a safe reveal.
law board_safe_reveal_keeps_flag:
  for mine: Bool
  for clue: U32
  {Board.visible_of(Board.reveal(Board.Cell{mine, Game.Flag{}}, clue)) == Game.Flag{} : Game.Square}
