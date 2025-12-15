import pytest


async def test_default_limit(controller):
    results = await controller.query_inline("search query", "gif")

    assert len(results) == 20


async def test_custom_limit(controller):
    results = await controller.query_inline("smile", "gif", limit = 2)

    assert len(results) == 2


@pytest.mark.parametrize("limit", [0, -1, -100])
async def test_negative_and_zero_limit(controller, limit):
    msg = "'limit' can not be less or equal to 0"
    with pytest.raises(ValueError, match=msg):
        await controller.query_inline("query", "gif", limit=limit)
