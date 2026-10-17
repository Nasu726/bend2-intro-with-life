# Headless checks of GUI geometry, input and color mapping.
# The GUI window is not opened by this program.
import Base
import ./gui.bend as Gui
import ./game.bend as Game
import ./start.bend as Start
import ./session.bend as Session

def bit(value: Bool) -> U32:
  match value:
    case True{}:
      1
    case False{}:
      0

def index_or(value: Maybe<&2, U32>) -> U32:
  match value:
    case Some{index}:
      index
    case None{}:
      999

def square_code(s: Game.Square) -> U32:
  match s:
    case Game.Hidden{}:
      0
    case Game.Flag{}:
      1
    case Game.Open{clue}:
      (10 + clue : U32)

def loss_phase(p: Session.Phase) -> Bool:
  match p:
    case Session.Lost{}:
      True{}
    case _:
      False{}

def is_lost(stage: Start.Stage) -> Bool:
  match stage:
    case Start.Fresh{mines}:
      False{}
    case Start.Active{session}:
      loss_phase(Session.phase_of(session))

def main() -> U32:
  (
    bit(U32.is_eq(index_or(Gui.cell_at(0, 0)), 0)) +
    bit(U32.is_eq(index_or(Gui.cell_at(63, 0)), 0)) +
    bit(U32.is_eq(index_or(Gui.cell_at(64, 0)), 1)) +
    bit(U32.is_eq(index_or(Gui.cell_at(255, 255)), 15)) +
    bit(U32.is_eq(index_or(Gui.cell_at(256, 20)), 999)) +
    bit(U32.is_eq(index_or(Gui.cell_at(20, 256)), 999)) +
    bit(U32.is_eq(Gui.digit_bits(3), 79)) +
    bit(U32.is_eq(Gui.tile_pixel(9, 0, 1, 123), 123)) +
    bit(U32.is_eq(square_code(Start.visible_at(
      Gui.pointer(Start.new(33), 0, 0, 0), 0)), 12)) +
    bit(Start.is_fresh(Gui.pointer(Start.new(33), 0, 0, 1))) +
    bit(U32.is_eq(square_code(Start.visible_at(
      Gui.pointer(Gui.pointer(Start.new(33), 0, 0, 0), 64, 0, 1), 1)), 1)) +
    bit(is_lost(Gui.pointer(Gui.pointer(Start.new(33), 0, 0, 0), 64, 0, 0))) +
    bit(Start.is_fresh(Gui.pointer(Start.new(33), 0, 0, 2)))
    : U32
  )
