# Versioned on-disk replay of the 10x10 GUI's PUBLIC input history.
# Open/read/write failures leave the live game running; successful saves use the same format.
# Filename (relative to current directory): minesweeper_nxn_save.txt
# Canonical format: BEND2-GUI-1|<seed>|<code>|...|END
# A code is 2*cell+button, within 0..199; no mine truth is serialized.
import Base
import ./nxn_gui_history.bend as History

def encode(entries: List<&2, U32>) -> String:
  match entries:
    case Nil{}:
      "END"
    case entry <> rest:
      U32.show(entry) ++ "|" ++ encode(rest)

def payload(+seed: U32, entries: List<&2, U32>) -> String:
  "BEND2-GUI-1|" ++ U32.show(seed) ++ "|" ++ encode(entries)

type Parsed is Data:
  ExpectEnd{}
  Valid{entries: List<&2, U32>}

def permit_end(ok: Bool) -> Maybe<&2, Parsed>:
  match ok:
    case True{}:
      Some{Valid{Nil{}}}
    case False{}:
      None{}

def permit_code(ok: Bool, code: U32, tail: List<&2, U32>) ->
  Maybe<&2, Parsed>:
  match ok:
    case True{}:
      Some{Valid{code <> tail}}
    case False{}:
      None{}

# The parsed scalar is tested and then retained in the replay list.
# Declare the helper's code duplicable to satisfy Bend's affine checker.
def bounded_code(+code: U32, tail: List<&2, U32>) ->
  Maybe<&2, Parsed>:
  permit_code(U32.is_lt(code, 200), code, tail)

def parsed_code(value: Maybe<&2, U32>, tail: List<&2, U32>) ->
  Maybe<&2, Parsed>:
  match value:
    case None{}:
      None{}
    case Some{code}:
      bounded_code(code, tail)

def merge_token(+token: String, suffix: Maybe<&2, Parsed>) ->
  Maybe<&2, Parsed>:
  match suffix:
    case None{}:
      None{}
    case Some{ExpectEnd{}}:
      permit_end(String.eq(token, "END"))
    case Some{Valid{entries}}:
      parsed_code(U32.read(token), entries)

def parse_tokens(tokens: List<&2, String>) -> Maybe<&2, Parsed>:
  match tokens:
    case Nil{}:
      Some{ExpectEnd{}}
    case token <> rest:
      merge_token(token, parse_tokens(rest))

def finish_tokens(parsed: Maybe<&2, Parsed>, seed: U32) -> History.Recovery:
  match parsed:
    case Some{Valid{entries}}:
      History.restore(seed, entries)
    case _:
      History.Corrupt{}

def with_seed(value: Maybe<&2, U32>, tokens: List<&2, String>) ->
  History.Recovery:
  match value:
    case None{}:
      History.Corrupt{}
    case Some{seed}:
      finish_tokens(parse_tokens(tokens), seed)

def split_seed(fields: List<&2, String>) -> History.Recovery:
  match fields:
    case Nil{}:
      History.Corrupt{}
    case seed_text <> tokens:
      with_seed(U32.read(seed_text), tokens)

def with_header(valid: Bool, fields: List<&2, String>) -> History.Recovery:
  match valid:
    case False{}:
      History.Corrupt{}
    case True{}:
      split_seed(fields)

def split_header(fields: List<&2, String>) -> History.Recovery:
  match fields:
    case Nil{}:
      History.Corrupt{}
    case header <> rest:
      with_header(String.eq(header, "BEND2-GUI-1"), rest)

def bounded_parse(valid: Bool, text: String) -> History.Recovery:
  match valid:
    case False{}:
      History.Corrupt{}
    case True{}:
      split_header(String.split(text, Chr{124}))

# The file read requests 4097 bytes, to reject a 4097+ byte prefix, too.
def deserialize(+text: String) -> History.Recovery:
  bounded_parse(Nat.is_le(String.length(text), 4096n), text)

def finish_write(model: History.Model,
                 result: File & Result<&1, &1, U32 & String, Unit>) ->
  IO(History.Model):
  (file, result) = result
  match result:
    case Done{value}:
      do IO<History.Model>:
        Unit <- File.close(file)
        return model
    case Fail{error}:
      do IO<History.Model>:
        Unit <- File.close(file)
        return model

def finish_open_write(model: History.Model, text: String,
                      opened: Result<&1, &1, U32 & String, File>) ->
  IO(History.Model):
  match opened:
    case Fail{error}:
      IO.pure(History.Model, model)
    case Done{file}:
      do IO<History.Model>:
        result: File & Result<&1, &1, U32 & String, Unit> <-
          File.write(file, text)
        finish_write(model, result)


def save_if_valid(valid: Bool, model: History.Model, text: String) ->
  IO(History.Model):
  match valid:
    case False{}:
      IO.pure(History.Model, model)
    case True{}:
      do IO<History.Model>:
        opened: Result<&1, &1, U32 & String, File> <-
          File.open("minesweeper_nxn_save.txt", "w")
        finish_open_write(model, text, opened)

# An invalid history never opens/truncates the existing save. An I/O error
# retains the live game, but is not displayed in the GUI yet.
# The non-copyable game survives the write without serializing mine truth.
def save(model: History.Model) -> IO(History.Model):
  match model:
    case History.Model{game, +newest_first, +seed}:
      +chronological = List.reverse(&2, U32, newest_first)
      save_if_valid(
        Bool.and(Nat.is_le(List.length(&2, U32, chronological), 512n),
                 History.valid_entries(chronological)),
        History.Model{game, newest_first, seed},
        payload(seed, chronological))

def finish_read(result: File & Result<&1, &1, U32 & String, String>) ->
  IO(History.Recovery):
  (file, status) = result
  match status:
    case Done{text}:
      do IO<History.Recovery>:
        Unit <- File.close(file)
        return deserialize(text)
    case Fail{error}:
      do IO<History.Recovery>:
        Unit <- File.close(file)
        return History.Corrupt{}

def finish_open_read(opened: Result<&1, &1, U32 & String, File>) ->
  IO(History.Recovery):
  match opened:
    case Fail{error}:
      IO.pure(History.Recovery, History.Corrupt{})
    case Done{file}:
      do IO<History.Recovery>:
        result: File & Result<&1, &1, U32 & String, String> <-
          File.read(file, 4097)
        finish_read(result)

# A missing/unreadable save returns Corrupt, so App.run keeps the live model.
def load() -> IO(History.Recovery):
  do IO<History.Recovery>:
    opened: Result<&1, &1, U32 & String, File> <-
      File.open("minesweeper_nxn_save.txt", "r")
    finish_open_read(opened)

# A pure parse smoke; real file I/O is exercised by the Python harness.
def main() -> U32:
  History.recovered_snapshot(
    deserialize("BEND2-GUI-1|20261029|0|199|END"), 99)
