# Small but real command-history save/restore for the *fixed* initial
# 4x4 game in cli_replay.bend. Does not serialize privileged engine internals.
#   bend examples/minesweeper/cli_save.bend save c0 f1
#   bend examples/minesweeper/cli_save.bend load
# Stored relative to current directory: minesweeper_save.txt
# Format: BEND2-SAVE-1|c0|f1|END (strict, bounded, versioned).
import Base
import ./cli_replay.bend as Replay
import ./start.bend as Start

def parsed_index(value: Maybe<&2, U32>) -> Bool:
  match value:
    case None{}:
      False{}
    case Some{index}:
      U32.is_lt(index, 16)

def valid_token(+command: String) -> Bool:
  (String.eq(command, "r") ||
   (String.starts_with(command, "c") &&
    parsed_index(U32.read(String.drop(command, 1n)))) ||
   (String.starts_with(command, "f") &&
    parsed_index(U32.read(String.drop(command, 1n)))) : Bool)

def valid_list(commands: List<&2, String>) -> Bool:
  match commands:
    case Nil{}:
      True{}
    case command <> rest:
      Bool.and(valid_token(command), valid_list(rest))

def valid_save(+commands: List<&2, String>) -> Bool:
  Bool.and(
    Nat.is_le(1n, List.length(&2, String, commands)),
    Bool.and(
      Nat.is_le(List.length(&2, String, commands), 64n),
      valid_list(commands)))

# The parser returns ExpectEnd for a list with no tokens. When traversing
# from right to left the rightmost token MUST be END, and all earlier tokens
# MUST be legal game commands. Even embedded END or extra fields are rejected.
type Parsed is Data:
  ExpectEnd{}
  Valid{commands: List<&2, String>}

def accept_end(ok: Bool) -> Maybe<&2, Parsed>:
  match ok:
    case True{}:
      Some{Valid{Nil{}}}
    case False{}:
      None{}

def accept_command(ok: Bool, command: String,
                   rest: List<&2, String>) -> Maybe<&2, Parsed>:
  match ok:
    case True{}:
      Some{Valid{command <> rest}}
    case False{}:
      None{}

def combine_token(+command: String, tail: Maybe<&2, Parsed>) ->
  Maybe<&2, Parsed>:
  match tail:
    case None{}:
      None{}
    case Some{ExpectEnd{}}:
      accept_end(String.eq(command, "END"))
    case Some{Valid{commands}}:
      accept_command(valid_token(command), command, commands)

def parse_tokens(tokens: List<&2, String>) -> Maybe<&2, Parsed>:
  match tokens:
    case Nil{}:
      Some{ExpectEnd{}}
    case command <> rest:
      combine_token(command, parse_tokens(rest))

# Loading must enforce the same 1..64-command contract as saving.
# A syntactically valid END token is not enough for a valid save.
def accepted_commands(ok: Bool, commands: List<&2, String>) ->
  Maybe<&2, List<&2, String>>:
  match ok:
    case True{}:
      Some{commands}
    case False{}:
      None{}

def checked_commands(+commands: List<&2, String>) ->
  Maybe<&2, List<&2, String>>:
  accepted_commands(valid_save(commands), commands)

def parsed_commands(parsed: Maybe<&2, Parsed>) ->
  Maybe<&2, List<&2, String>>:
  match parsed:
    case Some{Valid{commands}}:
      checked_commands(commands)
    case _:
      None{}

def if_header(ok: Bool, body: List<&2, String>) ->
  Maybe<&2, List<&2, String>>:
  match ok:
    case False{}:
      None{}
    case True{}:
      parsed_commands(parse_tokens(body))

def parse_parts(parts: List<&2, String>) ->
  Maybe<&2, List<&2, String>>:
  match parts:
    case Nil{}:
      None{}
    case header <> rest:
      if_header(String.eq(header, "BEND2-SAVE-1"), rest)

def if_small(ok: Bool, data: String) -> Maybe<&2, List<&2, String>>:
  match ok:
    case True{}:
      parse_parts(String.split(data, Chr{124}))
    case False{}:
      None{}

def deserialize(+data: String) -> Maybe<&2, List<&2, String>>:
  if_small(Nat.is_le(String.length(data), 512n), data)

def serialize(commands: List<&2, String>) -> String:
  "BEND2-SAVE-1|" ++ String.join(commands, "|") ++ "|END"

def written(result: File & Result<&1, &1, U32 & String, Unit>) -> IO(Unit):
  (file, status) = result
  match status:
    case Done{value}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.print("Saved minesweeper_save.txt")
    case Fail{error}:
      do IO<Unit>:
        Unit <- File.close(file)
        IO.die(Unit, 1, "Could not write minesweeper_save.txt")

def save_if_valid(ok: Bool, commands: List<&2, String>) -> IO(Unit):
  match ok:
    case False{}:
      IO.die(Unit, 1, "Invalid commands (c0..c15, f0..f15, r; up to 64)")
    case True{}:
      do IO<Unit>:
        file: File <- IO.try(File, File.open("minesweeper_save.txt", "w"))
        result: File & Result<&1, &1, U32 & String, Unit> <-
          File.write(file, serialize(commands))
        written(result)

def save(+commands: List<&2, String>) -> IO(Unit):
  save_if_valid(valid_save(commands), commands)

# IO.args / the CLI engine use an affine List<String>; String.split
# returns a data-kinded List<&2,String>. Copy elements structurally at
# the boundary instead of assuming the two list kinds are equal.
def to_affine(xs: List<&2, String>) -> List<String>:
  match xs:
    case Nil{}:
      Nil{}
    case item <> rest:
      item <> to_affine(rest)

def to_data(xs: List<String>) -> List<&2, String>:
  match xs:
    case Nil{}:
      Nil{}
    case item <> rest:
      item <> to_data(rest)

def show_restored(parsed: Maybe<&2, List<&2, String>>) -> IO(Unit):
  match parsed:
    case None{}:
      IO.die(Unit, 1, "Corrupt/unsupported saved command history")
    case Some{commands}:
      IO.print(Replay.show_board(Replay.replay(to_affine(commands), Start.new(33))))

def closed_read(result: File & Result<&1, &1, U32 & String, String>) ->
  IO(String):
  (file, status) = result
  match status:
    case Done{data}:
      do IO<String>:
        Unit <- File.close(file)
        return data
    case Fail{error}:
      do IO<String>:
        Unit <- File.close(file)
        IO.die(String, 1, "Could not read minesweeper_save.txt")

def load() -> IO(Unit):
  do IO<Unit>:
    file: File <- IO.try(File, File.open("minesweeper_save.txt", "r"))
    read: File & Result<&1, &1, U32 & String, String> <- File.read(file, 4096)
    text: String <- closed_read(read)
    show_restored(deserialize(text))

def load_if_no_extra(args: List<&2, String>) -> IO(Unit):
  match args:
    case Nil{}:
      load()
    case _:
      IO.die(Unit, 1, "load expects no extra arguments")

def dispatch(saving: Bool, loading: Bool, commands: List<&2, String>) -> IO(Unit):
  match saving loading:
    case True{} _:
      save(commands)
    case False{} True{}:
      load_if_no_extra(commands)
    case False{} False{}:
      IO.die(Unit, 1, "Usage: cli_save.bend save c0 f1 | load")

def command_mode(+mode: String, commands: List<&2, String>) -> IO(Unit):
  dispatch(String.eq(mode, "save"), String.eq(mode, "load"), commands)

def execute(args: List<&2, String>) -> IO(Unit):
  match args:
    case Nil{}:
      IO.die(Unit, 1, "Usage: cli_save.bend save c0 f1 | load")
    case mode <> commands:
      command_mode(mode, commands)

def main() -> IO(Unit):
  do IO<Unit>:
    args: List<String> <- IO.args()
    execute(to_data(Replay.without_program(args)))
