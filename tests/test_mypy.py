"""Tests for the plugin."""

from typing import  Annotated
import quantities as pq

import pytest

@pytest.mark.mypy_testing
def test_add() -> None:
    a: Annotated[int, pq.meter] = 3
    b: Annotated[int, pq.second] = 7
    c = a + b  # E: [assignment]
