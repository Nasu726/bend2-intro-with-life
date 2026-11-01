# Join three PUBLIC clue masks with the bounded six-variable Bend solver.
# No true mine board or unverified player flags enter this module.
# The caller supplies exactly six distinct, sorted hidden cells and a sorted,
# unique, in-range list of revealed cells. Every clue must be revealed.
# use_total=True is sound only if these six cells are ALL remaining hidden cells.
import Base
import ./nxn_public_six_mask.bend as Six
import ./nxn_public_three_small.bend as Three
import ./nxn_public_subset.bend as Sets

# Consume each tagged mask once; an invalid mask must not become mask zero.
def with_third(+a: U32, +b: U32, third: Six.Mask,
               +ra: U32, +rb: U32, +rc: U32,
               +total: U32, +use_total: Bool) -> Three.Decision:
  match third:
    case Six.Invalid{}:
      Three.Inconsistent{}
    case Six.Valid{bits}:
      Three.infer(a, b, bits, ra, rb, rc, total, use_total)

def with_second(+a: U32, second: Six.Mask, third: Six.Mask,
                +ra: U32, +rb: U32, +rc: U32,
                +total: U32, +use_total: Bool) -> Three.Decision:
  match second:
    case Six.Invalid{}:
      Three.Inconsistent{}
    case Six.Valid{bits}:
      with_third(a, bits, third, ra, rb, rc, total, use_total)

def with_first(first: Six.Mask, second: Six.Mask, third: Six.Mask,
               +ra: U32, +rb: U32, +rc: U32,
               +total: U32, +use_total: Bool) -> Three.Decision:
  match first:
    case Six.Invalid{}:
      Three.Inconsistent{}
    case Six.Valid{bits}:
      with_second(bits, second, third, ra, rb, rc, total, use_total)

# A global mine count must never be imposed on a proper local subset.
# Distinguish this unsupported request from an apparent safe deduction.
def with_total_guard(ok: Bool, first: Six.Mask, second: Six.Mask,
                     third: Six.Mask, +r0: U32, +r1: U32, +r2: U32,
                     +total: U32, +use_total: Bool) -> Three.Decision:
  match ok:
    case False{}:
      Three.Inconsistent{}
    case True{}:
      with_first(first, second, third, r0, r1, r2, total, use_total)

# The three numbers are public residual mine counts. If there are separately
# certified mines, subtract them BEFORE constructing the hidden universe.
# No unsupported global mine count is inferred from a local six-cell frontier.
def from_public(+n: U32, +c0: U32, +c1: U32, +c2: U32,
                +r0: U32, +r1: U32, +r2: U32,
                +revealed: List<&2, U32>, +universe: List<&2, U32>,
                +total: U32, +use_total: Bool) -> Three.Decision:
  first = Six.mask_for(n, c0, revealed, universe)
  second = Six.mask_for(n, c1, revealed, universe)
  third = Six.mask_for(n, c2, revealed, universe)
  +total_ok = Bool.or(Bool.not(use_total),
                      U32.is_eq((n * n - Sets.size(revealed) : U32), 6))
  with_total_guard(total_ok, first, second, third,
                   r0, r1, r2, total, use_total)

# Public clues (0,2,7) all show 1 in a 3x3 board with two mines.
# Six remaining cells: (1,3,4,5,6,8). Models=2, safe=14, mines=1.
def main() -> U32:
  Three.score(from_public(3, 0, 2, 7, 1, 1, 1,
                         [0, 2, 7], [1, 3, 4, 5, 6, 8], 2, True{}))
