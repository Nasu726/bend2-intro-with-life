# G-01: player's first-left-click controller, specified in LAWS.bend.
# Keep Session.new separate: it models an already placed active board.
import Base
import ./game.bend as Game
import ./board4.bend as Board4
import ./session.bend as Session

type Stage is Type:
  Fresh{mines: U32}
  Active{session: Session.Session}

def new(mines: U32) -> Stage:
  Fresh{U32.and(mines, 65535)}

# The lowest set bit of a nonzero word gives the first available cell.
def lowest_bit(+word: U32) -> U32:
  U32.and(word, U32.sub(0, word))

# A mine under the first click moves to the lowest unoccupied index.
# 16 mines cannot be safely placed on 16 cells: callers remain Fresh.
def relocate_if_needed(is_mine: Bool, +mines: U32, bit: U32) -> U32:
  match is_mine:
    case False{}:
      mines
    case True{}:
      free = U32.and(U32.not(mines), 65535)
      destination = lowest_bit(free)
      U32.xor(U32.xor(mines, bit), destination)

def relocate_normalized(+mines: U32, +bit: U32) -> U32:
  relocate_if_needed(Board4.bit_is_set(mines, bit), mines, bit)

def relocate(mines: U32, index: U32) -> U32:
  relocate_normalized(U32.and(mines, 65535), U32.shln(1, U32.to_nat(index)))

def start_if_valid(valid: Bool, mines: U32, index: U32) -> Stage:
  match valid:
    case False{}:
      Fresh{mines}
    case True{}:
      Active{Session.click(Session.new(relocate(mines, index)), index)}

def begin_fresh(+mines: U32, +index: U32) -> Stage:
  start_if_valid(
    Bool.and(U32.is_lt(index, 16), U32.is_ne(mines, 65535)),
    mines, index)

def click(stage: Stage, index: U32) -> Stage:
  match stage:
    case Fresh{mines}:
      begin_fresh(mines, index)
    case Active{session}:
      Active{Session.click(session, index)}

def is_fresh(stage: Stage) -> Bool:
  match stage:
    case Fresh{mines}:
      True{}
    case Active{session}:
      False{}

def session_mask(s: Session.Session) -> U32:
  match s:
    case Session.Session{board, phase}:
      Board4.mine_mask(board)

def mine_mask(stage: Stage) -> U32:
  match stage:
    case Fresh{mines}:
      mines
    case Active{session}:
      session_mask(session)

def visible_at(stage: Stage, index: U32) -> Game.Square:
  match stage:
    case Fresh{mines}:
      Game.Hidden{}
    case Active{session}:
      Session.read_square(session, index)
