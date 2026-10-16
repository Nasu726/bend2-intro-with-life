import Base

# Deliberately invalid: an Array has one owner and cannot be reused.
def main() -> U32:
  board = [0 : U32*8n]
  pair1 = Array.get(U32, board, 0)
  pair2 = Array.get(U32, board, 1)
  0
