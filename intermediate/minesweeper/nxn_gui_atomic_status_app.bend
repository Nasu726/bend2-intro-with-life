# Experimental Linux/X11 GUI: reuse the shipped status view and controls,
# but route S through exclusive temporary creation + same-directory rename.
# This module is NOT in the reader ZIP allowlist; keep the shipped GUI unchanged
# until native X11 acceptance and PDF/ZIP source synchronization both succeed.
import Base
import ./nxn_gui_status_app.bend as Status
import ./nxn_gui_atomic_store.bend as Atomic
import ./nxn_gui_history.bend as History

def view(state: Status.State) -> Status.State & Image:
  Status.view(state)

def save_state(state: Status.State) -> IO(Status.State):
  match state:
    case Status.State{model, notice}:
      do IO<Status.State>:
        result: History.Model & Bool <- Atomic.save_atomic_report(model)
        return Status.after_save(result)

def resume_io(action: IO(Status.State)) -> IO(Maybe<Status.State>):
  do IO<Maybe<Status.State>>:
    next: Status.State <- action
    return Some{next}

def event(e: Event, state: Status.State) -> IO(Maybe<Status.State>):
  match e:
    case Key{115, True{}}:
      resume_io(save_state(state))
    case Key{83, True{}}:
      resume_io(save_state(state))
    case _:
      Status.event(e, state)

def apply_event(prev: Maybe<Status.State>, e: Event) -> IO(Maybe<Status.State>):
  match prev:
    case None{}:
      IO.pure(Maybe<Status.State>, None{})
    case Some{state}:
      event(e, state)

def fold_step(acc: IO(Maybe<Status.State>), e: Event) -> IO(Maybe<Status.State>):
  do IO<Maybe<Status.State>>:
    prev: Maybe<Status.State> <- acc
    apply_event(prev, e)

def tick(events: List<Event>, state: Status.State) -> IO(Maybe<Status.State>):
  List.foldl(~&1, ~Event, ~IO(Maybe<Status.State>), ~fold_step,
    events, IO.pure(Maybe<Status.State>, Some{state}))

def main() -> IO(Unit):
  App.run(~Status.State, ~App{view, tick},
    "Minesweeper 10x10 experimental atomic save (Linux only)",
    512, 512, Status.State{History.new(20261029), 0})
