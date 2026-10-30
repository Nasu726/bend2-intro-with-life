# Stateful App.run boundary for the replayable 10x10 GUI.
# S saves public actions; L restores them from the versioned File payload.
# Missing/unreadable files currently cause Store.load to exit: see chapter 21.
import Base
import ./nxn_gui_history.bend as History
import ./nxn_gui_store.bend as Store
import ./nxn_gui_render.bend as Render
import ./nxn_lazy_game.bend as Lazy

def pair_with_history(pair: Lazy.Game & Image,
                      newest_first: List<&2, U32>, seed: U32) ->
  History.Model & Image:
  (game, image) = pair
  (History.Model{game, newest_first, seed}, image)

def view(model: History.Model) -> History.Model & Image:
  match model:
    case History.Model{game, newest_first, seed}:
      pair_with_history(Render.view(game), newest_first, seed)

def recovered(result: History.Recovery, fallback: History.Model) -> History.Model:
  match result:
    case History.Corrupt{}:
      fallback
    case History.Restored{model}:
      model

def save_event(model: History.Model) -> IO(Maybe<History.Model>):
  do IO<Maybe<History.Model>>:
    saved: History.Model <- Store.save(model)
    return Some{saved}

def load_event(model: History.Model) -> IO(Maybe<History.Model>):
  do IO<Maybe<History.Model>>:
    result: History.Recovery <- Store.load()
    return Some{recovered(result, model)}

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
      save_event(model)
    case Key{83, True{}}:
      save_event(model)
    case Key{108, True{}}:
      load_event(model)
    case Key{76, True{}}:
      load_event(model)
    case Mouse{x, y, button, True{}}:
      IO.pure(Maybe<History.Model>, Some{History.pointer(model, x, y, button)})
    case _:
      IO.pure(Maybe<History.Model>, Some{model})

def follow(rest: List<Event>, current: Maybe<History.Model>) ->
  IO(Maybe<History.Model>):
  match current:
    case None{}:
      IO.pure(Maybe<History.Model>, None{})
    case Some{model}:
      tick(rest, model)

def tick(events: List<Event>, model: History.Model) -> IO(Maybe<History.Model>):
  match events:
    case Nil{}:
      IO.pure(Maybe<History.Model>, Some{model})
    case e <> rest:
      do IO<Maybe<History.Model>>:
        current: Maybe<History.Model> <- event(e, model)
        follow(rest, current)

def main() -> U32:
  History.snapshot(History.new(20261029), 0)
