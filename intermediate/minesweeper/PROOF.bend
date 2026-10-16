# Each 'def Laws.name' discharges a requirement in LAWS.bend.
# These are not example-only assertions: the quantified properties are proven
# for all values of their declared types, subject to the modeled scope.
import Base
import ./LAWS.bend as Laws

def Laws.hidden_is_flagged():
  {==}

def Laws.flagged_is_hidden():
  {==}

def Laws.opened_ignores_flag(clue):
  {==}

def Laws.flag_toggle_involution(s):
  match s:
    case Laws.Game.Hidden{}:
      {==}
    case Laws.Game.Flag{}:
      {==}
    case Laws.Game.Open{clue}:
      {==}

def Laws.reveal_hidden(clue):
  {==}

def Laws.reveal_flagged(clue):
  {==}

def Laws.reveal_opened(old_clue, new_clue):
  {==}
