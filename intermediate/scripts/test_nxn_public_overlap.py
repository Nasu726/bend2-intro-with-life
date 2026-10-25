#!/usr/bin/env python3
"""Independent exact assignment oracle for two arbitrary public clue sets.

Bend receives no hidden mine board. The reference enumerates all assignments
on A union B, then intersects the assignments' forced mine/safe conclusions.
"""
import itertools
import os
from pathlib import Path
import random
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / 'minesweeper'
FILES = ('nxn_public_subset.bend', 'nxn_public_overlap.bend')


def check_match_scrutinees_in(code):
    """Reject computed and local-binder matches before invoking Bend 2.0.39.

    A plain local name is NOT sufficient: the match scrutinee must be a
    parameter of the current definition. Multi-line signatures are supported.
    This is an early syntax guard, not a substitute for Bend --check-only.
    """
    import re
    parameters = set()
    signature = ''
    in_signature = False
    for lineno, line in enumerate(code.splitlines(), 1):
        statement = line.strip()
        if statement.startswith('def '):
            signature = statement
            in_signature = True
            parameters = set()
        elif in_signature:
            signature += ' ' + statement
        if in_signature and ') ->' in signature:
            args = signature.split('(', 1)[1].split(') ->', 1)[0]
            parameters = set(re.findall(r'\+?([a-z_]\w*)\s*:', args))
            in_signature = False
        if statement.startswith('match '):
            matched = re.fullmatch(r'match ([a-z_]\w*):', statement)
            if not matched or matched.group(1) not in parameters:
                raise AssertionError(
                    f'Invalid Bend match scrutinee on line {lineno}: {statement}'
                )


def check_match_scrutinees():
    code = (GAME / 'nxn_public_overlap.bend').read_text(encoding='utf-8')
    check_match_scrutinees_in(code)
    for invalid in (
        'def bad(x: Bool) -> U32:\\n  match Bool.not(x):\\n    case True{}:\\n      1',
        'def bad(x: Bool) -> U32:\\n  local = x\\n  match local:\\n    case True{}:\\n      1',
    ):
        try:
            check_match_scrutinees_in(invalid.replace('\\n', '\n'))
        except AssertionError:
            continue
        raise AssertionError('Scrutinee guard failed to reject invalid Bend')

def oracle(a, b, ra, rb):
    a, b = set(a), set(b)
    union = sorted(a | b)
    solutions = []
    for bits in itertools.product((0, 1), repeat=len(union)):
        mines = {index for index, bit in zip(union, bits) if bit}
        if len(mines & a) == ra and len(mines & b) == rb:
            solutions.append(mines)
    if not solutions:
        return 4, (), ()
    # The Bend kernel visits A, followed by the cells of B that are not in A.
    order = sorted(a) + sorted(b - a)
    safe = tuple(i for i in order if all(i not in s for s in solutions))
    mines = tuple(i for i in order if all(i in s for s in solutions))
    return 1, safe, mines


def cases():
    checks = [
        ((1, 2, 3), (2, 3, 4), 1, 2), # nonnested: safe 1, mine 4
        ((1, 2, 3), (2, 3, 4), 2, 1), # reverse
        ((1, 2, 3), (2, 3, 4), 1, 1), # unresolved
        ((1, 2), (2, 3), 0, 1),
        ((1, 2), (2, 3), 2, 1),
        ((1, 2), (2, 3), 0, 2), # impossible
        ((1, 2), (1, 2), 1, 1),
        ((1, 2), (1, 2), 1, 2), # inconsistent
        ((1, 2), (1, 2, 3), 1, 1),
        ((1, 2), (1, 2, 3), 1, 2),
        ((), (), 0, 0),
        ((), (1, 2), 0, 0),
        ((), (1, 2), 0, 2),
        ((1, 2), (), 2, 0),
        ((1,), (), 0, 1),
    ]
    rng = random.Random(20261025)
    for k in range(110):
        a = {i for i in range(1, 8) if rng.randrange(3) == 0}
        b = {i for i in range(1, 8) if rng.randrange(3) == 0}
        if k % 4 == 0:
            a &= b
        if k % 4 == 1:
            b &= a
        a, b = tuple(sorted(a)), tuple(sorted(b))
        checks.append((a, b, rng.randrange(len(a) + 2),
                       rng.randrange(len(b) + 2)))
    return checks


def literal(items):
    return '[' + ', '.join(map(str, items)) + ']' if items else 'Nil{}'


def source(checks):
    lines = [
        'import Base', 'import ./nxn_public_overlap.bend as Rule', '',
        'def same(a: List<U32>, b: List<U32>) -> Bool:',
        '  match a:',
        '    case Nil{}:',
        '      match b:',
        '        case Nil{}:', '          True{}',
        '        case y <> ys:', '          False{}',
        '    case x <> xs:',
        '      match b:',
        '        case Nil{}:', '          False{}',
        '        case y <> ys:',
        '          Bool.and(U32.is_eq(x, y), same(xs, ys))', '',
        'def one_if_true(b: Bool) -> U32:',
        '  match b:',
        '    case True{}:', '      1',
        '    case False{}:', '      0', '',
        'def compare(tag: U32, expected_safe: List<U32>, expected_mines: List<U32>, result: Rule.Decision) -> U32:',
        '  match result:',
        '    case Rule.Inconsistent{}:',
        '      one_if_true(U32.is_eq(tag, 4))',
        '    case Rule.Deduced{safe, mines}:',
        '      one_if_true(Bool.and(U32.is_eq(tag, 1),',
        '        Bool.and(same(expected_safe, safe), same(expected_mines, mines))))', '',
    ]
    for i, (a, b, ra, rb) in enumerate(checks):
        tag, safe, mines = oracle(a, b, ra, rb)
        lines += [
            f'def case_{i}() -> U32:',
            f'  compare({tag}, {literal(safe)}, {literal(mines)}, Rule.infer(',
            f'    {literal(a)}, {literal(b)}, {ra}, {rb}))', '',
        ]
    for start in range(0, len(checks), 8):
        lines += [
            f'def group_{start}() -> U32:',
            '  (' + ' + '.join(f'case_{i}()' for i in range(start, min(start+8, len(checks)))) + ' : U32)', '',
        ]
    lines += [
        'def main() -> U32:',
        '  (' + ' + '.join(f'group_{i}()' for i in range(0, len(checks), 8)) + ' : U32)', '',
    ]
    return '\n'.join(lines)


def main():
    check_match_scrutinees()
    checks = cases()
    assert len(checks) == 125
    assert {oracle(*case)[0] for case in checks} == {1, 4}
    assert oracle(*checks[0]) == (1, (1,), (4,))
    # Exhaustive four-cell oracle/bounds comparison, independent of Bend.
    from itertools import combinations
    universe = set(range(4))
    subsets = [set(c) for k in range(5) for c in combinations(universe, k)]
    verified = 0
    for a in subsets:
        for b in subsets:
            for ra in range(len(a) + 2):
                for rb in range(len(b) + 2):
                    common = len(a & b)
                    x, y = len(a - b), len(b - a)
                    lower = max(0, ra - x, rb - y)
                    upper = min(common, ra, rb)
                    expected = oracle(a, b, ra, rb)
                    if ra > len(a) or rb > len(b) or lower > upper:
                        assert expected[0] == 4
                    else:
                        order = sorted(a) + sorted(b - a)
                        safe = tuple(i for i in order if
                                     (i in a and i in b and upper == 0) or
                                     (i in a and i not in b and ra - lower == 0) or
                                     (i in b and i not in a and rb - lower == 0))
                        mines = tuple(i for i in order if
                                      (i in a and i in b and lower == common) or
                                      (i in a and i not in b and ra - upper == x) or
                                      (i in b and i not in a and rb - upper == y))
                        assert expected == (1, safe, mines)
                    verified += 1
    print(f"PASS {verified} exhaustive four-cell Python bounds checks", flush=True)
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        for name in FILES:
            (folder / name).write_bytes((GAME / name).read_bytes())
        program = folder / 'check_nxn_public_overlap.bend'
        program.write_text(source(checks), encoding='utf-8')
        for args in (('bend', str(program), '--check-only'), ('bend', str(program))):
            print(f'CHECK two arbitrary public constraints: {len(checks)} / {args[-1]}', flush=True)
            result = subprocess.run(args, cwd=folder, capture_output=True,
                                    text=True, timeout=360,
                                    env=dict(os.environ, BEND_NO_TELEMETRY='1'))
            if result.returncode:
                raise AssertionError(f'{args}: {result.stdout}\n{result.stderr}')
            if len(args) == 2 and result.stdout.strip().splitlines()[-1] != str(len(checks)):
                raise AssertionError(f'Expected {len(checks)}; got {result.stdout}')
    print(f'PASS {len(checks)} finite nonnested two-constraint deductions')


if __name__ == '__main__':
    main()
