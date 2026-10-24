# Deterministic N x N CLI replay: 10x10 example with M=10 mines.
# cINDEX clicks, fINDEX toggles a flag, r resets; unknown commands are ignored.
# This is not an interactive prompt or a save/load implementation.
# Only visible squares are rendered: mine truth stays inside the engine.
import Base
import ./game.bend as Square
import ./nxn_mine_words.bend as Words
import ./nxn_full_game.bend as Engine
import ./nxn_step.bend as Step
import ./nxn_terminal.bend as Terminal

# Fixed layout for a reproducible lesson, not a random game generator.
def initial_board() -> Words.MineWords:
  board = Words.new(10)
  board = Words.set_checked(board, 11, True{})
  board = Words.set_checked(board, 12, True{})
  board = Words.set_checked(board, 22, True{})
  board = Words.set_checked(board, 34, True{})
  board = Words.set_checked(board, 45, True{})
  board = Words.set_checked(board, 56, True{})
  board = Words.set_checked(board, 67, True{})
  board = Words.set_checked(board, 78, True{})
  board = Words.set_checked(board, 89, True{})
  Words.set_checked(board, 99, True{})

def click_number(stage: Engine.Game, value: Maybe<&2, U32>) -> Engine.Game:
  match value:
    case Some{index}:
      Engine.click(stage, index)
    case None{}:
      stage

def flag_number(stage: Engine.Game, value: Maybe<&2, U32>) -> Engine.Game:
  match value:
    case Some{index}:
      Engine.mark(stage, index)
    case None{}:
      stage

def choose_flag(stage: Engine.Game, command: String, is_flag: Bool) -> Engine.Game:
  match is_flag:
    case True{}:
      flag_number(stage, U32.read(String.drop(command, 1n)))
    case False{}:
      stage

def choose_click(stage: Engine.Game, +command: String, is_click: Bool) -> Engine.Game:
  match is_click:
    case True{}:
      click_number(stage, U32.read(String.drop(command, 1n)))
    case False{}:
      choose_flag(stage, command, String.starts_with(command, "f"))

def reset_or_action(stage: Engine.Game, +command: String, reset: Bool) -> Engine.Game:
  match reset:
    case True{}:
      Engine.new(initial_board())
    case False{}:
      choose_click(stage, command, String.starts_with(command, "c"))

def action(stage: Engine.Game, +command: String) -> Engine.Game:
  reset_or_action(stage, command, String.eq(command, "r"))

# Structurally decreasing command list comes before the mutable game state.
def replay(commands: List<String>, stage: Engine.Game) -> Engine.Game:
  match commands:
    case Nil{}:
      stage
    case command <> rest:
      replay(rest, action(stage, command))

def cell_symbol(square: Square.Square) -> String:
  match square:
    case Square.Hidden{}:
      "."
    case Square.Flag{}:
      "F"
    case Square.Open{clue}:
      U32.show(clue)

def separator(end_of_row: Bool) -> String:
  match end_of_row:
    case True{}:
      "\n"
    case False{}:
      " "

# Array has power-of-two capacity; print exactly n*n logical cells.
def show_cells(remaining: Nat, cells: List<Square.Square>, +column: U32, +n: U32) -> String:
  match remaining:
    case 0n:
      ""
    case 1n+k:
      match cells:
        case Nil{}:
          ""
        case square <> rest:
          cell_symbol(square) ++ separator(U32.is_eq(U32.mod((column + 1 : U32), n), 0)) ++ show_cells(k, rest, (column + 1 : U32), n)

def show_session(session: Step.Session) -> String:
  match session:
    case Step.Session{+n, mines, cells, phase}:
      show_cells(U32.to_nat((n * n : U32)), Array.to_list(Square.Square, cells), 0, n)

def show_state(state: Terminal.State) -> String:
  match state:
    case Terminal.Playing{session}:
      "Playing\n" ++ show_session(session)
    case Terminal.Won{session}:
      "Won\n" ++ show_session(session)
    case Terminal.Lost{session}:
      "Lost\n" ++ show_session(session)

def show_board(stage: Engine.Game) -> String:
  match stage:
    case Engine.Fresh{board}:
      "Fresh: first click with c0..c99\n"
    case Engine.Active{state}:
      show_state(state)

def without_program(args: List<String>) -> List<String>:
  match args:
    case Nil{}:
      Nil{}
    case first <> rest:
      rest

def main() -> IO(Unit):
  do IO<Unit>:
    args: List<String> <- IO.args()
    IO.print(show_board(replay(without_program(args), Engine.new(initial_board()))))
