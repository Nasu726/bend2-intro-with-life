# Finite, non-wrapping N x N coordinates for the variable-size game.
# Valid board sizes are 2..100. Coordinates use x=column, y=row.
# Geometry only: this is NOT a complete variable-size game engine.
import Base

def valid_size(+n: U32) -> Bool:
  Bool.and(U32.is_lt(1, n), U32.is_lt(n, 101))

def in_bounds(+n: U32, +x: U32, +y: U32) -> Bool:
  Bool.and(valid_size(n), Bool.and(U32.is_lt(x, n), U32.is_lt(y, n)))

# PRECONDITION: in_bounds(n,x,y). Use checked_index for untrusted input.
def index(+n: U32, +x: U32, +y: U32) -> U32:
  (y * n + x : U32)

def checked_index(+n: U32, +x: U32, +y: U32) -> Maybe<&2, U32>:
  match in_bounds(n, x, y):
    case True{}:
      Some{index(n, x, y)}
    case False{}:
      None{}

# Array.get wraps invalid indices: 100..127 are padding, not cells,
# when a 10x10 board uses a 128-slot Array.
def valid_index(+n: U32, +i: U32) -> Bool:
  Bool.and(valid_size(n), U32.is_lt(i, (n * n : U32)))

# Adjacent or equal; no unsigned subtraction. Call only via neighbor,
# which validates both coordinate pairs.
def close(+a: U32, +b: U32) -> Bool:
  Bool.or(U32.is_eq(a, b),
    Bool.or(U32.is_eq((a + 1 : U32), b),
            U32.is_eq(a, (b + 1 : U32))))

def neighbor(+n: U32, +x: U32, +y: U32, +u: U32, +v: U32) -> Bool:
  Bool.and(
    Bool.and(in_bounds(n, x, y), in_bounds(n, u, v)),
    Bool.and(
      Bool.and(close(x, u), close(y, v)),
      Bool.not(Bool.and(U32.is_eq(x, u), U32.is_eq(y, v)))))

def main() -> U32:
  index(10, 5, 5)
