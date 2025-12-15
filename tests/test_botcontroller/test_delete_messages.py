from telethon.tl.functions.messages import DeleteHistoryRequest


async def test_default_args(mock_controller):
    await mock_controller.delete_messages()

    expected = DeleteHistoryRequest(
        peer=mock_controller._target_peer,
        just_clear=False,
        revoke=True,
        max_id=0,
        min_date=None,
        max_date=None,
    )

    actual = mock_controller.client.await_args[0][0]
    mock_controller.client.assert_awaited_once()
    assert actual == expected


async def test_with_changed_kwargs(mock_controller):
    await mock_controller.delete_messages(just_clear=True, revoke=False)

    expected = DeleteHistoryRequest(
        peer=mock_controller._target_peer,
        just_clear=True,
        revoke=False,
        max_id=0,
        min_date=None,
        max_date=None,
    )

    actual = mock_controller.client.await_args[0][0]
    mock_controller.client.assert_awaited_once()
    assert actual == expected
