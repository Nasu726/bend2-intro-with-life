import Base

# The first argument is the column x, then the row y (both 0..3).
# Caller checks bounds; this is only a coordinate-to-index conversion.
def index(x: U32, y: U32) -> U32:
  (y * 4 + x : U32)
