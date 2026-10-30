# Structured File outcome for the learner-facing S/L notification example.
# Keep the original Store.save API unchanged for the simpler GUI.
import Base
import ./nxn_gui_history.bend as History
import ./nxn_gui_store.bend as Store

# Save reporting is separate from the compatible save() API. Returning the
# affine Model together with a Bool lets a GUI distinguish a failed S from
# a successful S, without ever serializing hidden mine truth.
def finish_write_report(model: History.Model,
                        pair: File & Result<&1, &1, U32 & String, Unit>) ->
  IO(History.Model & Bool):
  (file, result) = pair
  match result:
    case Done{value}:
      do IO<History.Model & Bool>:
        Unit <- File.close(file)
        return (model, True{})
    case Fail{error}:
      do IO<History.Model & Bool>:
        Unit <- File.close(file)
        return (model, False{})

def finish_open_write_report(model: History.Model, text: String,
                             opened: Result<&1, &1, U32 & String, File>) ->
  IO(History.Model & Bool):
  match opened:
    case Fail{error}:
      IO.pure(History.Model & Bool, (model, False{}))
    case Done{file}:
      do IO<History.Model & Bool>:
        result: File & Result<&1, &1, U32 & String, Unit> <- File.write(file, text)
        finish_write_report(model, result)

def save_if_valid_report(valid: Bool, model: History.Model, text: String) ->
  IO(History.Model & Bool):
  match valid:
    case False{}:
      IO.pure(History.Model & Bool, (model, False{}))
    case True{}:
      do IO<History.Model & Bool>:
        opened: Result<&1, &1, U32 & String, File> <-
          File.open("minesweeper_nxn_save.txt", "w")
        finish_open_write_report(model, text, opened)

def save_report(model: History.Model) -> IO(History.Model & Bool):
  match model:
    case History.Model{game, +newest_first, +seed}:
      +chronological = List.reverse(&2, U32, newest_first)
      save_if_valid_report(
        Bool.and(Nat.is_le(List.length(&2, U32, chronological), 512n),
                 History.valid_entries(chronological)),
        History.Model{game, newest_first, seed},
        Store.payload(seed, chronological))


def main() -> U32:
  0
