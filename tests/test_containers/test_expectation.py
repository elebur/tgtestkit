from unittest.mock import Mock, patch

import pytest
from pyrogram.types import Message

from tgtestkit.expectation import Expectation
from tgtestkit.timeout_settings import TimeoutSettings


@pytest.mark.parametrize(
    "min_n,max_n,num_msgs,is_sufficient,is_match",
    [
        # TODO: (0,0,0) ?
        (1, 1, 0, False, False),
        (1, 1, 1, True, True),
        (1, 1, 2, True, False),
    ],
)
def test_expectation(
    min_n: int,
    max_n: int,
    num_msgs: int,
    is_sufficient: bool,
    is_match: bool,
):
    obj = Expectation(min_updates=min_n, max_updates=max_n)
    msgs = [Mock(Message)] * num_msgs
    assert obj.is_sufficient(msgs) == is_sufficient
    assert obj._is_match(msgs) == is_match

@pytest.mark.parametrize(
    "min_m,max_m,num_msgs,assert_raise_log",
    [
        (2, 3, 2, False),
        (3, 3, 4, True),
        (2, 3, 1, True),
    ]
)
def test_verify(min_m, max_m, num_msgs, assert_raise_log):
    e = Expectation(min_updates=min_m, max_updates=max_m)
    messages = [Mock(Message)] * num_msgs

    with patch("tgtestkit.expectation._raise_or_log") as mock_raise_or_log:
        e.verify(messages, TimeoutSettings())

    if assert_raise_log:
        mock_raise_or_log.assert_called_once()
    else:
        mock_raise_or_log.assert_not_called()
