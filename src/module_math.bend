import Base

# A helper module, imported by 19_module_main.bend.
def square(+x: U32) -> U32:
  (x * x : U32)

def cell_index(y: U32, x: U32) -> U32:
  (y * 8 + x : U32)
