# Pure 10x10 lazy-game view. The 16x16 Image canvas is scaled to 512x512.
# The playable top-left 10x10 cells occupy 320x320 pixels; the rest is padding.
# Never consult mine truth: the view uses only public Game.Square values.
import Base
import ./game.bend as Game
import ./nxn_lazy_game.bend as Lazy
import ./nxn_mine_words.bend as Words
import ./nxn_step.bend as Step
import ./nxn_terminal.bend as Terminal

def choose(c: Bool, yes: U32, no: U32) -> U32:
  match c:
    case True{}:
      yes
    case False{}:
      no

# 0=Hidden, 1=Flag, 10..18=Open{clue}, 99=canvas padding.
def cell_color(+code: U32) -> U32:
  choose(U32.is_eq(code, 0), 8689825,
    choose(U32.is_eq(code, 1), 14704438,
      choose(U32.is_eq(code, 10), 15658734,
        choose(U32.is_lt(code, 19), 1578496, 0))))

# The cloned Array becomes a list. Only the first 100 logical cells are read.
def list_code(fuel: Nat, cells: List<Game.Square>) -> U32:
  match cells:
    case Nil{}:
      99
    case square <> rest:
      match fuel:
        case 0n:
          Step.square_code(square)
        case 1n+k:
          list_code(k, rest)

def visible_code(valid: Bool, cells: List<Game.Square>, +x: U32, +y: U32) -> U32:
  match valid:
    case True{}:
      list_code(U32.to_nat((y * 10 + x : U32)), cells)
    case False{}:
      99

# Each tile has an 8x8 logical pixel grid, with a border and digit glyph.
# A 16x16 grid of tiles is a 128x128 Image, scaled 4x to 512x512.
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
  Bool.and(U32.is_ne(U32.and(bits, bit), 0), rect(x, y, x0, x1, y0, y1))

def digit_pixel(+code: U32, +x: U32, +y: U32) -> Bool:
  +bits = digit_bits(code)
  (lit(bits, 1, x, y, 2, 6, 1, 2) ||
   lit(bits, 2, x, y, 5, 6, 2, 4) ||
   lit(bits, 4, x, y, 5, 6, 4, 6) ||
   lit(bits, 8, x, y, 2, 6, 6, 7) ||
   lit(bits, 16, x, y, 2, 3, 4, 6) ||
   lit(bits, 32, x, y, 2, 3, 2, 4) ||
   lit(bits, 64, x, y, 2, 6, 3, 4) : Bool)

def tile_pixel(+code: U32, +x: U32, +y: U32) -> U32:
  choose(U32.is_eq(code, 99), 0,
    choose(Bool.or(U32.is_eq(x, 0), U32.is_eq(y, 0)), 2697513,
      choose(U32.is_eq(code, 0), 8689825,
        choose(U32.is_eq(code, 1),
          choose(rect(x, y, 3, 6, 2, 5), 14704438, 11579568),
          choose(digit_pixel((code - 10 : U32), x, y), 1578496, 15658734)))))

# A tile is 8x8 logical pixels, so 32x32 screen pixels at 4x scale.
def tile_draw(+depth: Nat, +code: U32, +x: U32, +y: U32) -> Image:
  match depth:
    case 0n:
      Pix{tile_pixel(code, x, y)}
    case 1n+k:
      +half = U32.shln(1, k)
      tl tr bl br = tile_draw(k, code, x, y)
        tile_draw(k, code, (x + half : U32), y)
        tile_draw(k, code, x, (y + half : U32))
        tile_draw(k, code, (x + half : U32), (y + half : U32))
      Qua{tl, tr, bl, br}

# Only public square codes are passed to the recursive image constructor.
def picture(+depth: Nat, +x: U32, +y: U32, +cells: List<Game.Square>) -> Image:
  match depth:
    case 0n:
      tile_draw(3n, visible_code(
        Bool.and(U32.is_lt(x, 10), U32.is_lt(y, 10)), cells, x, y), 0, 0)
    case 1n+k:
      +half = U32.shln(1, k)
      tl tr bl br = picture(k, x, y, cells)
        picture(k, (x + half : U32), y, cells)
        picture(k, x, (y + half : U32), cells)
        picture(k, (x + half : U32), (y + half : U32), cells)
      Qua{tl, tr, bl, br}

def fresh_picture() -> Image:
  picture(4n, 0, 0,
    Array.to_list(Game.Square, Array.new(Game.Square, 7n, Game.Hidden{})))

# Keep the original affine visible Array in the game; inspect only its clone.
def view_cloned(n: U32, mines: Words.MineWords, phase: Step.Phase,
                pair: Array<Game.Square> & Array<Game.Square>) -> Step.Session & Image:
  (keep, inspect) = pair
  (Step.Session{n, mines, keep, phase},
   picture(4n, 0, 0, Array.to_list(Game.Square, inspect)))

def view_session(session: Step.Session) -> Step.Session & Image:
  match session:
    case Step.Session{n, mines, cells, phase}:
      view_cloned(n, mines, phase, Array.clone(Game.Square, cells))

def playing_view(pair: Step.Session & Image) -> Terminal.State & Image:
  (session, img) = pair
  (Terminal.Playing{session}, img)

def won_view(pair: Step.Session & Image) -> Terminal.State & Image:
  (session, img) = pair
  (Terminal.Won{session}, img)

def lost_view(pair: Step.Session & Image) -> Terminal.State & Image:
  (session, img) = pair
  (Terminal.Lost{session}, img)

def view_state(state: Terminal.State) -> Terminal.State & Image:
  match state:
    case Terminal.Playing{session}:
      playing_view(view_session(session))
    case Terminal.Won{session}:
      won_view(view_session(session))
    case Terminal.Lost{session}:
      lost_view(view_session(session))

def active_view(pair: Terminal.State & Image) -> Lazy.Game & Image:
  (state, img) = pair
  (Lazy.Active{state}, img)

def view(game: Lazy.Game) -> Lazy.Game & Image:
  match game:
    case Lazy.Fresh{n, count, seed}:
      (Lazy.Fresh{n, count, seed}, fresh_picture())
    case Lazy.Active{state}:
      active_view(view_state(state))
    case Lazy.Invalid{}:
      (Lazy.Invalid{}, Pix{0})

# Headless pixel sampler: select a quadrant without inspecting mine truth.
def choose_x(right: Bool, left: Image, right_image: Image) -> Image:
  match right:
    case True{}:
      right_image
    case False{}:
      left

def choose_quadrant(bottom: Bool, right: Bool,
                    tl: Image, tr: Image, bl: Image, br: Image) -> Image:
  match bottom:
    case True{}:
      choose_x(right, bl, br)
    case False{}:
      choose_x(right, tl, tr)

def pixel_at(img: Image, +x: U32, +y: U32, +size: U32) -> U32:
  match img:
    case Pix{color}:
      color
    case Qua{tl, tr, bl, br}:
      +half = U32.div(size, 2)
      pixel_at(choose_quadrant(U32.is_ge(y, half), U32.is_ge(x, half),
                              tl, tr, bl, br),
               U32.mod(x, half), U32.mod(y, half), half)

def top_left(img: Image) -> U32:
  match img:
    case Pix{color}:
      color
    case Qua{tl, tr, bl, br}:
      top_left(tl)

def bottom_right(img: Image) -> U32:
  match img:
    case Pix{color}:
      color
    case Qua{tl, tr, bl, br}:
      bottom_right(br)

def main() -> U32:
  pixel_at(fresh_picture(), 1, 1, 128)
