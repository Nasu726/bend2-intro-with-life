# 10x10 GUI verification-only entry point. S saves, L loads public replay history.
# The 512x512 window has a 320x320 active area in the top-left corner.
import Base
import ./nxn_gui_history.bend as History
import ./nxn_gui_session.bend as Session

def main() -> IO(Unit):
  App.run(~History.Model, ~App{Session.view, Session.tick},
    "Minesweeper 10x10: left/right click, R reset, S save, L load, Esc close",
    512, 512, History.new(20261029))
