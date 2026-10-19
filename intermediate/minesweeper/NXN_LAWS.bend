# First independent N x N contracts. The 4x4 LAWS are unchanged.
# Checked operation contracts concern only logical cells, not Array capacity.
import Base
import ./game.bend as Game
import ./board_n.bend as BoardN

law nxn_index_last_10:
  {BoardN.index(10, 9, 9) == 99 : U32}

law nxn_depth_10_is_7:
  {BoardN.storage_depth(10) == 7n : Nat}

law nxn_origin_is_valid_10:
  {BoardN.in_bounds(10, 0, 0) == True{} : Bool}

law nxn_far_corner_valid_10:
  {BoardN.in_bounds(10, 9, 9) == True{} : Bool}

law nxn_outside_right:
  for y: U32
  {BoardN.in_bounds(10, 10, y) == False{} : Bool}

# Concrete bottom-edge witness; the Python oracle checks every column.
law nxn_outside_bottom:
  {BoardN.in_bounds(10, 0, 10) == False{} : Bool}

law nxn_padding_100_is_invalid:
  {BoardN.valid_index(10, 100) == False{} : Bool}

law nxn_padding_127_is_invalid:
  {BoardN.valid_index(10, 127) == False{} : Bool}

law nxn_last_cell_99_is_valid:
  {BoardN.valid_index(10, 99) == True{} : Bool}

law nxn_mark_padding_unchanged:
  for mines: Array<Bool>
  for cells: Array<Game.Square>
  {BoardN.mark_checked(BoardN.State{10, mines, cells}, 100)
      == BoardN.State{10, mines, cells} : BoardN.State}

law nxn_mark_far_padding_unchanged:
  for mines: Array<Bool>
  for cells: Array<Game.Square>
  {BoardN.mark_checked(BoardN.State{10, mines, cells}, 127)
      == BoardN.State{10, mines, cells} : BoardN.State}
