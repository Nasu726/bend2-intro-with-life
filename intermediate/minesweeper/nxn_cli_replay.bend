# Fixed 10x10 CLI replay over the full N x N Bend game engine.
# Usage: bend intermediate/minesweeper/nxn_cli_replay.bend 99 c0 c99
# First argument is the cell to inspect. Later cN/fN/r commands are replayed.
# Output is a PUBLIC snapshot code, never a mine mask. Not an interactive GUI.
import Base
import ./nxn_mine_words.bend as Words
import ./nxn_playthrough.bend as Demo
import ./nxn_full_game.bend as Game

def initial() -> Game.Game:
  Game.new(Demo.mine_wall(Words.new(10)))

def click_number(game: Game.Game, number: Maybe<&2, U32>) -> Game.Game:
  match number:
    case Some{index}:
      Game.click(game, index)
    case None{}:
      game

def flag_number(game: Game.Game, number: Maybe<&2, U32>) -> Game.Game:
  match number:
    case Some{index}:
      Game.mark(game, index)
    case None{}:
      game

def choose_flag(game: Game.Game, command: String, flag: Bool) -> Game.Game:
  match flag:
    case True{}:
      flag_number(game, U32.read(String.drop(command, 1n)))
    case False{}:
      game

def choose_click(game: Game.Game, command: String, click: Bool) -> Game.Game:
  match click:
    case True{}:
      click_number(game, U32.read(String.drop(command, 1n)))
    case False{}:
      choose_flag(game, command, String.starts_with(command, "f"))

def reset_or_action(game: Game.Game, command: String, reset: Bool) -> Game.Game:
  match reset:
    case True{}:
      initial()
    case False{}:
      choose_click(game, command, String.starts_with(command, "c"))

def choose_action(game: Game.Game, command: String) -> Game.Game:
  reset_or_action(game, command, String.eq(command, "r"))

# The decreasing list comes first: the game state is a linear resource.
def replay(commands: List<String>, game: Game.Game) -> Game.Game:
  match commands:
    case Nil{}:
      game
    case command <> rest:
      replay(rest, choose_action(game, command))

def read_probe(number: Maybe<&2, U32>, commands: List<String>) -> U32:
  match number:
    case None{}:
      999
    case Some{index}:
      Game.snapshot(replay(commands, initial()), index)

def run_args(args: List<String>) -> U32:
  match args:
    case Nil{}:
      999
    case probe <> commands:
      read_probe(U32.read(probe), commands)

def without_program(args: List<String>) -> List<String>:
  match args:
    case Nil{}:
      Nil{}
    case first <> rest:
      rest

def main() -> IO(Unit):
  do IO<Unit>:
    args: List<String> <- IO.args()
    IO.print(U32.show(run_args(without_program(args))))
