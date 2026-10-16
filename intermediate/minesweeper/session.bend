# Pure click/flag/phase rules. Contract: LAWS.bend (G-series).
# No first-click placement, zero expansion, GUI or solver in this milestone.
import Base
import ./game.bend as Game
import ./board4.bend as Board4

type Phase is Data:
  Playing{}
  Won{}
  Lost{}

type Session is Type:
  Session{board: Board4.State, phase: Phase}

def new(mines: U32) -> Session:
  Session{Board4.new_state(mines), Playing{}}

def phase_of(s: Session) -> Phase:
  match s:
    case Session{board, phase}:
      phase

def read_square(s: Session, index: U32) -> Game.Square:
  match s:
    case Session{board, phase}:
      Board4.visible_at(board, index)

def mark(s: Session, index: U32) -> Session:
  match s:
    case Session{board, phase}:
      match phase:
        case Playing{}:
          Session{Board4.toggle_checked(board, index), Playing{}}
        case Won{}:
          Session{board, Won{}}
        case Lost{}:
          Session{board, Lost{}}

def finish(result: Board4.State & Bool) -> Session:
  (board, complete) = result
  match complete:
    case True{}:
      Session{board, Won{}}
    case False{}:
      Session{board, Playing{}}

# Mines are examined ONLY here, after confirming the clicked cell is Hidden.
def open_safe(+mines: U32, cells: Array<Game.Square>, +index: U32) -> Session:
  clue = Board4.clue(mines, U32.mod(index, 4), U32.div(index, 4))
  board = Board4.reveal_at(Board4.State{mines, cells}, index, clue)
  finish(Board4.check_won(board))

def click_hidden(is_mine: Bool, mines: U32, cells: Array<Game.Square>, index: U32) -> Session:
  match is_mine:
    case True{}:
      Session{Board4.State{mines, cells}, Lost{}}
    case False{}:
      open_safe(mines, cells, index)

def click_read(+mines: U32, index: U32, read: Array<Game.Square> & Game.Square) -> Session:
  (cells, square) = read
  match square:
    case Game.Hidden{}:
      click_hidden(Board4.bit_is_set(mines, U32.shln(1, U32.to_nat(index))), mines, cells, index)
    case Game.Flag{}:
      Session{Board4.State{mines, cells}, Playing{}}
    case Game.Open{clue}:
      Session{Board4.State{mines, cells}, Playing{}}

def click_valid(valid: Bool, board: Board4.State, index: U32) -> Session:
  match valid:
    case False{}:
      Session{board, Playing{}}
    case True{}:
      match board:
        case Board4.State{mines, cells}:
          click_read(mines, index, Array.get(Game.Square, cells, index))

def click(s: Session, +index: U32) -> Session:
  match s:
    case Session{board, phase}:
      match phase:
        case Playing{}:
          click_valid(U32.is_lt(index, 16), board, index)
        case Won{}:
          Session{board, Won{}}
        case Lost{}:
          Session{board, Lost{}}
