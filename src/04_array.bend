import Base

def read_value(r: Array<U32> & U32) -> U32:
  (a, value) = r
  value

def main() -> U32:
  a = [0 : U32*8n]
  a = Array.set(U32, a, 5, 42)
  read_value(Array.get(U32, a, 5))
