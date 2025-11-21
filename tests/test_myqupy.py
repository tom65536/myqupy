


import pytest

@pytest.mark.mypy_xfail(
    'error', '[assignment]',
)
def test_foo():
    """doc"""
    x: int = "20"