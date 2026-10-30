# Pure replayable 10x10 GUI action history. File IO and App.run wiring follow.
# The accepted initial seed is recorded; no mine truth exists before first click.
# History stores (2*cell + button), where button=0 reveal and 1 flag.
# Invalid pixel/button input is ignored. A reset clears old commands.
import Base
import ./nxn_lazy_game.bend as Lazy
import ./nxn_gui_adapter.bend as GUI

type Model is Type:
  Model{game: Lazy.Game, newest_first: List<&2, U32>, seed: U32}

type Recovery is Type:
  Restored{model: Model}
  Corrupt{}

def new(+seed: U32) -> Model:
  Model{GUI.reset_gui(seed), Nil{}, seed}

def reset(model: Model) -> Model:
  match model:
    case Model{game, newest_first, seed}:
      new(seed)

def code(+index: U32, +button: U32) -> U32:
  (index * 2 + button : U32)

def use_code(game: Lazy.Game, +entry: U32) -> Lazy.Game:
  +index = U32.div(entry, 2)
  +button = U32.mod(entry, 2)
  GUI.pointer_n(game, 10,
    (U32.mod(index, 10) * 32 + 16 : U32),
    (U32.div(index, 10) * 32 + 16 : U32), button)

def recorded(model: Model, +index: U32, +button: U32) -> Model:
  match model:
    case Model{game, newest_first, seed}:
      Model{use_code(game, code(index, button)),
            code(index, button) <> newest_first, seed}

def if_cell(index: Maybe<&2, U32>, model: Model, button: U32) -> Model:
  match index:
    case None{}:
      model
    case Some{index}:
      recorded(model, index, button)

def if_button(valid: Bool, model: Model, +x: U32, +y: U32, +button: U32) -> Model:
  match valid:
    case False{}:
      model
    case True{}:
      if_cell(GUI.cell_at(10, x, y), model, button)

def pointer(model: Model, +x: U32, +y: U32, +button: U32) -> Model:
  if_button(U32.is_lt(button, 2), model, x, y, button)

def replay(entries: List<&2, U32>, game: Lazy.Game) -> Lazy.Game:
  match entries:
    case Nil{}:
      game
    case entry <> rest:
      replay(rest, use_code(game, entry))

def valid_entries(entries: List<&2, U32>) -> Bool:
  match entries:
    case Nil{}:
      True{}
    case entry <> rest:
      Bool.and(U32.is_lt(entry, 20000), valid_entries(rest))

def on_valid(valid: Bool, +entries: List<&2, U32>, +seed: U32) -> Recovery:
  match valid:
    case False{}:
      Corrupt{}
    case True{}:
      Restored{Model{replay(entries, GUI.reset_gui(seed)),
                     List.reverse(&2, U32, entries), seed}}

# Serialized data is chronological. Maximum 512 input actions per save.
# A rejected transcript never gets partially applied.
def restore(+seed: U32, +entries: List<&2, U32>) -> Recovery:
  on_valid(Bool.and(Nat.is_le(List.length(&2, U32, entries), 512n),
                    valid_entries(entries)), entries, seed)

def history(model: Model) -> List<&2, U32>:
  match model:
    case Model{game, newest_first, seed}:
      List.reverse(&2, U32, newest_first)

def snapshot(model: Model, index: U32) -> U32:
  match model:
    case Model{game, newest_first, seed}:
      GUI.snapshot(game, index)

def recovered_snapshot(result: Recovery, index: U32) -> U32:
  match result:
    case Corrupt{}:
      600
    case Restored{model}:
      snapshot(model, index)

def main() -> U32:
  recovered_snapshot(restore(20261029, [0, 199]), 99)
