#!/usr/bin/env python3
"""Regression audit for the published Chapter 7/8 Bend examples.

Static checks only: run the real Bend examples separately. These tests ensure
that the reader-facing examples and the existing runtime gate do not drift.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'


class ByteClockSourceContract(unittest.TestCase):
    def test_binary_values_and_read_limit(self):
        code = (SRC / '45_binary_file.bend').read_text(encoding='utf-8')
        self.assertRegex(code, r'File\.write_bytes\(file,\s*\[0,\s*10,\s*13,\s*255\]\)')
        self.assertRegex(code, r'File\.read_bytes\(input,\s*16\)')
        self.assertIn('List.length', code)

    def test_file_handles_closed_on_both_results(self):
        code = (SRC / '45_binary_file.bend').read_text(encoding='utf-8')
        for name in ('after_write', 'after_read'):
            section = code.split('def ' + name + '(', 1)[1].split('\ndef ', 1)[0]
            self.assertIn('case Done{', section)
            self.assertIn('case Fail{', section)
            self.assertEqual(section.count('File.close(file)'), 2)

    def test_clock_is_io_plus_pure_difference(self):
        code = (SRC / '46_elapsed_clock.bend').read_text(encoding='utf-8')
        self.assertEqual(code.count('IO.now()'), 2)
        self.assertIn('IO.sleep(20)', code)
        self.assertIn('Nat.sub(last, first)', code)

    def test_runtime_gate_checks_bytes_and_variable_time(self):
        code = (ROOT / 'scripts' / 'test_examples.py').read_text(encoding='utf-8')
        self.assertIn('raw != bytes((0, 10, 13, 255))', code)
        self.assertIn('sample_bytes.bin', code)
        self.assertIn('45_binary_file.bend', code)
        self.assertIn('46_elapsed_clock.bend', code)
        self.assertRegex(code, r'clock\.isdecimal\(\)')


if __name__ == '__main__':
    unittest.main()
