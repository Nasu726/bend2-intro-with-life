# 4x4 playable Minesweeper window using the same Start/Session engine as the CLI.
# Left click: reveal. Right click: toggle flag. R: restart. Esc: close.
# Every 64x64 tile has a dark grid border and a small seven-segment digit.
# This GUI still needs a real desktop for interactive acceptance testing.
import Base
import ./game.bend as Game
import ./board4.bend as Board4
import ./session.bend as Session
import ./start.bend as Start

def choose(c: Bool, a: U32, b: U32) -> U32:
  match c:
    case True{}:
      a
    case False{}:
      b

def square_code(s: Game.Square) -> U32:
  match s:
    case Game.Hidden{}:
      9
    case Game.Flag{}:
      10
    case Game.Open{clue}:
      clue

# Seven-segment bits: a=1, b=2, c=4, d=8, e=16, f=32, g=64.
def digit_bits(+code: U32) -> U32:
  choose(U32.is_eq(code, 1), 6,
  choose(U32.is_eq(code, 2), 91,
  choose(U32.is_eq(code, 3), 79,
  choose(U32.is_eq(code, 4), 102,
  choose(U32.is_eq(code, 5), 109,
  choose(U32.is_eq(code, 6), 125,
  choose(U32.is_eq(code, 7), 7,
  choose(U32.is_eq(code, 8), 127, 0))))))))

def rect(+x: U32, +y: U32, x0: U32, x1: U32, y0: U32, y1: U32) -> Bool:
  Bool.and(Bool.and(U32.is_ge(x, x0), U32.is_lt(x, x1)),
    Bool.and(U32.is_ge(y, y0), U32.is_lt(y, y1)))

def lit(bits: U32, bit: U32, +x: U32, +y: U32,
        x0: U32, x1: U32, y0: U32, y1: U32) -> Bool:
  Bool.and(Board4.bit_is_set(bits, bit), rect(x, y, x0, x1, y0, y1))

def digit_pixel(+code: U32, +x: U32, +y: U32) -> Bool:
  +bits = digit_bits(code)
  (lit(bits, 1, x, y, 2, 6, 1, 2) ||
   lit(bits, 2, x, y, 5, 6, 2, 4) ||
   lit(bits, 4, x, y, 5, 6, 4, 6) ||
   lit(bits, 8, x, y, 2, 6, 6, 7) ||
   lit(bits, 16, x, y, 2, 3, 4, 6) ||
   lit(bits, 32, x, y, 2, 3, 2, 4) ||
   lit(bits, 64, x, y, 2, 6, 3, 4) : Bool)

def opened_color(+code: U32, +x: U32, +y: U32) -> U32:
  choose(U32.is_eq(code, 0), 15658734,
    choose(digit_pixel(code, x, y), 1578496, 15658734))

def flag_color(+x: U32, +y: U32) -> U32:
  choose(rect(x, y, 3, 6, 2, 5), 14704438, 11579568)

def tile_pixel(+code: U32, +x: U32, +y: U32, border: U32) -> U32:
  choose(Bool.or(U32.is_eq(x, 0), U32.is_eq(y, 0)), border,
    choose(U32.is_eq(code, 9), 8689825,
      choose(U32.is_eq(code, 10), flag_color(x, y),
        opened_color(code, x, y))))

# A 64x64 tile. Each Pix covers an 8x8 block on screen.
def tile_draw(d: Nat, +code: U32, +border: U32, +x: U32, +y: U32) -> Image:
  match d:
    case 0n:
      Pix{tile_pixel(code, x, y, border)}
    case 1n+k:
      +h = U32.shln(1, k)
      +x1 = (x + h : U32)
      +y1 = (y + h : U32)
      tl tr bl br = tile_draw(k, code, border, x, y)
        tile_draw(k, code, border, x1, y)
        tile_draw(k, code, border, x, y1)
        tile_draw(k, code, border, x1, y1)
      Qua{tl, tr, bl, br}

def tile(square: Game.Square, border: U32) -> Image:
  tile_draw(3n, square_code(square), border, 0, 0)

# Consume each of the 16 visible cells once; never inspect the mine mask.
def board_picture(cells: List<Game.Square>, +border: U32) -> Image:
  match cells:
    case a <> b <> c <> d <> e <> f <> g <> h <> i <> j <> k <> l <> m <> n <> o <> p <> rest:
      Qua{
        Qua{tile(a, border), tile(b, border),
            tile(e, border), tile(f, border)},
        Qua{tile(c, border), tile(d, border),
            tile(g, border), tile(h, border)},
        Qua{tile(i, border), tile(j, border),
            tile(m, border), tile(n, border)},
        Qua{tile(k, border), tile(l, border),
            tile(o, border), tile(p, border)}}
    case _:
      Pix{border}

def fresh_picture() -> Image:
  board_picture([
    Game.Hidden{}, Game.Hidden{}, Game.Hidden{}, Game.Hidden{},
    Game.Hidden{}, Game.Hidden{}, Game.Hidden{}, Game.Hidden{},
    Game.Hidden{}, Game.Hidden{}, Game.Hidden{}, Game.Hidden{},
    Game.Hidden{}, Game.Hidden{}, Game.Hidden{}, Game.Hidden{}], 2697513)

# Open state preserves its affine Array via Array.clone.
def active_view(+mines: U32, +phase: Session.Phase,
                pair: Array<Game.Square> & Array<Game.Square>) ->
                Start.Stage & Image:
  (keep, inspect) = pair
  border = phase_border(phase)
  (Start.Active{Session.Session{Board4.State{mines, keep}, phase}},
    board_picture(Array.to_list(Game.Square, inspect), border))

def phase_border(phase: Session.Phase) -> U32:
  match phase:
    case Session.Playing{}:
      2697513
    case Session.Won{}:
      3030856
    case Session.Lost{}:
      12066878

def view(stage: Start.Stage) -> Start.Stage & Image:
  match stage:
    case Start.Fresh{mines}:
      (Start.Fresh{mines}, fresh_picture())
    case Start.Active{session}:
      match session:
        case Session.Session{board, phase}:
          match board:
            case Board4.State{mines, cells}:
              active_view(mines, phase, Array.clone(Game.Square, cells))

def cell_if_valid(valid: Bool, x: U32, y: U32) -> Maybe<&2, U32>:
  match valid:
    case True{}:
      Some{(U32.div(y, 64) * 4 + U32.div(x, 64) : U32)}
    case False{}:
      None{}

def cell_at(+x: U32, +y: U32) -> Maybe<&2, U32>:
  cell_if_valid(Bool.and(U32.is_lt(x, 256), U32.is_lt(y, 256)), x, y)

def flag(stage: Start.Stage, index: U32) -> Start.Stage:
  match stage:
    case Start.Fresh{mines}:
      Start.Fresh{mines}
    case Start.Active{session}:
      Start.Active{Session.mark(session, index)}

def mouse_mode(right: Bool, stage: Start.Stage, index: U32) -> Start.Stage:
  match right:
    case True{}:
      flag(stage, index)
    case False{}:
      Start.click(stage, index)

def mouse_index(index: Maybe<&2, U32>, stage: Start.Stage, button: U32) -> Start.Stage:
  match index:
    case None{}:
      stage
    case Some{i}:
      mouse_mode(U32.is_eq(button, 1), stage, i)

def pointer(stage: Start.Stage, x: U32, y: U32, button: U32) -> Start.Stage:
  mouse_index(cell_at(x, y), stage, button)

def event(e: Event, stage: Start.Stage) -> Maybe<Start.Stage>:
  match e:
    case Close{}:
      None{}
    case Key{27, True{}}:
      None{}
    case Key{114, True{}}:
      Some{Start.new(33)}
    case Mouse{x, y, button, True{}}:
      Some{pointer(stage, x, y, button)}
    case _:
      Some{stage}

def handle_events(events: List<Event>, stage: Start.Stage) -> Maybe<Start.Stage>:
  match events:
    case Nil{}:
      Some{stage}
    case e <> rest:
      Maybe.bind(&1, Start.Stage, Start.Stage, event(e, stage),
        next => handle_events(rest, next))

def tick(events: List<Event>, stage: Start.Stage) -> IO(Maybe<Start.Stage>):
  IO.pure(Maybe<Start.Stage>, handle_events(events, stage))

def main() -> IO(Unit):
  App.run(~Start.Stage, ~App{view, tick}, "Minesweeper: left/right click, R restart",
    256, 256, Start.new(33))
