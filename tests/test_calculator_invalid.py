"""Tests for calculator security safeguards rejecting arbitrary Python code."""

import pytest
from app.tools.calculator import evaluate_expression


def test_reject_arbitrary_imports():
    """Verify rejection of __import__ or os modules."""
    with pytest.raises(ValueError):
        evaluate_expression("__import__('os').system('ls')")


def test_reject_eval_and_exec():
    """Verify rejection of eval or exec calls."""
    with pytest.raises(ValueError):
        evaluate_expression("eval('2 + 2')")

    with pytest.raises(ValueError):
        evaluate_expression("exec('x = 10')")


def test_reject_file_access():
    """Verify rejection of open() calls."""
    with pytest.raises(ValueError):
        evaluate_expression("open('/etc/passwd').read()")


def test_reject_variable_assignment_and_names():
    """Verify rejection of undefined variables or assignment expressions."""
    with pytest.raises(ValueError):
        evaluate_expression("x = 10")

    with pytest.raises(ValueError):
        evaluate_expression("x + 5")


def test_reject_attribute_access():
    """Verify rejection of attribute traversals (e.g. str.__class__)."""
    with pytest.raises(ValueError):
        evaluate_expression("(1).__class__.__bases__")


def test_reject_excessive_exponentiation():
    """Verify defense against algorithmic complexity / DoS via huge exponents."""
    with pytest.raises(ValueError, match="maximum security threshold"):
        evaluate_expression("2 ** 1000")


def test_reject_empty_and_whitespace():
    """Verify rejection of empty expressions."""
    with pytest.raises(ValueError):
        evaluate_expression("")

    with pytest.raises(ValueError):
        evaluate_expression("   ")
