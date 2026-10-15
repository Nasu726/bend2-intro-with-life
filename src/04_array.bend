import Base

def main() -> U32:
  a = [0 : U32*8n]
  a = Array.set(U32, a, 5, 42)
  (a, value) = Array.get(U32, a, 5)
  value
