#!/usr/bin/env python3
"""Optionally compile and compare the Bend terminal program to the oracle.
Requires an independently installed `bend` CLI. Does not install software.
"""
from __future__ import annotations
import argparse
import difflib
import pathlib
import shutil
import subprocess
import sys
from reference import transcript

ROOT = pathlib.Path(__file__).resolve().parent.parent
BEND = ROOT / 'src' / '08_life_terminal.bend'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native', action='store_true', help='Compile to native binary before testing')
    args = parser.parse_args()
    if shutil.which('bend') is None:
        print('SKIP: Bend compiler not installed; Python reference test only.')
        return 2
    if args.native:
        exe = ROOT / 'build' / 'life-check'
        exe.parent.mkdir(parents=True, exist_ok=True)
        cmd = ['bend', str(BEND), '-o', str(exe)]
        print('BUILD:', ' '.join(cmd))
        subprocess.run(cmd, check=True)
        cmd = [str(exe), '--gpu', 'off']
    else:
        cmd = ['bend', str(BEND)]
    print('RUN:', ' '.join(cmd))
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        return proc.returncode
    actual = proc.stdout.replace('\r\n', '\n')
    # The checker may print status text before or after main's IO output.
    start = actual.find('generation 0\n')
    end = actual.find('done\n', start)
    if start < 0 or end < 0:
        print('Could not find expected generation frames in Bend output. Raw output:\n' + actual)
        return 1
    actual = actual[start:end + len('done\n')]
    expected = transcript()
    if actual == expected:
        print('PASS: all five Life frames equal the independent reference.')
        return 0
    print(''.join(difflib.unified_diff(expected.splitlines(True), actual.splitlines(True),
                                       fromfile='Python oracle', tofile='Bend')))
    return 1


if __name__ == '__main__':
    sys.exit(main())
