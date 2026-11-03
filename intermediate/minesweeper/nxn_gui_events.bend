# Event delivery boundary for the 10x10 lazy GUI; no renderer or App.run.
import Base
import ./nxn_lazy_game.bend as Lazy
import ./nxn_gui_adapter.bend as GUI

def event(e: Event, game: Lazy.Game, seed: U32) -> Maybe<Lazy.Game>:
  match e:
    case Close{}:
      None{}
    case Key{27, True{}}:
      None{}
    case Key{114, True{}}:
      Some{GUI.reset_gui(seed)}
    case Key{82, True{}}:
      Some{GUI.reset_gui(seed)}
    case Mouse{x, y, button, True{}}:
      Some{GUI.pointer(game, x, y, button)}
    case _:
      Some{game}

def handle_events(events: List<Event>, game: Lazy.Game, +seed: U32) -> Maybe<Lazy.Game>:
  match events:
    case Nil{}:
      Some{game}
    case e <> rest:
      Maybe.bind(&1, Lazy.Game, Lazy.Game, event(e, game, seed),
        next => handle_events(rest, next, seed))

def tick(events: List<Event>, game: Lazy.Game, seed: U32) -> IO(Maybe<Lazy.Game>):
  IO.pure(Maybe<Lazy.Game>, handle_events(events, game, seed))

def main() -> U32:
  GUI.snapshot(GUI.reset_gui(20261029), 0)
