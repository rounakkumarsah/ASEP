"""
ASEP — RestrictedPython Sandbox Configuration
=============================================
Defines safe builtins whitelist, disallowed primitives blacklist, and security
policies for untrusted LLM-generated code execution.
"""

from __future__ import annotations

import math
import operator
from typing import Any

from RestrictedPython import PrintCollector, safe_builtins
from RestrictedPython.Eval import (
    default_guarded_getitem,
    default_guarded_getiter,
)
from RestrictedPython.Guards import (
    full_write_guard,
    guarded_iter_unpack_sequence,
    safer_getattr,
)

# ---------------------------------------------------------------------------
# Whitelist of allowed built-in functions and identifiers
# ---------------------------------------------------------------------------
ALLOWED_BUILTINS: frozenset[str] = frozenset(
    [
        # Core collection and iteration helpers
        "print",
        "len",
        "range",
        "enumerate",
        "zip",
        "map",
        "filter",
        "sorted",
        "reversed",
        # Fundamental scalar & collection types
        "int",
        "float",
        "str",
        "bool",
        "list",
        "dict",
        "set",
        "tuple",
        "bytes",
        "frozenset",
        # Math & numerical functions
        "abs",
        "min",
        "max",
        "sum",
        "round",
        "divmod",
        "pow",
        # Logical checks & assertions
        "all",
        "any",
        "isinstance",
        "issubclass",
        "callable",
        "repr",
        "hash",
        # Standard exceptions permitted for error handling & tests
        "AssertionError",
        "Exception",
        "ValueError",
        "TypeError",
        "KeyError",
        "IndexError",
        "ZeroDivisionError",
        "AttributeError",
        "StopIteration",
        "RuntimeError",
        "ArithmeticError",
        "LookupError",
    ]
)

# ---------------------------------------------------------------------------
# Blacklist of prohibited primitives (denied by AST and runtime security)
# ---------------------------------------------------------------------------
DISALLOWED_BUILTINS: frozenset[str] = frozenset(
    [
        "open",
        "exec",
        "eval",
        "__import__",
        "input",
        "globals",
        "locals",
        "getattr",
        "setattr",
        "delattr",
        "compile",
        "breakpoint",
        "memoryview",
        "exit",
        "quit",
        "help",
        "super",
        "vars",
        "dir",
    ]
)

# Execution timeout threshold in seconds
DEFAULT_SANDBOX_TIMEOUT_SECONDS: float = 30.0

INPLACE_OPERATORS: dict[str, Any] = {
    "+=": operator.iadd,
    "-=": operator.isub,
    "*=": operator.imul,
    "/=": operator.itruediv,
    "//=": operator.ifloordiv,
    "%=": operator.imod,
    "**=": operator.ipow,
    "<<=": operator.ilshift,
    ">>=": operator.irshift,
    "&=": operator.iand,
    "^=": operator.ixor,
    "|=": operator.ior,
}


def default_inplacevar(op: str, x: Any, y: Any) -> Any:
    """Implements safe augmented in-place operations (+=, -=, *=, etc.)."""
    func = INPLACE_OPERATORS.get(op)
    if func is not None:
        return func(x, y)
    raise TypeError(f"Unsupported in-place operator: {op}")


def create_safe_builtins(output_buffer: list[str] | None = None) -> dict[str, Any]:
    """
    Constructs a hardened __builtins__ dictionary adhering to the whitelist.

    Args:
        output_buffer: Optional list to collect stdout from print() statements.

    Returns:
        Dictionary representing safe __builtins__.
    """
    builtins_dict: dict[str, Any] = {}

    # Copy safe base builtins from RestrictedPython that match whitelist
    for key, val in safe_builtins.items():
        if key in ALLOWED_BUILTINS and key not in DISALLOWED_BUILTINS:
            builtins_dict[key] = val

    # Expose math module utilities under safe builtins
    builtins_dict["math"] = math

    # Safe built-in types and functions
    safe_callables: dict[str, Any] = {
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sorted": sorted,
        "reversed": reversed,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "frozenset": frozenset,
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "round": round,
        "divmod": divmod,
        "pow": pow,
        "all": all,
        "any": any,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "callable": callable,
        "repr": repr,
        "AssertionError": AssertionError,
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "KeyError": KeyError,
        "IndexError": IndexError,
        "ZeroDivisionError": ZeroDivisionError,
        "RuntimeError": RuntimeError,
    }

    for name, func in safe_callables.items():
        if name in ALLOWED_BUILTINS and name not in DISALLOWED_BUILTINS:
            builtins_dict[name] = func

    # Safe print implementation
    def _safe_print(*args: Any, **kwargs: Any) -> None:
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        text = sep.join(str(arg) for arg in args) + end
        if output_buffer is not None:
            output_buffer.append(text)

    builtins_dict["print"] = _safe_print

    return builtins_dict


def get_default_guards() -> dict[str, Any]:
    """Returns the default AST and execution guard hooks required by RestrictedPython."""
    return {
        "_getattr_": safer_getattr,
        "_getitem_": default_guarded_getitem,
        "_getiter_": default_guarded_getiter,
        "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
        "_write_": full_write_guard,
        "_inplacevar_": default_inplacevar,
        "_print_": PrintCollector,
        "math": math,
    }
