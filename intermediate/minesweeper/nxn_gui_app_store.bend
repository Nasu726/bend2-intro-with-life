# 10x10 GUI with replayable public-input history and S/L File controls.
# S saves, L loads; R resets; Esc closes. No mine truth is serialized.
# The 512x512 window has a 320x320 active area in the top-left corner.
import Base
import ./nxn_lazy_game.bend as Lazy
import ./nxn_gui_adapter.bend as GUI
import ./nxn_gui_render.bend as Render
import ./nxn_gui_history.bend as History
import ./nxn_gui_store.bend as Store

# Keep the affine game and its history together across image rendering.
def with_view(pair: Lazy.Game & Image,
              newest_first: List<&2, U32>, seed: U32) -> History.Model & Image:
  (game, image) = pair
  (History.Model{game, newest_first, seed}, image)

def view(model: History.Model) -> History.Model & Image:
  match model:
    case History.Model{game, newest_first, seed}:
      with_view(Render.view(game), newest_first, seed)

# A corrupt on-disk transcript must never replace the current live game.
def accept_load(current: History.Model, recovery: History.Recovery) -> History.Model:
  match recovery:
    case History.Corrupt{}:
      current
    case History.Restored{model}:
      model

def event(e: Event, model: History.Model) -> IO(Maybe<History.Model>):
  match e:
    case Close{}:
      IO.pure(Maybe<History.Model>, None{})
    case Key{27, True{}}:
      IO.pure(Maybe<History.Model>, None{})
    case Key{114, True{}}:
      IO.pure(Maybe<History.Model>, Some{History.reset(model)})
    case Key{82, True{}}:
      IO.pure(Maybe<History.Model>, Some{History.reset(model)})
    case Key{115, True{}}:
      do IO<Maybe<History.Model>>:
        saved: History.Model <- Store.save(model)
        return Some{saved}
    case Key{83, True{}}:
      do IO<Maybe<History.Model>>:
        saved: History.Model <- Store.save(model)
        return Some{saved}
    case Key{108, True{}}:
      do IO<Maybe<History.Model>>:
        recovery: History.Recovery <- Store.load()
        return Some{accept_load(model, recovery)}
    case Key{76, True{}}:
      do IO<Maybe<History.Model>>:
        recovery: History.Recovery <- Store.load()
        return Some{accept_load(model, recovery)}
    case Mouse{x, y, button, True{}}:
      IO.pure(Maybe<History.Model>, Some{History.pointer(model, x, y, button)})
    case _:
      IO.pure(Maybe<History.Model>, Some{model})

# Bend safe definitions cannot recurse mutually. A left fold builds one
# IO action chain; each step awaits the previous action before reading an event.
def apply_event(prev: Maybe<History.Model>, e: Event) -> IO(Maybe<History.Model>):
  match prev:
    case None{}:
      IO.pure(Maybe<History.Model>, None{})
    case Some{model}:
      event(e, model)

def fold_step(acc: IO(Maybe<History.Model>), e: Event) -> IO(Maybe<History.Model>):
  do IO<Maybe<History.Model>>:
    prev: Maybe<History.Model> <- acc
    apply_event(prev, e)

# Preserve OS event order, including S then R then L in the same frame.
# Once Close/Esc produces None, the remaining events cannot change state.
def handle_events(events: List<Event>, model: History.Model) -> IO(Maybe<History.Model>):
  List.foldl(~&1, ~Event, ~IO(Maybe<History.Model>), ~fold_step,
    events, IO.pure(Maybe<History.Model>, Some{model}))

def tick(events: List<Event>, model: History.Model) -> IO(Maybe<History.Model>):
  handle_events(events, model)

def main() -> IO(Unit):
  App.run(~History.Model, ~App{view, tick},
    "Minesweeper 10x10: left/right, R reset, S save, L load, Esc close",
    512, 512, History.new(20261029))
