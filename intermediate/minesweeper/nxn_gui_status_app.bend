# Verification-only 10x10 GUI with an observable S/L outcome.
# The 32x32 square at x=384..415, y=0..31 is outside the playable board.
# Green: S succeeded; blue: L succeeded; red: S failed; amber: L failed.
# A mouse press or reset clears the marker; all public game cells are unchanged.
import Base
import ./nxn_gui_history.bend as History
import ./nxn_gui_render.bend as Render
import ./nxn_gui_store.bend as Store
import ./nxn_lazy_game.bend as Lazy

type State is Type:
  State{model: History.Model, notice: U32}

def notice_color(+notice: U32) -> U32:
  Render.choose(U32.is_eq(notice, 1), 65280,
    Render.choose(U32.is_eq(notice, 2), 255,
      Render.choose(U32.is_eq(notice, 3), 16711680, 16753920)))

# Four levels isolate one tile in the non-interactive right-hand gutter.
def mark4(img: Image, color: U32) -> Image:
  match img:
    case Pix{old}:
      Pix{color}
    case Qua{tl, tr, bl, br}:
      Qua{Pix{color}, tr, bl, br}

def mark3(img: Image, color: U32) -> Image:
  match img:
    case Pix{old}:
      Pix{color}
    case Qua{tl, tr, bl, br}:
      Qua{mark4(tl, color), tr, bl, br}

def mark2(img: Image, color: U32) -> Image:
  match img:
    case Pix{old}:
      Pix{color}
    case Qua{tl, tr, bl, br}:
      Qua{tl, mark3(tr, color), bl, br}

def mark1(img: Image, color: U32) -> Image:
  match img:
    case Pix{old}:
      Pix{color}
    case Qua{tl, tr, bl, br}:
      Qua{tl, mark2(tr, color), bl, br}

def mark_if(show: Bool, img: Image, color: U32) -> Image:
  match show:
    case False{}:
      img
    case True{}:
      mark1(img, color)

def attach_view(pair: History.Model & Image, +notice: U32) -> State & Image:
  (model, img) = pair
  (State{model, notice},
   mark_if(U32.is_ne(notice, 0), img, notice_color(notice)))

# Destructure the Render.view result in a function parameter. Directly
# destructuring a computed result in a branch is not accepted by Bend 2.0.39.
def with_rendered_game(pair: Lazy.Game & Image, newest_first: List<&2, U32>,
                       seed: U32, notice: U32) -> State & Image:
  (game, img) = pair
  attach_view((History.Model{game, newest_first, seed}, img), notice)

def view(state: State) -> State & Image:
  match state:
    case State{model, notice}:
      match model:
        case History.Model{game, newest_first, seed}:
          with_rendered_game(Render.view(game), newest_first, seed, notice)

def after_save(pair: History.Model & Bool) -> State:
  (model, ok) = pair
  match ok:
    case True{}:
      State{model, 1}
    case False{}:
      State{model, 3}

def after_load(model: History.Model, result: History.Recovery) -> State:
  match result:
    case History.Corrupt{}:
      State{model, 4}
    case History.Restored{restored}:
      State{restored, 2}

def event(e: Event, state: State) -> IO(Maybe<State>):
  match state:
    case State{model, notice}:
      match e:
        case Close{}:
          IO.pure(Maybe<State>, None{})
        case Key{27, True{}}:
          IO.pure(Maybe<State>, None{})
        case Key{114, True{}}:
          IO.pure(Maybe<State>, Some{State{History.reset(model), 0}})
        case Key{82, True{}}:
          IO.pure(Maybe<State>, Some{State{History.reset(model), 0}})
        case Key{115, True{}}:
          do IO<Maybe<State>>:
            outcome: History.Model & Bool <- Store.save_report(model)
            return Some{after_save(outcome)}
        case Key{83, True{}}:
          do IO<Maybe<State>>:
            outcome: History.Model & Bool <- Store.save_report(model)
            return Some{after_save(outcome)}
        case Key{108, True{}}:
          do IO<Maybe<State>>:
            recovery: History.Recovery <- Store.load()
            return Some{after_load(model, recovery)}
        case Key{76, True{}}:
          do IO<Maybe<State>>:
            recovery: History.Recovery <- Store.load()
            return Some{after_load(model, recovery)}
        case Mouse{x, y, button, True{}}:
          IO.pure(Maybe<State>, Some{State{History.pointer(model, x, y, button), 0}})
        case _:
          IO.pure(Maybe<State>, Some{State{model, notice}})

def apply_event(prev: Maybe<State>, e: Event) -> IO(Maybe<State>):
  match prev:
    case None{}:
      IO.pure(Maybe<State>, None{})
    case Some{state}:
      event(e, state)

def fold_step(acc: IO(Maybe<State>), e: Event) -> IO(Maybe<State>):
  do IO<Maybe<State>>:
    prev: Maybe<State> <- acc
    apply_event(prev, e)

def tick(events: List<Event>, state: State) -> IO(Maybe<State>):
  List.foldl(~&1, ~Event, ~IO(Maybe<State>), ~fold_step,
    events, IO.pure(Maybe<State>, Some{state}))

def main() -> IO(Unit):
  App.run(~State, ~App{view, tick},
    "Minesweeper 10x10 S/L indicator: green/blue good red/amber error",
    512, 512, State{History.new(20261029), 0})
