# Experimental Linux-only atomic replacement for the GUI's PUBLIC replay.
# Not wired to the learner-facing GUI until the Bend + X11 gate succeeds.
# Same-directory temporary write, close, then GNU mv -fT (rename on Linux).
# No fsync: this protects against partial replacement, not power-loss durability.
# No multi-process lock; randomized temporary names reduce, not eliminate, races.
import Base
import ./nxn_gui_history.bend as History
import ./nxn_gui_store.bend as Store

def cleanup_failed(model: History.Model, temp: String) -> IO(History.Model & Bool):
  do IO<History.Model & Bool>:
    ignored: Result<&1, &1, U32 & String, U32 & (String & String)> <-
      Process.run("/usr/bin/rm", ["-f", "--", temp], "", 512, 3000)
    return (model, False{})

def after_exit(model: History.Model, temp: String, ok: Bool) ->
  IO(History.Model & Bool):
  match ok:
    case True{}:
      IO.pure(History.Model & Bool, (model, True{}))
    case False{}:
      cleanup_failed(model, temp)

def after_move(model: History.Model, temp: String,
               result: Result<&1, &1, U32 & String, U32 & (String & String)>) ->
  IO(History.Model & Bool):
  match result:
    case Fail{error}:
      cleanup_failed(model, temp)
    case Done{value}:
      (code, outputs) = value
      after_exit(model, temp, U32.is_eq(code, 0))

def after_write(model: History.Model, +temp: String,
                pair: File & Result<&1, &1, U32 & String, Unit>) ->
  IO(History.Model & Bool):
  (file, status) = pair
  match status:
    case Done{value}:
      do IO<History.Model & Bool>:
        Unit <- File.close(file)
        moved: Result<&1, &1, U32 & String, U32 & (String & String)> <-
          Process.run("/usr/bin/mv",
                      ["-fT", "--", temp, "minesweeper_nxn_save.txt"],
                      "", 512, 3000)
        after_move(model, temp, moved)
    case Fail{error}:
      do IO<History.Model & Bool>:
        Unit <- File.close(file)
        cleanup_failed(model, temp)

def after_open(model: History.Model, text: String, +temp: String,
               opened: Result<&1, &1, U32 & String, File>) ->
  IO(History.Model & Bool):
  match opened:
    case Fail{error}:
      IO.pure(History.Model & Bool, (model, False{}))
    case Done{file}:
      do IO<History.Model & Bool>:
        pair: File & Result<&1, &1, U32 & String, Unit> <- File.write(file, text)
        after_write(model, temp, pair)

def write_temp(model: History.Model, text: String, +temp: String) ->
  IO(History.Model & Bool):
  do IO<History.Model & Bool>:
    opened: Result<&1, &1, U32 & String, File> <- File.open(temp, "w")
    after_open(model, text, temp, opened)

def with_nonce(model: History.Model, text: String,
               nonce: Result<&1, &1, U32 & String, U32>) ->
  IO(History.Model & Bool):
  match nonce:
    case Fail{error}:
      IO.pure(History.Model & Bool, (model, False{}))
    case Done{value}:
      write_temp(model, text, "minesweeper_nxn_save.txt.tmp." ++ U32.show(value))

def if_valid(valid: Bool, model: History.Model, text: String) ->
  IO(History.Model & Bool):
  match valid:
    case False{}:
      IO.pure(History.Model & Bool, (model, False{}))
    case True{}:
      do IO<History.Model & Bool>:
        nonce: Result<&1, &1, U32 & String, U32> <- IO.random_u32()
        with_nonce(model, text, nonce)

def save_atomic_report(model: History.Model) -> IO(History.Model & Bool):
  match model:
    case History.Model{game, +newest_first, +seed}:
      +chronological = List.reverse(&2, U32, newest_first)
      if_valid(
        Bool.and(Nat.is_le(List.length(&2, U32, chronological), 512n),
                 History.valid_entries(chronological)),
        History.Model{game, newest_first, seed},
        Store.payload(seed, chronological))

def print_result(pair: History.Model & Bool) -> IO(Unit):
  (model, ok) = pair
  match ok:
    case True{}:
      IO.print("1")
    case False{}:
      IO.print("0")

def main() -> IO(Unit):
  do IO<Unit>:
    result: History.Model & Bool <- save_atomic_report(
      History.pointer(History.pointer(History.new(20261029), 0, 0, 0), 319, 319, 1))
    print_result(result)
