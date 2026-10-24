# Requirements are maintained independently of the engine and its proofs.
# The first milestone specifies only the public state of one cell.
# Do not weaken these statements merely to make an implementation pass.
import Base
import ./game.bend as Game
import ./board.bend as Board
import ./board4.bend as Board4
import ./session.bend as Session
import ./start.bend as Start

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

# B-02 (whole board): a visible-state edit must preserve ALL 16 mine bits.
# A State is a dense 16-cell Array plus the U32 mine mask.
# The index can be arbitrary here: Array's out-of-range behavior is a
# separate input-validation obligation, and does not weaken this invariant.
law board4_toggle_keeps_all_mines:
  for mines: U32
  for cells: Array<Game.Square>
  for index: U32
  {Board4.mine_mask(Board4.toggle_at(Board4.State{mines, cells}, index)) == mines : U32}

law board4_reveal_keeps_all_mines:
  for mines: U32
  for cells: Array<Game.Square>
  for index: U32
  for clue: U32
  {Board4.mine_mask(Board4.reveal_at(Board4.State{mines, cells}, index, clue)) == mines : U32}

# B-04: 0 mines means 0 adjacent mines at every coordinate.
law board4_empty_clue_is_zero:
  for x: U32
  for y: U32
  {Board4.clue(0, x, y) == 0 : U32}

# Concrete regression contracts distinguish cell from neighbor and edge
# from toroidal wrap. Every possible single-mine position is also tested
# independently against a Python oracle.
law board4_own_mine_not_counted:
  {Board4.clue(1, 0, 0) == 0 : U32}

law board4_diagonal_clue:
  {Board4.clue(1, 1, 1) == 1 : U32}

law board4_two_mines_clue:
  {Board4.clue(33, 1, 0) == 2 : U32}

# B-05: the public checked editing API rejects indices beyond 0..15.
# Unchecked Array.get/set wraps indices; the game must never expose those
# operations directly to a user click or a solver move.
law board4_rejects_invalid_flag_index:
  for mines: U32
  for cells: Array<Game.Square>
  {Board4.toggle_checked(Board4.State{mines, cells}, 16) == Board4.State{mines, cells} : Board4.State}

law board4_rejects_invalid_reveal_index:
  for mines: U32
  for cells: Array<Game.Square>
  for clue: U32
  {Board4.reveal_checked(Board4.State{mines, cells}, 16, clue) == Board4.State{mines, cells} : Board4.State}

# G-02: game rules are written BEFORE the implementation in session.bend.
# A left-click on a hidden mine loses; a flagged mine is not opened.
law session_mine_click_loses:
  {Session.phase_of(Session.click(Session.new(1), 0)) == Session.Lost{} : Session.Phase}

law session_flag_protects_mine:
  {Session.phase_of(Session.click(Session.mark(Session.new(1), 0), 0)) == Session.Playing{} : Session.Phase}

# Invalid indexes must not count as clicks, including on an otherwise mined board.
law session_outside_ignored:
  for mines: U32
  {Session.phase_of(Session.click(Session.new(mines), 16)) == Session.Playing{} : Session.Phase}

# Once a game is finished no later click (or flag change) can revive it.
law session_lost_is_terminal:
  for board: Board4.State
  for index: U32
  {Session.click(Session.Session{board, Session.Lost{}}, index) == Session.Session{board, Session.Lost{}} : Session.Session}

law session_won_is_terminal:
  for board: Board4.State
  for index: U32
  {Session.click(Session.Session{board, Session.Won{}}, index) == Session.Session{board, Session.Won{}} : Session.Session}

# G-03: a board with 15 mines has one safe cell: clicking it wins.
# The general criterion ("all safe cells opened, and only then") is
# implemented by scanning the Array, and checked separately by an oracle.
law session_last_safe_cell_wins:
  {Session.phase_of(Session.click(Session.new(65534), 0)) == Session.Won{} : Session.Phase}

# The user-facing click computes the true adjacent clue; it does NOT trust
# a caller-supplied number, and it never changes already-visible numbers.
law session_safe_click_shows_true_clue:
  {Session.read_square(Session.click(Session.new(1), 5), 5) == Game.Open{1} : Game.Square}

# G-01 (separate entry point): the first left-click must not be a loss.
# Active Session.new is deliberately a low-level, ALREADY-PLACED board.
# These contracts introduce a Fresh controller instead of changing G-02.
# Valid setup has 0..15 mines; the full 16-mine board is rejected.
law start_relocates_clicked_mine:
  {Start.mine_mask(Start.click(Start.new(1), 0)) == 2 : U32}

law start_preserves_other_mines:
  {Start.mine_mask(Start.click(Start.new(33), 0)) == 34 : U32}

law start_keeps_safe_placement:
  {Start.mine_mask(Start.click(Start.new(1), 5)) == 1 : U32}

law start_first_square_opened:
  {Start.visible_at(Start.click(Start.new(1), 0), 0) == Game.Open{1} : Game.Square}

law start_ignores_outside_first_click:
  {Start.is_fresh(Start.click(Start.new(1), 16)) == True{} : Bool}

law start_rejects_impossible_full_board:
  {Start.is_fresh(Start.click(Start.new(65535), 0)) == True{} : Bool}

# G-04: A zero click reaches all zero-connected safe squares and the
# nonzero boundary, but neither mines nor existing flags may be opened.
law flood_empty_board_wins:
  {Session.phase_of(Session.click(Session.new(0), 0)) == Session.Won{} : Session.Phase}

law flood_empty_board_far_corner:
  {Session.read_square(Session.click(Session.new(0), 0), 15) == Game.Open{0} : Game.Square}

law flood_reaches_numbered_boundary:
  {Session.read_square(Session.click(Session.new(32768), 0), 14) == Game.Open{1} : Game.Square}

law flood_never_reveals_mine:
  {Session.read_square(Session.click(Session.new(32768), 0), 15) == Game.Hidden{} : Game.Square}

law flood_preserves_flagged_safe_cell:
  {Session.read_square(Session.click(Session.mark(Session.new(0), 1), 0), 1) == Game.Flag{} : Game.Square}

law nonzero_click_does_not_cascade:
  {Session.read_square(Session.click(Session.new(1), 5), 15) == Game.Hidden{} : Game.Square}
