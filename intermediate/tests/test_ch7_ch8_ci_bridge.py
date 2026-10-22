"""Include Chapter 7/8 source-contract checks in the regular CI unittest gate.

The authoritative tests live in scripts/ because they can also be run directly.
Unittest discovery only scans intermediate/tests, so load them here explicitly.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "test_ch7_ch8_source_contract.py"
_SPEC = spec_from_file_location("_ch7_ch8_source_contract_impl", _SOURCE)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Cannot load Chapter 7/8 source contract: {_SOURCE}")
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
ByteClockSourceContract = _MODULE.ByteClockSourceContract
