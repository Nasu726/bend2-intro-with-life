import Base

# A pure Image is a tree of colored square regions.
# We inspect the top-left path without opening a GUI.
def top_left_color(img: Image) -> U32:
  match img:
    case Pix{color}:
      color
    case Qua{tl, tr, bl, br}:
      top_left_color(tl)

def make_icon() -> Image:
  Qua{Pix{16711680}, Pix{0}, Pix{0}, Pix{0}}

def main() -> U32:
  top_left_color(make_icon())
