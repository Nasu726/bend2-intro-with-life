# Three PUBLIC clues in a 3 x 3 board: (0,0), (2,1), (6,1).
# Reuse the certified-safe results by hand; this is NOT an automatic
# fixed-point solver. Flags and the hidden mine layout are never inputs.
import Base
import ./nxn_public_local.bend as Rule

def first() -> U32:
  Rule.tag(Rule.infer(3, 0, 0, Nil{}, [0, 2, 6]))

def second() -> U32:
  Rule.tag(Rule.infer(3, 2, 1, Nil{}, [0, 1, 3, 4, 6]))

def third() -> U32:
  Rule.tag(Rule.infer(3, 6, 1, Nil{}, [0, 1, 3, 4, 6]))

def main() -> U32:
  (first() + second() + third() : U32)
