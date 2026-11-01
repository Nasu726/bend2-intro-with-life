import Base
import ./module_math.bend as Math

def main() -> U32:
  Math.square(Math.cell_index(1, 2))
