# 10x10 GUI entry point. Requires a graphical desktop; no desktop CI assertion.
# The 512x512 window has a 320x320 active area in the top-left corner.
import Base
import ./nxn_lazy_game.bend as Lazy
import ./nxn_gui_adapter.bend as GUI
import ./nxn_gui_events.bend as Events
import ./nxn_gui_render.bend as Render

def view(game: Lazy.Game) -> Lazy.Game & Image:
  Render.view(game)

def tick(events: List<Event>, game: Lazy.Game) -> IO(Maybe<Lazy.Game>):
  Events.tick(events, game, 20261029)

def main() -> IO(Unit):
  App.run(~Lazy.Game, ~App{view, tick},
    "Minesweeper 10x10: left/right click, R reset, Esc close",
    512, 512, GUI.reset_gui(20261029))
