# Run: bend examples/minesweeper/nxn_layout_demo.bend
# 10x10 logical cells, 128 physical slots, no wrap into slots 100..127.
import Base
import ./game.bend as Game
import ./board_n.bend as BoardN

def print_invalid(r: BoardN.State & Maybe<&2, Game.Square>,
                  physical: U32, cell_99: U32) -> IO(Unit):
  (unused_board, invalid) = r
  do IO<Unit>:
    IO.print(U32.show(physical))
    IO.print(U32.show(cell_99))
    IO.print(U32.show(BoardN.square_code(invalid)))

def print_flag(r: BoardN.State & Maybe<&2, Game.Square>,
               physical: U32) -> IO(Unit):
  (board, square) = r
  print_invalid(BoardN.read_checked(board, 100),
                physical, BoardN.square_code(square))

def show_layout(r: BoardN.State & U32) -> IO(Unit):
  (board, physical) = r
  board1 = BoardN.mark_checked(board, 99)
  board2 = BoardN.mark_checked(board1, 100)
  print_flag(BoardN.read_checked(board2, 99), physical)

def run_board(c: BoardN.Creation) -> IO(Unit):
  match c:
    case BoardN.Invalid{}:
      IO.print("Unsupported N")
    case BoardN.Created{board}:
      show_layout(BoardN.capacity(board))

def main() -> IO(Unit):
  run_board(BoardN.new_checked(10))
