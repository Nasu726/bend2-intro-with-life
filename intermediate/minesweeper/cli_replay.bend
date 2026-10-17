# Deterministic, non-interactive command-line replay of a 4x4 game.
# Commands are read from IO.args: c0 = click cell 0, f1 = toggle flag 1,
# r = reset to the initial mine layout. This is not yet a prompt loop.
# We intentionally show ONLY the public board, never the true mine mask.
import Base
import ./game.bend as Game
import ./board4.bend as Board4
import ./session.bend as Session
import ./start.bend as Start

def mark(stage: Start.Stage, index: U32) -> Start.Stage:
  match stage:
    case Start.Fresh{mines}:
      Start.Fresh{mines}
    case Start.Active{session}:
      Start.Active{Session.mark(session, index)}

def click_number(stage: Start.Stage, value: Maybe<&2, U32>) -> Start.Stage:
  match value:
    case Some{index}:
      Start.click(stage, index)
    case None{}:
      stage

def flag_number(stage: Start.Stage, value: Maybe<&2, U32>) -> Start.Stage:
  match value:
    case Some{index}:
      mark(stage, index)
    case None{}:
      stage

def choose_action(stage: Start.Stage, +command: String) -> Start.Stage:
  match String.starts_with(command, "c"):
    case True{}:
      click_number(stage, U32.read(String.drop(command, 1n)))
    case False{}:
      match String.starts_with(command, "f"):
        case True{}:
          flag_number(stage, U32.read(String.drop(command, 1n)))
        case False{}:
          stage

def action(stage: Start.Stage, command: String) -> Start.Stage:
  match String.eq(command, "r"):
    case True{}:
      Start.new(33)
    case False{}:
      choose_action(stage, command)

def replay(stage: Start.Stage, commands: List<String>) -> Start.Stage:
  match commands:
    case Nil{}:
      stage
    case command <> rest:
      replay(action(stage, command), rest)

def cell_symbol(square: Game.Square) -> String:
  match square:
    case Game.Hidden{}:
      "."
    case Game.Flag{}:
      "F"
    case Game.Open{clue}:
      U32.show(clue)

def spacing(column: U32) -> String:
  match U32.is_eq(U32.mod((column + 1 : U32), 4), 0):
    case True{}:
      "\n"
    case False{}:
      " "

def show_cells(cells: List<Game.Square>, +column: U32) -> String:
  match cells:
    case Nil{}:
      ""
    case cell <> rest:
      cell_symbol(cell) ++ spacing(column) ++ show_cells(rest, (column + 1 : U32))

def phase_name(phase: Session.Phase) -> String:
  match phase:
    case Session.Playing{}:
      "Playing\n"
    case Session.Won{}:
      "Won\n"
    case Session.Lost{}:
      "Lost\n"

def show_session(session: Session.Session) -> String:
  match session:
    case Session.Session{board, phase}:
      match board:
        case Board4.State{mines, cells}:
          phase_name(phase) ++ show_cells(Array.to_list(Game.Square, cells), 0)

def show_board(stage: Start.Stage) -> String:
  match stage:
    case Start.Fresh{mines}:
      "Fresh: first click with c0..c15\n"
    case Start.Active{session}:
      show_session(session)

def without_program(args: List<String>) -> List<String>:
  match args:
    case Nil{}:
      Nil{}
    case first <> rest:
      rest

def main() -> IO(Unit):
  do IO<Unit>:
    args: List<String> <- IO.args()
    IO.print(show_board(replay(Start.new(33), without_program(args))))
