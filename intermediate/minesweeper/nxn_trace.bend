# Pure replay of a typed N x N click/flag trace (n=2..100).
# No IO and no access to mine truth from the action list. The initial board
# remains internal to the game; this is a bridge toward CLI and GUI inputs.
import Base
import ./nxn_mine_words.bend as Words
import ./nxn_full_game.bend as Full

type Action is Data:
  Click{index: U32}
  Mark{index: U32}

def apply(game: Full.Game, action: Action) -> Full.Game:
  match action:
    case Click{index}:
      Full.click(game, index)
    case Mark{index}:
      Full.mark(game, index)

# Put the structurally decreasing list first. The linear game is consumed
# and returned at every step, including after Won or Lost.
def replay(actions: List<Action>, game: Full.Game) -> Full.Game:
  match actions:
    case Nil{}:
      game
    case action <> rest:
      replay(rest, apply(game, action))

def main() -> U32:
  board = Words.set_checked(Words.new(2), 3, True{})
  game = replay([Click{0}, Mark{1}], Full.new(board))
  Full.snapshot(game, 0)
